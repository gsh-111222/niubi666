import sys
import socket
from typing import Optional

import numpy as np
from PIL import Image
from PyQt5.QtGui import QFont, QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QFrame,
    QLabel,
    QCheckBox,
    QMessageBox,
    QGroupBox,
)

from snake_backend import (
    SnakeUdpController,
    VideoStreamAssembler,
    slider_to_angle_display,
    DEFAULT_BIND_IP,
    DEFAULT_BIND_PORT,
)

# ---------- 界面主题（浅蓝灰 + 天青强调色） ----------
LINE_EDIT_STYLE = """
    QLineEdit {
        background-color: #FFFFFF;
        color: #1E293B;
        font-size: 14px;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 8px 12px;
        min-height: 20px;
    }
    QLineEdit:focus {
        border-color: #0284C7;
        outline: none;
    }
    QLineEdit::placeholder {
        color: #94A3B8;
    }
"""

LINE_EDIT_READONLY_STYLE = """
    QLineEdit {
        background-color: #F1F5F9;
        color: #334155;
        font-size: 14px;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 8px 12px;
    }
"""

BTN_PAD_LG = """
    QPushButton {
        font-size: 52px;
        font-weight: bold;
        color: #0369A1;
        background-color: #F0F9FF;
        border: 2px solid #7DD3FC;
        border-radius: 50px;
        padding: 4px;
    }
    QPushButton:hover {
        background-color: #E0F2FE;
        border-color: #0284C7;
        color: #0C4A6E;
    }
    QPushButton:pressed {
        background-color: #BAE6FD;
        border-color: #0369A1;
    }
"""

BTN_PAD_MD = """
    QPushButton {
        font-size: 34px;
        font-weight: bold;
        color: #0369A1;
        background-color: #F0F9FF;
        border: 2px solid #7DD3FC;
        border-radius: 50px;
        padding: 4px;
    }
    QPushButton:hover {
        background-color: #E0F2FE;
        border-color: #0284C7;
    }
    QPushButton:pressed {
        background-color: #BAE6FD;
    }
"""

BTN_TILE = """
    QPushButton {
        font-size: 17px;
        font-weight: bold;
        color: #FFFFFF;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #0EA5E9, stop:1 #0284C7);
        border: none;
        border-radius: 12px;
        padding: 8px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #38BDF8, stop:1 #0369A1);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #0284C7, stop:1 #075985);
    }
"""

BTN_SECONDARY = """
    QPushButton {
        font-size: 13px;
        font-weight: bold;
        color: #0369A1;
        background-color: #FFFFFF;
        border: 2px solid #7DD3FC;
        border-radius: 10px;
        padding: 10px 14px;
    }
    QPushButton:hover {
        background-color: #F0F9FF;
        border-color: #0284C7;
    }
    QPushButton:pressed {
        background-color: #E0F2FE;
    }
"""

BTN_PRIMARY = """
    QPushButton {
        font-size: 15px;
        font-weight: bold;
        color: #FFFFFF;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #06B6D4, stop:1 #0284C7);
        border: none;
        border-radius: 10px;
        padding: 12px 16px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #22D3EE, stop:1 #0369A1);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #0891B2, stop:1 #075985);
    }
"""

BTN_DANGER = """
    QPushButton {
        font-size: 15px;
        font-weight: bold;
        color: #FFFFFF;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #F87171, stop:1 #DC2626);
        border: none;
        border-radius: 10px;
        padding: 12px 16px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #FCA5A5, stop:1 #B91C1C);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #EF4444, stop:1 #991B1B);
    }
"""

SLIDER_H_STYLE = """
    QSlider { background: transparent; min-height: 36px; }
    QSlider::groove:horizontal {
        height: 8px;
        background: #E2E8F0;
        border-radius: 4px;
    }
    QSlider::sub-page:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #67E8F9, stop:1 #0284C7);
        border-radius: 4px;
    }
    QSlider::add-page:horizontal {
        background: #E2E8F0;
        border-radius: 4px;
    }
    QSlider::handle:horizontal {
        width: 20px;
        height: 20px;
        margin: -7px 0;
        background: #FFFFFF;
        border: 2px solid #0284C7;
        border-radius: 10px;
    }
    QSlider::handle:horizontal:hover {
        background: #F0F9FF;
        border-color: #0369A1;
    }
"""

