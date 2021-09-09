# Available variables:
#
# - (string/REG_SZ) Theme


import os, json


__settings_file__ = "settings.json"


class Settings():
  def __init__(self) -> None:
    self._json_settings = {
      "default_url": "https://www.rfi.fr/fr/journaux-monde/",
      "default_location": (1612, 0),
      "theme": "DarkGrey12",
    }

    if os.path.exists(__settings_file__):
      with open(__settings_file__, "r") as file: self._json_settings = json.load(fp=file)
    else: self.SaveSettings()

  def SaveSettings(self):
    with open(__settings_file__, "w") as file: json.dump(obj=self._json_settings, fp=file, indent=2)
  
  def Get(self, key: str):
    for ckey in self._json_settings.keys():
      if ckey == key: return self._json_settings[ckey]
  
  def Set(self, key: str, value: object):
    self._json_settings[key] = value