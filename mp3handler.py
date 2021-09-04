import os
import urllib.request as request
from mutagen.mp3 import MP3
from audioplayer import AudioPlayer

class MP3Handler():
  def __init__(self, mp3_url, mp3_filename="rfitemp.mp3") -> None:
    self.mp3_url = mp3_url
    self.mp3_filename = mp3_filename
    self.mp3_player = None # Will be instanced after downloading
  
  def DownloadMP3(self) -> None:
    self.mp3_file = request.urlretrieve(url=self.mp3_url, filename=self.mp3_filename)[0]
    self.mp3_length = MP3(self.mp3_file).info.length
  
  def LoadMP3(self) -> None:
    self.mp3_player = AudioPlayer(self.mp3_file)
    self.playing = False
    self.stopped = True
  
  def Play(self) -> None:
    if self.mp3_player:
      self.mp3_player.play()
      self.playing = True
      self.stopped = False
  
  def PauseResume(self) -> None:
    if self.mp3_player:
      if not self.stopped and self.playing:
        self.mp3_player.pause()
        self.playing = False
      elif not self.stopped and not self.playing:
        self.mp3_player.resume()
        self.playing = True
  
  def Stop(self) -> None:
    if self.mp3_player:
      self.mp3_player.stop()
      self.playing = False
      self.stopped = True
  
  @property
  def volume(self):
    if self.mp3_player: return self.mp3_player.volume
    else: return 100
  
  @volume.setter
  def volume(self, new_value):
    if self.mp3_player:
      if new_value >= 0 and new_value <= 100:
        self.mp3_player.volume = new_value
      else: raise ValueError("The value must be between 0 and 100.")

  def Detroy(self) -> None:
    if self.mp3_player: self.mp3_player.close()
    if os.path.exists(self.mp3_filename): os.remove(self.mp3_filename)