SLIDER_V_STYLE = """
    QSlider { background: transparent; min-width: 36px; }
    QSlider::groove:vertical {
        width: 8px;
        background: #E2E8F0;
        border-radius: 4px;
    }
    QSlider::sub-page:vertical {
        background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
            stop:0 #67E8F9, stop:1 #0284C7);
        border-radius: 4px;
    }
    QSlider::add-page:vertical {
        background: #E2E8F0;
        border-radius: 4px;
    }
    QSlider::handle:vertical {
        width: 20px;
        height: 20px;
        margin: 0 -7px;
        background: #FFFFFF;
        border: 2px solid #0284C7;
        border-radius: 10px;
    }
"""

CHECKBOX_STYLE = """
    QCheckBox {
        color: #475569;
        font-size: 12px;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid #94A3B8;
        background: #FFFFFF;
    }
    QCheckBox::indicator:checked {
        background: #0284C7;
        border-color: #0284C7;
    }
    QCheckBox::indicator:hover {
        border-color: #0284C7;
    }
"""

GROUP_BOX_STYLE = """
    QGroupBox {
        font-size: 13px;
        font-weight: bold;
        color: #0F172A;
        border: 1px solid #D8E4F0;
        border-radius: 12px;
        margin-top: 14px;
        padding: 14px 12px 10px 12px;
        background-color: #FAFCFE;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 14px;
        padding: 0 8px;
        background-color: #FAFCFE;
    }
"""

CARD_FRAME = """
    QFrame#AppCard {
        background-color: #FFFFFF;
        border: 1px solid #D8E4F0;
        border-radius: 16px;
    }
"""

TELEMETRY_CARD = """
    QFrame#TelemetryCard {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
    }
    QFrame#TelemetryCard QLabel {
        color: #64748B;
        font-size: 12px;
    }
"""

VIDEO_OUTER = """
    QFrame#VideoOuter {
        background-color: #FFFFFF;
        border: 1px solid #D8E4F0;
        border-radius: 16px;
    }
"""

VIDEO_VIEWPORT = """
    QLabel#VideoViewport {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 12px;
        color: #94A3B8;
        font-size: 15px;
    }
"""

SIDE_PANEL = """
    QFrame#SidePanel {
        background-color: #FFFFFF;
        border: 1px solid #D8E4F0;
        border-radius: 16px;
    }
    QFrame#SidePanel QLabel {
        color: #64748B;
        font-size: 12px;
    }
"""

MAIN_WINDOW_STYLE = """
    QWidget#MainRoot {
        background-color: #E8EEF4;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #EEF2F7, stop:0.5 #E8EEF4, stop:1 #E2EBF5);
    }
"""


def _apply_card_style(frame: QFrame, name: str) -> None:
    frame.setObjectName(name)
    extra = {
        "AppCard": CARD_FRAME,
        "TelemetryCard": TELEMETRY_CARD,
        "VideoOuter": VIDEO_OUTER,
        "SidePanel": SIDE_PANEL,
    }.get(name, CARD_FRAME)
    frame.setStyleSheet(extra)


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


