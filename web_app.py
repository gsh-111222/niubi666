import io
import socket
import threading
import time
from typing import Optional

from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS
from PIL import Image

from snake_backend import (
    DEFAULT_BIND_IP,
    DEFAULT_BIND_PORT,
    SnakeUdpController,
    VideoStreamAssembler,
    slider_to_angle_display,
)


class UdpVideoService:
    def __init__(self, controller: SnakeUdpController) -> None:
        self.controller = controller
        self.bind_ip = DEFAULT_BIND_IP
        self.bind_port = DEFAULT_BIND_PORT
        self.update_peer_on_recv = True

        self._assembler = VideoStreamAssembler()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._sock: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self._latest_jpeg: Optional[bytes] = None

    @property
    def running(self) -> bool:
        return self._running

    def start(self, bind_ip: str, bind_port: int, update_peer_on_recv: bool) -> bool:
        if self._running:
            return True

        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.update_peer_on_recv = update_peer_on_recv
        self._assembler.reset()
        self._latest_jpeg = None

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((bind_ip, bind_port))
        except OSError:
            sock.close()
            return False

        sock.settimeout(0.5)
        self._sock = sock
        self.controller.bind_socket(sock)
        self._running = True
        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._running = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._thread = None
        self._sock = None
        self.controller.clear_socket()

    def _recv_loop(self) -> None:
        sock = self._sock
        if sock is None:
            return
        while self._running:
            try:
                data, addr = sock.recvfrom(1_000_000)
            except socket.timeout:
                continue
            except OSError:
                break
            if self.update_peer_on_recv:
                self.controller.set_peer(addr)
            try:
                img = self._assembler.feed(data)
            except Exception:
                continue
            if img is None:
                continue
            try:
                rgb = img.convert("RGB")
                buf = io.BytesIO()
                rgb.save(buf, format="JPEG", quality=80)
                with self._lock:
                    self._latest_jpeg = buf.getvalue()
            except Exception:
                continue

    def latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/video_feed": {"origins": "*"}})
controller = SnakeUdpController()
video_service = UdpVideoService(controller)


def detect_local_ipv4(fallback: str = DEFAULT_BIND_IP) -> str:
    """尽量获取可用于局域网通信的本机 IPv4。"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # 不实际发送数据，只借系统路由挑选当前出口网卡地址
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            if ip and ip != "0.0.0.0":
                return ip
    except OSError:
        pass
    try:
        host_ip = socket.gethostbyname(socket.gethostname())
        if host_ip and host_ip != "0.0.0.0":
            return host_ip
    except OSError:
        pass
    return fallback


video_service.bind_ip = detect_local_ipv4(video_service.bind_ip)


def state_payload() -> dict:
    # 未运行时持续刷新本机 IP，网页输入框会随 /api/state 自动同步显示
    if not video_service.running:
        video_service.bind_ip = detect_local_ipv4(video_service.bind_ip)
    mode_name = "小车模式" if controller.mode == "car" else "蛇形模式"
    return {
        "speed": controller.speed,
        "mode": mode_name,
        "angle1": controller.packet[6],
        "angle2": controller.packet[7],
        "angle1_display": slider_to_angle_display(controller.packet[6]),
        "angle2_display": slider_to_angle_display(controller.packet[7]),
        "receiver_running": video_service.running,
        "bind_ip": video_service.bind_ip,
        "bind_port": video_service.bind_port,
        "peer": controller.peer_address,
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def api_state():
    return jsonify(state_payload())


@app.post("/api/peer")
def api_peer():
    data = request.get_json(silent=True) or {}
    ip = str(data.get("ip", "")).strip()
    port = data.get("port")
    try:
        port = int(port)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "端口必须是整数"}), 400
    if not ip or not (1 <= port <= 65535):
        return jsonify({"ok": False, "error": "请输入有效 IP 和端口"}), 400
    controller.set_peer((ip, port))
    return jsonify({"ok": True, "state": state_payload()})


@app.post("/api/receiver")
def api_receiver():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action == "start":
        # 开启接收时自动检测一次，避免网卡变化后仍使用旧地址
        bind_ip = detect_local_ipv4(video_service.bind_ip)
        bind_port = data.get("bind_port", DEFAULT_BIND_PORT)
        auto_peer = bool(data.get("auto_peer", True))
        try:
            bind_port = int(bind_port)
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "监听端口无效"}), 400
        ok = video_service.start(bind_ip, bind_port, auto_peer)
        if not ok:
            return jsonify({"ok": False, "error": "UDP 绑定失败，请检查 IP/端口"}), 400
        return jsonify({"ok": True, "state": state_payload()})
    if action == "stop":
        video_service.stop()
        return jsonify({"ok": True, "state": state_payload()})
    return jsonify({"ok": False, "error": "未知操作"}), 400


@app.get("/video_feed")
def video_feed():
    def gen():
        while True:
            frame = video_service.latest_jpeg()
            if frame is None:
                time.sleep(0.05)
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
            time.sleep(0.03)

    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.post("/api/action")
def api_action():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    actions = {
        "left_press": controller.btn_left_press,
        "right_press": controller.btn_right_press,
        "forward_press": controller.btn_forward_press,
        "back_press": controller.btn_back_press,
        "stop": controller.motor_stop,
        "turn_left": controller.turn_left_fixed,
        "turn_right": controller.turn_right_fixed,
        "restore": controller.restore,
    }
    fn = actions.get(action)
    if fn is None:
        return jsonify({"ok": False, "error": "未知动作"}), 400
    fn()
    return jsonify({"ok": True, "state": state_payload()})


@app.post("/api/mode")
def api_mode():
    controller.toggle_mode()
    return jsonify({"ok": True, "state": state_payload()})


@app.post("/api/speed")
def api_speed():
    data = request.get_json(silent=True) or {}
    value = data.get("value")
    try:
        value = int(value)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "速度必须是整数"}), 400
    controller.set_speed(value)
    return jsonify({"ok": True, "state": state_payload()})


@app.post("/api/angle")
def api_angle():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    value = data.get("value")
    try:
        value = int(value)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "角度值必须是整数"}), 400
    if name == "angle1":
        controller.set_angle1(value)
    elif name == "angle2":
        controller.set_angle2(value)
    else:
        return jsonify({"ok": False, "error": "未知角度名称"}), 400
    return jsonify({"ok": True, "state": state_payload()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
