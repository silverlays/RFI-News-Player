import os, json


__settings_file__ = "settings.json"

json_settings = {
  "url": "https://www.rfi.fr/fr/journaux-monde/",
  "location": (1612, 0),
  "theme": "DarkGrey12",
}


def load_settings():
  global json_settings
  if os.path.exists(__settings_file__):
    with open(__settings_file__, "r") as file: json_settings = json.load(fp=file)
  else: save_settings()


def save_settings():
  with open(__settings_file__, "w") as file: json.dump(obj=json_settings, fp=file, indent=2)


def set_setting(key: str, value: str):
  global json_settings
  json_settings[key] = value