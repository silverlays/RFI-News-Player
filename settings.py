# Available variables:
#
# - (string/REG_SZ) Theme


import winreg
from windowdata import WindowData


class Settings():
  DEFAULT_PATH = "Software\\RFI News Player"

  def __init__(self):
    self._registry = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.DEFAULT_PATH)
    
  def LoadSettings(self, window_data: WindowData):
    _, values, _ = winreg.QueryInfoKey(self._registry)
    for value in range(values):
      value_name, value_data, _ = winreg.EnumValue(self._registry, value)
      
      # HANDELED VALUES
      if value_name == "Theme": window_data.theme = value_data

  def SaveSettings(self, window_data: WindowData):
    winreg.SetValueEx(self._registry, "Theme", 0, winreg.REG_SZ, window_data.theme)