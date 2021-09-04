from scrapper import Scrapper
from mp3handler import MP3Handler

class WindowData():
  UPDATE_TICK = 100 # Seconds
  DEFAULT_TITLE_STR = "N/A"
  DEFAULT_DATETIME_STR = "N/A"

  def __init__(self):
    self.font = "Lucida"
    self.theme = ""
    self.url = ""
    self.location = (0, 0)
    self.scrapper = Scrapper
    self.mp3handler = MP3Handler
    self.playpause = bytes
    self.title_str = self.DEFAULT_TITLE_STR
    self.datetime_str = self.DEFAULT_DATETIME_STR
    self.progressbar_values = {'actual': 0, 'max': 0}
    self.statusbar_str = "{}".format(' ' * 40)