class VideoReceiveThread(QThread):
    """绑定本地 UDP 接收视频；解析逻辑在 backend，帧通过信号交给主线程显示。"""

    frame_ready = pyqtSignal(QImage)

    def __init__(
        self,
        bind_ip: str,
        bind_port: int,
        controller: SnakeUdpController,
        update_peer_on_recv: bool = True,
    ):
        super().__init__()
        self._bind_ip = bind_ip
        self._bind_port = bind_port
        self._controller = controller
        self._update_peer_on_recv = update_peer_on_recv
        self._run_flag = True
        self._assembler = VideoStreamAssembler()
        self.udp_socket: Optional[socket.socket] = None

    def request_stop(self) -> None:
        self._run_flag = False
        if self.udp_socket is not None:
            try:
                self.udp_socket.close()
            except OSError:
                pass

    def run(self) -> None:

        self._assembler.reset()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self._bind_ip, self._bind_port))
        except OSError as e:
            print("绑定失败:", e)
            return
        sock.settimeout(0.5)
        self.udp_socket = sock
        self._controller.bind_socket(sock)

        while self._run_flag:
            try:
                data, addr = sock.recvfrom(1_000_000)
            except socket.timeout:
                continue
            except OSError:
                break
            if self._update_peer_on_recv:
                self._controller.set_peer(addr)
            try:
                img = self._assembler.feed(data)
            except Exception as ret:
                print("VideoStreamAssembler error:", ret)
                continue
            if img is None:
                continue
            try:
                arr = np.ascontiguousarray(np.asarray(img.convert("RGB")))
                h, w, _ = arr.shape
                qimg = QImage(arr.data, w, h, 3 * w, QImage.Format_RGB888).copy()
                self.frame_ready.emit(qimg)
            except Exception as ret:
                print("图像转换错误:", ret)

        try:
            sock.close()
        except OSError:
            pass
        self.udp_socket = None
        self._controller.clear_socket()
        print("接收线程结束")


class VideoBoard(QWidget):
    def __init__(self) -> None:
        super().__init__()
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        outer = QFrame()
        _apply_card_style(outer, "VideoOuter")
        outer.setFixedSize(668, 518)
        v = QVBoxLayout(outer)
        v.setContentsMargins(18, 16, 18, 18)
        v.setSpacing(10)
        cap = QLabel("实时画面")
        cap.setStyleSheet(
            "color: #0F172A; font-size: 16px; font-weight: bold; letter-spacing: 1px;"
        )
        v.addWidget(cap)
        self.video_label = QLabel("等待数据中…")
        self.video_label.setObjectName("VideoViewport")
        self.video_label.setStyleSheet(VIDEO_VIEWPORT)
        self.video_label.setScaledContents(True)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(496, 330)                           #改
        v.addWidget(self.video_label, 0, Qt.AlignCenter)
        v.addStretch()
        main_layout.addWidget(outer)

    def set_frame(self, qimg: QImage) -> None:
        self.video_label.setPixmap(QPixmap.fromImage(qimg))


