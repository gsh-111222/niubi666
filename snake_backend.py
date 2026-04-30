"""
UDP 控制与视频流协议：无 Qt 依赖，供界面层调用。
"""
from __future__ import annotations

import io
import socket
from typing import List, Optional, Tuple

from PIL import Image

# 默认控制包：与下位机协议一致
DEFAULT_PACKET: List[int] = [0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3C, 0x3C, 0xFE]

# 下位机地址在首次收到 UDP 数据时由 set_peer 自动记录，无需预设 IP/端口
DEFAULT_BIND_IP = "192.168.127.10"
DEFAULT_BIND_PORT = 9090


def slider_to_angle_display(value: int) -> str:
    """滑块值 -> 界面显示角度字符串。"""
    return str((value - 20) * 2.25)


class SnakeUdpController:
    """维护控制包、速度与对端地址，负责 sendto。"""

    def __init__(self) -> None:
        self.packet = DEFAULT_PACKET
        self.speed = 50
        self.peer_address: Optional[Tuple[str, int]] = None
        self._sock: Optional[socket.socket] = None
        self.mode = "snake"

    def bind_socket(self, sock: socket.socket) -> None:
        self._sock = sock

    def clear_socket(self) -> None:
        self._sock = None

    def set_peer(self, addr: Tuple[str, int]) -> None:
        self.peer_address = addr

    def send(self) -> bool:
        if self._sock is None or self.peer_address is None:
            return False
        try:
            self._sock.sendto(bytes(self.packet), self.peer_address)
            print(self.packet)
            return True
        except OSError:
            return False

    def _speed_byte(self) -> int:
        return self.speed & 0x7F

    def motor_stop(self) -> None:
        self.packet[2] = 0x00
        self.packet[3] = 0x00
        self.packet[4] = 0x00
        self.packet[5] = 0x00
        try:
            self.send()
        except:
            pass

    def motor2_stop(self) -> None:
        if self.mode == "snake":
            pass
        else:
            self.packet[2] = 0x00
            self.packet[3] = 0x00
            self.packet[4] = 0x00
            self.packet[5] = 0x00
            try:
                self.send()
            except:
                pass


    def btn_left_press(self) -> None:
        s = self._speed_byte()
        if self.mode == "car":
            self.packet[2] = (self.packet[2] & 0x7F) | s
            self.packet[3] = (self.packet[3] & 0x7F) | s
            self.packet[4] = (self.packet[4] | 0x80) | s
            self.packet[5] = (self.packet[5] | 0x80) | s
        else:
            self.packet[2] = (self.packet[2] & 0x7F) | s
            self.packet[3] = (self.packet[3] | 0x80) | s
            self.packet[4] = (self.packet[4] & 0x7F) | s
            self.packet[5] = (self.packet[5] | 0x80) | s
        try:
            self.send()
        except:
            pass


    def btn_forward_press(self) -> None:
        s = self._speed_byte()
        if self.mode == "car":
            self.packet[2] = (self.packet[2] & 0x7F) | s
            self.packet[3] = (self.packet[3] | 0x80) | s
            self.packet[4] = (self.packet[4] | 0x80) | s
            self.packet[5] = (self.packet[5] & 0x7F) | s
        else:
            self.packet[2] = (self.packet[2] | 0x80) | s
            self.packet[3] = (self.packet[3] | 0x80) | s
            self.packet[4] = (self.packet[4] | 0x80) | s
            self.packet[5] = (self.packet[5] | 0x80) | s
        try:
            self.send()
        except:
            pass

    def btn_back_press(self) -> None:
        s = self._speed_byte()
        if self.mode == "car":
            self.packet[2] = (self.packet[2] | 0x80) | s
            self.packet[3] = (self.packet[3] & 0x7F) | s
            self.packet[4] = (self.packet[4] & 0x7F) | s
            self.packet[5] = (self.packet[5] | 0x80) | s
        else:
            self.packet[2] = (self.packet[2] & 0x7F) | s
            self.packet[3] = (self.packet[3] & 0x7F) | s
            self.packet[4] = (self.packet[4] & 0x7F) | s
            self.packet[5] = (self.packet[5] & 0x7F) | s
        try:
            self.send()
        except:
            pass

    def btn_right_press(self) -> None:
        s = self._speed_byte()
        if self.mode == "car":
            self.packet[2] = (self.packet[2] | 0x80) | s
            self.packet[3] = (self.packet[3] | 0x80) | s
            self.packet[4] = (self.packet[4] & 0x7F) | s
            self.packet[5] = (self.packet[5] & 0x7F) | s
        else:
            self.packet[2] = (self.packet[2] | 0x80) | s
            self.packet[3] = (self.packet[3] & 0x7F) | s
            self.packet[4] = (self.packet[4] | 0x80) | s
            self.packet[5] = (self.packet[5] & 0x7F) | s
        try:
            self.send()
        except:
            pass

    def turn_left_fixed(self):
        if self.mode != "car":
            self.packet[1] = self.packet[1] | 0x02
            try:
                self.send()
            except:
                pass
            self.packet[1] = self.packet[1] & 0xFD
        else:
            s = self._speed_byte()
            self.packet[2] = (self.packet[2] & 0x7F) | s
            self.packet[3] = (self.packet[3] & 0x7F) | s
            self.packet[4] = (self.packet[4] & 0x7F) | s
            self.packet[5] = (self.packet[5] & 0x7F) | s
            try:
                self.send()
            except:
                pass

    def turn_right_fixed(self):
        if self.mode != "car":
            self.packet[1] = self.packet[1] | 0x01
            try:
                self.send()
            except:
                pass
            self.packet[1] = self.packet[1] & 0xFE
        else:
            s = self._speed_byte()
            self.packet[2] = (self.packet[2] | 0x80) | s
            self.packet[3] = (self.packet[3] | 0x80) | s
            self.packet[4] = (self.packet[4] | 0x80) | s
            self.packet[5] = (self.packet[5] | 0x80) | s
            try:
                self.send()
            except:
                pass

    def restore(self) -> None:
        if self.mode == "car":
            return
        else:
            self.packet[6]=60
            self.packet[7]=60
        try:
            self.send()
        except:
            pass

    def toggle_mode(self) -> str:
        """切换蛇形/小车模式，返回界面应显示的模式名称。"""
        if self.mode == "car":
            self.packet[6] = 60
            self.packet[7] = 60
            self.mode = "snake"
            name = "蛇形模式"
        else:
            self.packet[6] = 100
            self.packet[7] = 20
            self.mode = "car"
            name = "小车模式"
        try:
            self.send()
        except:
            pass
        return name

    def set_speed(self, value: int) -> None:
        self.speed = max(0, min(99, int(value)))

    def set_angle1(self, value: int) -> None:
        if self.mode == "car":
            return
        self.packet[6] = value
        try:
            self.send()
        except:
            pass

    def set_angle2(self, value: int) -> None:
        if self.mode == "car":
            return
        self.packet[7] = value
        try:
            self.send()
        except:
            pass


