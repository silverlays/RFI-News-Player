import os
from ctypes import c_buffer, windll
import urllib.request as request


class MP3Handler():
  STATUS_STOPPED = "stopped"
  STATUS_PLAYING = "playing"
  STATUS_PAUSED = "paused"

  def __init__(self, mp3_url: str, mp3_filename="rfitemp.mp3") -> None:
    self.mp3_url = mp3_url
    self.mp3_filename = mp3_filename
    self._alias = "A{}".format(id(self))

  def DownloadMP3(self) -> None:
    self.mp3_file = request.urlretrieve(url=self.mp3_url, filename=self.mp3_filename)[0]

  def LoadMP3(self) -> None:
    self._MciSendString(r'open "{}" type mpegvideo alias {}'.format(self.mp3_filename, self._alias))
    self._MciSendString(f"set {self._alias} time format milliseconds")

  def Play(self) -> None:
    self._MciSendString(f"play {self._alias}")

  def Pause(self) -> None:
    self._MciSendString(f"pause {self._alias}")

  def Resume(self) -> None:
    self._MciSendString(f"resume {self._alias}")

  def Stop(self) -> None:
    self._MciSendString(f"stop {self._alias}")
    self._MciSendString(f"seek {self._alias} to start")

  def Detroy(self) -> None:
    self._MciSendString(f"close {self._alias}")
    if os.path.exists(self.mp3_filename): os.remove(self.mp3_filename)
  
  def _MciSendString(self, command, buffer=False):
    if buffer:
      buffer = c_buffer(255)
      ret = windll.winmm.mciSendStringW(command, buffer, 254, 0)
      if ret != 0: raise MP3HandlerError(ret)
      return buffer.raw
    if not buffer:
      ret = windll.winmm.mciSendStringW(command, 0, 0, 0)
      if ret != 0: raise MP3HandlerError(ret)

  @property
  def length(self):
    try:
      length = self._MciSendString(f"status {self._alias} length", True)
      length = int(length.replace(b'\x00', b'')) / 1000
    except: length = 0.0
    return length

  @property
  def position(self):
    try:
      position = self._MciSendString(f"status {self._alias} position", True)
      position = int(position.replace(b'\x00', b'')) / 1000
    except: position = 0.0
    return position  

  @position.setter
  def position(self, new_value: float):
    if new_value < 0: new_value = 0
    if new_value > self.length: new_value = self.length
    self._MciSendString(f"play {self._alias} from {int(new_value * 1000)}")

  @property
  def status(self):
    try:
      status = self._MciSendString(f"status {self._alias} mode", True)
      status = str(status.replace(b'\x00', b'')).removeprefix("b'").removesuffix("'")
    except: status = "stopped"
    return status

  @property
  def volume(self):
    try:
      volume = self._MciSendString(f"status {self._alias} volume", True)
      volume = int(volume.replace(b'\x00', b'')) / 10
    except: volume = 100.0
    return int(volume)

  @volume.setter
  def volume(self, new_value: float):
    self._MciSendString(f"setaudio {self._alias} volume to {int(new_value)*10}")


class MP3HandlerError(Exception):
  def __init__(self, error_code: int) -> None:
    error_str = c_buffer(255)
    windll.winmm.mciGetErrorStringA(error_code, error_str, 254)
    error_str = str(error_str.value, encoding="windows_1252")
    super().__init__(error_str)