class ControlBoard(QWidget):
    def __init__(self, controller: SnakeUdpController) -> None:
        super().__init__()
        self._ctrl = controller
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(14)
        frame1 = QFrame()
        _apply_card_style(frame1, "AppCard")
        frame1.setMaximumSize(620, 520)
        v_pad = QVBoxLayout(frame1)
        v_pad.setContentsMargins(18, 16, 18, 18)
        v_pad.setSpacing(12)
        pad_title = QLabel("行驶控制")
        pad_title.setStyleSheet(
            "color: #0F172A; font-size: 16px; font-weight: bold; letter-spacing: 1px;"
        )
        v_pad.addWidget(pad_title)
        layout1 = QHBoxLayout()
        layout1.setSpacing(14)
        v_pad.addLayout(layout1)
        frame2 = QFrame()
        _apply_card_style(frame2, "TelemetryCard")
        frame2.setMaximumSize(300, 520)
        layout2 = QVBoxLayout(frame2)
        layout2.setContentsMargins(16, 16, 16, 16)
        layout2.setSpacing(8)
        hdr = QLabel("状态")
        hdr.setStyleSheet(
            "color: #0F172A; font-size: 15px; font-weight: bold; border: none;"
        )
        layout2.addWidget(hdr)

        col1 = QVBoxLayout()
        btn1 = QPushButton("◀")
        btn1.setFixedHeight(100)
        btn1.setFixedWidth(100)
        btn1.pressed.connect(self._ctrl.btn_left_press)
        btn1.released.connect(self._ctrl.motor_stop)
        btn1.setStyleSheet(BTN_PAD_LG)
        col1.addWidget(btn1)

        col2 = QVBoxLayout()
        btn2 = QPushButton("▲")
        btn2.setFixedWidth(100)
        btn2.setFixedHeight(100)
        btn2.pressed.connect(self._ctrl.btn_forward_press)
        btn2.released.connect(self._ctrl.motor_stop)
        btn2.setStyleSheet(BTN_PAD_MD)
        btn3 = QPushButton("▼")
        btn3.setFixedWidth(100)
        btn3.setFixedHeight(100)
        btn3.pressed.connect(self._ctrl.btn_back_press)
        btn3.released.connect(self._ctrl.motor_stop)
        btn3.setStyleSheet(BTN_PAD_MD)
        col2.addWidget(btn2)
        col2.addWidget(btn3)

        col3 = QVBoxLayout()
        btn4 = QPushButton("▶")
        btn4.setFixedWidth(100)
        btn4.setFixedHeight(100)
        btn4.pressed.connect(self._ctrl.btn_right_press)
        btn4.released.connect(self._ctrl.motor_stop)
        btn4.setStyleSheet(BTN_PAD_LG)
        col3.addWidget(btn4)

        col4 = QVBoxLayout()
        btn5 = QPushButton("重置")
        btn5.setFixedWidth(100)
        btn5.setFixedHeight(100)
        btn5.pressed.connect(self.restore_clicked)
        btn5.setStyleSheet(BTN_TILE)
        btn6 = QPushButton("左转")
        btn6.setFixedWidth(100)
        btn6.setFixedHeight(100)
        btn6.pressed.connect(self._ctrl.turn_left_fixed)
        btn6.released.connect(self._ctrl.motor2_stop)
        btn6.setStyleSheet(BTN_TILE)
        self.angle1_slider = QSlider(Qt.Horizontal)
        self.angle1_slider.setRange(20, 100)
        self.angle1_slider.setValue(self._ctrl.packet[6])
        self.angle1_slider.setTickPosition(QSlider.TicksBelow)
        self.angle1_slider.setTickInterval(10)
        self.angle1_slider.setFixedSize(100, 70)
        self.angle1_slider.sliderMoved.connect(self._on_angle1_preview)
        self.angle1_slider.sliderReleased.connect(self._on_angle1_commit)
        self.angle1_slider.setStyleSheet(SLIDER_H_STYLE)
        col4.addWidget(btn5)
        col4.addWidget(btn6)
        col4.addWidget(self.angle1_slider)

        col5 = QVBoxLayout()
        btn7 = QPushButton("模式")
        btn7.setFixedWidth(100)
        btn7.setFixedHeight(100)
        btn7.clicked.connect(self._on_mode_clicked)
        btn7.setStyleSheet(BTN_TILE)
        btn8 = QPushButton("右转")
        btn8.setFixedWidth(100)
        btn8.setFixedHeight(100)
        btn8.pressed.connect(self._ctrl.turn_right_fixed)
        btn8.released.connect(self._ctrl.motor2_stop)
        btn8.setStyleSheet(BTN_TILE)
        self.angle2_slider = QSlider(Qt.Horizontal)
        self.angle2_slider.setRange(20, 100)
        self.angle2_slider.setValue(self._ctrl.packet[7])
        self.angle2_slider.setTickPosition(QSlider.TicksBelow)
        self.angle2_slider.setTickInterval(10)
        self.angle2_slider.setFixedSize(100, 70)
        self.angle2_slider.sliderMoved.connect(self._on_angle2_preview)
        self.angle2_slider.sliderReleased.connect(self._on_angle2_commit)
        self.angle2_slider.setStyleSheet(SLIDER_H_STYLE)
        col5.addWidget(btn7)
        col5.addWidget(btn8)
        col5.addWidget(self.angle2_slider)

        col6 = QVBoxLayout()
        speed_lbl = QLabel("速度")
        speed_lbl.setStyleSheet("color: #64748B; font-size: 12px; font-weight: bold;")
        col6.addWidget(speed_lbl, 0, Qt.AlignHCenter)
        self.speed_slider = QSlider(Qt.Vertical)
        self.speed_slider.setRange(0, 99)
        self.speed_slider.setValue(self._ctrl.speed)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(10)
        self.speed_slider.setFixedSize(50, 300)
        self.speed_slider.valueChanged.connect(self._on_speed)
        self.speed_slider.setStyleSheet(SLIDER_V_STYLE)
        col6.addWidget(self.speed_slider)

        col7 = QFormLayout()
        col7.setHorizontalSpacing(12)
        col7.setVerticalSpacing(10)
        col7.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.angle1 = QLineEdit()
        self.angle1.setFixedWidth(200)
        self.angle1.setFixedHeight(44)
        self.angle1.setReadOnly(True)
        self.angle1.setStyleSheet(LINE_EDIT_READONLY_STYLE)
        self.angle1.setText(slider_to_angle_display(self._ctrl.packet[6]))
        self.angle2 = QLineEdit()
        self.angle2.setFixedWidth(200)
        self.angle2.setFixedHeight(44)
        self.angle2.setReadOnly(True)
        self.angle2.setStyleSheet(LINE_EDIT_READONLY_STYLE)
        self.angle2.setText(slider_to_angle_display(self._ctrl.packet[7]))
        self.Speed = QLineEdit(str(self._ctrl.speed))
        self.Speed.setFixedWidth(200)
        self.Speed.setFixedHeight(44)
        self.Speed.setStyleSheet(LINE_EDIT_READONLY_STYLE)
        self.Speed.setReadOnly(True)
        self.mode = QLineEdit()
        self.mode.setFixedWidth(200)
        self.mode.setFixedHeight(44)
        self.mode.setStyleSheet(LINE_EDIT_READONLY_STYLE)
        self.mode.setReadOnly(True)
        self.mode.setText("蛇形模式")
        col7.addRow("角度1", self.angle1)
        col7.addRow("角度2", self.angle2)
        col7.addRow("速度", self.Speed)
        col7.addRow("模式", self.mode)

        layout1.addLayout(col1)
        layout1.addLayout(col2)
        layout1.addLayout(col3)
        layout1.addLayout(col6)
        layout1.addLayout(col4)
        layout1.addLayout(col5)
        layout2.addLayout(col7)
        main_layout.addWidget(frame2)
        main_layout.addWidget(frame1)

    def _on_speed(self, value: int) -> None:
        self._ctrl.set_speed(value)
        self.Speed.setText(str(value))

    def _on_angle1_preview(self, value: int) -> None:
        if self._ctrl.mode == "car":
            return
        self.angle1.setText(slider_to_angle_display(value))

    def _on_angle1_commit(self) -> None:
        if self._ctrl.mode == "car":
            return
        value = self.angle1_slider.value()
        self._ctrl.set_angle1(value)
        self.angle1.setText(slider_to_angle_display(value))

    def _on_angle2_preview(self, value: int) -> None:
        if self._ctrl.mode == "car":
            return
        self.angle2.setText(slider_to_angle_display(value))

    def _on_angle2_commit(self) -> None:
        if self._ctrl.mode == "car":
            return
        value = self.angle2_slider.value()
        self._ctrl.set_angle2(value)
        self.angle2.setText(slider_to_angle_display(value))

    def _on_mode_clicked(self) -> None:
        name = self._ctrl.toggle_mode()
        self.mode.setText(name)
        for s in (self.angle1_slider, self.angle2_slider):
            s.blockSignals(True)
        self.angle1_slider.setValue(self._ctrl.packet[6])
        self.angle2_slider.setValue(self._ctrl.packet[7])
        self.angle1.setText(slider_to_angle_display(self._ctrl.packet[6]))
        self.angle2.setText(slider_to_angle_display(self._ctrl.packet[7]))
        for s in (self.angle1_slider, self.angle2_slider):
            s.blockSignals(False)

    def restore_clicked(self) -> None:
        self._ctrl.restore()
        for s in (self.angle1_slider, self.angle2_slider):
            s.blockSignals(True)
        self.angle1_slider.setValue(self._ctrl.packet[6])
        self.angle2_slider.setValue(self._ctrl.packet[7])
        self.angle1.setText(slider_to_angle_display(self._ctrl.packet[6]))
        self.angle2.setText(slider_to_angle_display(self._ctrl.packet[7]))
        for s in (self.angle1_slider, self.angle2_slider):
            s.blockSignals(False)