class VideoStreamAssembler:
    """ESP32Cam 分片协议：从 UDP 数据报还原 JPEG/图像字节。"""

    def __init__(self) -> None:
        self.flage = 1
        self.buff = b""
        self.pic_len = 0
        self.pic_num = 0

    def reset(self) -> None:
        self.flage = 1
        self.buff = b""
        self.pic_len = 0
        self.pic_num = 0

    def feed(self, data: bytes) -> Optional[Image.Image]:
        """
        处理一帧 UDP 负载。若为完整图像则返回 PIL Image，否则返回 None。
        """
        try:
            if self.flage == 1:
                text = data.decode("utf-8").strip()
                if text == "ok":
                    self.flage = 2
                return None
            if self.flage == 2:
                text = data.decode("utf-8").strip()
                self.pic_len = int(text)
                self.pic_num = int(self.pic_len / 1024) + 1
                self.flage = 3
                return None
            self.buff += data
            self.pic_num -= 1
            if self.pic_num == 0:
                try:
                    stream = io.BytesIO(self.buff)
                    image = Image.open(stream)
                    image.load()
                    out = image.copy()
                except Exception:
                    out = None
                self.flage = 1
                self.pic_len = 0
                self.pic_num = 0
                self.buff = b""
                return out
        except Exception:
            pass
        return None