class MainWidget(QWidget):
    """主窗口：组合界面并管理接收线程生命周期。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("万向灵蛇")
        self.setGeometry(280, 100, 1580, 580)
        self.setWindowIcon(QIcon("app logo.png"))
        self.setObjectName("MainRoot")
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        self.controller = SnakeUdpController()
        self.udp_thread: Optional[VideoReceiveThread] = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(22, 22, 22, 22)
        main_layout.setSpacing(20)

        side = QFrame()
        _apply_card_style(side, "SidePanel")
        side.setMinimumWidth(296)
        side.setMaximumWidth(318)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(6, 8, 6, 12)
        side_layout.setSpacing(6)

        side_title = QLabel("连接与网络")
        side_title.setStyleSheet(
            "color: #0F172A; font-size: 15px; font-weight: bold; padding: 4px 6px 8px 6px;"
        )
        side_layout.addWidget(side_title)

        self.content1 = ControlBoard(self.controller)
        self.content2 = VideoBoard()

        self.bind_ip = DEFAULT_BIND_IP
        self.bind_port = DEFAULT_BIND_PORT

        g_listen = QGroupBox("本机监听")
        g_listen.setStyleSheet(GROUP_BOX_STYLE)
        form_listen = QFormLayout(g_listen)
        form_listen.setSpacing(10)
        form_listen.setContentsMargins(4, 12, 4, 8)
        self.edit_IP = QLineEdit(self.bind_ip)
        self.edit_port = QLineEdit(str(self.bind_port))
        self.edit_IP.setFixedWidth(212)
        self.edit_port.setFixedWidth(212)
        self.edit_IP.setStyleSheet(LINE_EDIT_STYLE)
        self.edit_port.setStyleSheet(LINE_EDIT_STYLE)
        form_listen.addRow("本机 IP", self.edit_IP)
        form_listen.addRow("端口", self.edit_port)
        self._refresh_local_ip_field()

        g_peer = QGroupBox("下位机地址")
        g_peer.setStyleSheet(GROUP_BOX_STYLE)
        form_peer = QFormLayout(g_peer)
        form_peer.setSpacing(10)
        form_peer.setContentsMargins(4, 12, 4, 8)
        self.edit_peer_ip = QLineEdit()
        self.edit_peer_ip.setPlaceholderText("例如 192.168.4.1")
        self.edit_peer_port = QLineEdit()
        self.edit_peer_port.setPlaceholderText("例如 8888")
        self.edit_peer_ip.setFixedWidth(212)
        self.edit_peer_port.setFixedWidth(212)
        self.edit_peer_ip.setStyleSheet(LINE_EDIT_STYLE)
        self.edit_peer_port.setStyleSheet(LINE_EDIT_STYLE)
        form_peer.addRow("设备 IP", self.edit_peer_ip)
        form_peer.addRow("设备端口", self.edit_peer_port)

        self.btn_apply_peer = QPushButton("应用对端")
        self.btn_apply_peer.setFixedHeight(40)
        self.btn_apply_peer.setStyleSheet(BTN_SECONDARY)
        self.btn_apply_peer.clicked.connect(self._on_apply_peer_clicked)
        form_peer.addRow("", self.btn_apply_peer)

        g_stream = QGroupBox("视频流")
        g_stream.setStyleSheet(GROUP_BOX_STYLE)
        stream_layout = QVBoxLayout(g_stream)
        stream_layout.setContentsMargins(4, 12, 4, 8)
        self.chk_auto_peer = QCheckBox("收包时自动更新对端")
        self.chk_auto_peer.setChecked(True)
        self.chk_auto_peer.setStyleSheet(CHECKBOX_STYLE)
        self.chk_auto_peer.setToolTip(
            "勾选：用发来视频/数据的源地址作为控制发送目标。"
            "不勾选：仅使用手动填写的对端（需先点「应用对端」）。"
        )
        stream_layout.addWidget(self.chk_auto_peer)

        self.btn9 = QPushButton("开启接收")
        self.btn9.setFixedHeight(44)
        self.btn9.clicked.connect(self._toggle_receiver)
        self.btn9.setStyleSheet(BTN_PRIMARY)
        stream_layout.addWidget(self.btn9)

        side_layout.addWidget(g_listen)
        side_layout.addWidget(g_peer)
        side_layout.addWidget(g_stream)
        side_layout.addStretch()

        main_layout.addWidget(self.content1)
        main_layout.addWidget(self.content2)
        main_layout.addWidget(side)

        self._sync_recv_button_look()

    def _sync_recv_button_look(self) -> None:
        if self.btn9.text() in ("关闭", "停止接收"):
            self.btn9.setStyleSheet(BTN_DANGER)
        else:
            self.btn9.setStyleSheet(BTN_PRIMARY)

    def _refresh_local_ip_field(self) -> str:
        """自动检测本机 IP 并同步到输入框。"""
        local_ip = detect_local_ipv4(self.bind_ip)
        self.bind_ip = local_ip
        self.edit_IP.setText(local_ip)
        return local_ip

    def _parse_peer_from_fields(self):
        """若 IP 与端口均有效则返回 (ip, port)，否则返回 None。"""
        ip = self.edit_peer_ip.text().strip()
        port_s = self.edit_peer_port.text().strip()
        if not ip or not port_s:
            return None
        try:
            port = int(port_s)
            if not (0 < port < 65536):
                return None
        except ValueError:
            return None
        return (ip, port)

    def _apply_peer_silent(self) -> bool:
        """从输入框写入 controller，仅在两项都填好时生效。"""
        parsed = self._parse_peer_from_fields()
        if parsed is None:
            return False
        self.controller.set_peer(parsed)
        return True

    def _on_apply_peer_clicked(self) -> None:
        parsed = self._parse_peer_from_fields()
        if parsed is None:
            QMessageBox.warning(
                self,
                "提示",
                "请填写有效的下位机 IP 和端口（端口为 1～65535 的整数）。",
            )
            return
        self.controller.set_peer(parsed)
        QMessageBox.information(self, "提示", "已设置对端：%s:%d" % parsed)

    def _stop_receiver(self) -> None:
        if self.udp_thread is not None:
            try:
                self.udp_thread.frame_ready.disconnect(self.content2.set_frame)
            except (TypeError, RuntimeError):
                pass
            self.udp_thread.request_stop()
            self.udp_thread.wait(5000)
            self.udp_thread = None
        self.controller.clear_socket()

    def _toggle_receiver(self) -> None:
        if self.btn9.text() == "开启接收":
            try:
                # 启动前再次检测，避免网卡切换后仍使用旧地址
                self.bind_ip = self._refresh_local_ip_field()
                self.bind_port = int(self.edit_port.text().strip())
            except ValueError:
                return
            self.udp_thread = VideoReceiveThread(
                self.bind_ip,
                self.bind_port,
                self.controller,
                update_peer_on_recv=self.chk_auto_peer.isChecked(),
            )
            self.udp_thread.frame_ready.connect(self.content2.set_frame)
            self.udp_thread.start()
            self._apply_peer_silent()
            self.btn9.setText("停止接收")
            self._sync_recv_button_look()
        else:
            self._stop_receiver()
            self.btn9.setText("开启接收")
            self._sync_recv_button_look()

    def closeEvent(self, event) -> None:
        self._stop_receiver()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    _font = QFont("Microsoft YaHei UI", 10)
    if not _font.exactMatch():
        _font = QFont("Microsoft YaHei", 10)
    app.setFont(_font)
    w = MainWidget()
    w.show()
    sys.exit(app.exec_())
