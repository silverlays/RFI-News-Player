# Changes compared to v1.1:
#
# - Fully optimized and reorganized code (last time?)
# - Added themes menu for easy switching
# - New save settings feature in the registry (only for themes actually)


import time
import PySimpleGUI as sg
from images import Images
from windowdata import WindowData
from scrapper import Scrapper
from mp3handler import MP3Handler
from settings import Settings


### USER SETTINGS
default_url = "https://www.rfi.fr/fr/journaux-monde/"
default_location = (1612, 0)
default_theme = "DarkGrey12"
### USER SETTINGS


version = "1.2"
program_title = f"RFI News Player v{version}"

window_data = WindowData()
window_data.url = default_url
window_data.location = default_location
window_data.theme = default_theme
window_data.playpause = Images.base64_play
switch_theme = False

settings = Settings()

class GUI():
  def __init__(self):
    global window_data
    if not switch_theme: window_data.scrapper = Scrapper(window_data.url)
    sg.SetGlobalIcon(Images.base64_app)
    sg.theme(window_data.theme)

    self.col1 = sg.Column([
      [sg.Button(key="playpause", border_width=0, image_data=window_data.playpause), sg.Button(key="stop", border_width=0, image_data=Images.base64_stop)],
      [sg.Slider(range=(0, 100), key="volumeslider", default_value=100, enable_events=True, size=(0, 10), orientation="horizontal", disable_number_display=True, expand_x=True, relief=sg.RELIEF_FLAT)]
    ], pad=(0, 0))

    self.col2 = sg.Column([
      [sg.ProgressBar(window_data.progressbar_values['max'], key="progressbar", size=(10, 0), border_width=1, relief=sg.RELIEF_RAISED, expand_x=True, expand_y=True)]
    ], vertical_alignment="center", expand_x=True, expand_y=True, pad=(0, 0))

    self.col3 = sg.Column([
      [sg.Text(window_data.mp3time_str, key="mp3time", font=("", 10))],
      [sg.Text(window_data.mp3volume_str, key="mp3volume", font=("", 10))]
    ], vertical_alignment="center", pad=(0, 0))

    self.menubar = [
      ["&Les journaux Monde", [ ["{} {}::_NEWS_".format(*window_data.scrapper.ExtractDataByItem(item)) for item in window_data.scrapper.Entries] ]],
      ["&Themes", self._GenerateThemesMenu()]
    ]

    self.layout = [
      [sg.MenubarCustom(self.menubar, key="menubar", bar_font=("", 10), bar_background_color=sg.theme_background_color(), bar_text_color=sg.theme_text_color())],
      [sg.HorizontalSeparator()],
      [sg.Text(window_data.title_str, key="title", font=("", 20, "bold"), justification="center", expand_x=True, pad=(0, 0))],
      [sg.Text(window_data.datetime_str, key="datetime", font=("", 14, "bold"), justification="center", expand_x=True, pad=(0, 0))],
      [sg.HorizontalSeparator()],
      [self.col1, self.col2, self.col3],
      [sg.HorizontalSeparator()],
      [sg.StatusBar(window_data.statusbar_str, key="statusbar", justification="center", relief=sg.RELIEF_RAISED, expand_x=True)]
    ]

    self.window = sg.Window(program_title, layout=self.layout, location=window_data.location, finalize=True)
    self._LoadNewMP3()
    window_data.location = self.window.CurrentLocation()

    while True:
      event, values = self.window.read(window_data.UPDATE_TICK)
      # print(event, values)
      if event == "__TIMEOUT__":
        if window_data.mp3time_values['elapsed'] > window_data.mp3time_values['length']: self.window['stop'].click()
        elif hasattr(window_data.mp3handler, "playing") and window_data.mp3handler.playing:
          window_data.mp3time_values['elapsed'] += (window_data.UPDATE_TICK / 1000)
          self._RefreshWindow(timer=True, progressbar=True)
      if event == sg.WIN_CLOSED:
        if hasattr(window_data.mp3handler, "playing"): window_data.mp3handler.Detroy()
        break
      if event == "playpause" and hasattr(window_data.mp3handler, "playing"):
        if window_data.mp3handler.playing: # DO PAUSE
          window_data.mp3handler.PauseResume()
          window_data.playpause = Images.base64_play
          window_data.statusbar_str = "Paused..."
          self._RefreshWindow(playpause=True, statusbar=True)
        elif not window_data.mp3handler.playing: # DO PLAY
          window_data.mp3handler.PauseResume() if not window_data.mp3handler.stopped else window_data.mp3handler.Play()
          window_data.playpause = Images.base64_pause
          window_data.statusbar_str = "Playing..."
          self._RefreshWindow(playpause=True, statusbar=True)
      if event == "stop" and hasattr(window_data.mp3handler, "playing"): # DO STOP
        window_data.mp3handler.Stop()
        window_data.mp3time_values['elapsed'] = 0.0
        window_data.playpause = Images.base64_play
        window_data.statusbar_str = "Stopped..."
        self._RefreshWindow(timer=True, progressbar=True, playpause=True, statusbar=True)
      if event == "volumeslider" and hasattr(window_data.mp3handler, "volume"): # CHANGE VOLUME
        window_data.mp3volume_str = "Volume: {:.0f}".format(values['volumeslider'])
        window_data.mp3handler.volume = values['volumeslider']
        self._RefreshWindow(volume=True)
      if values['menubar']:
        menubar_item = f"{values['menubar'].split('::')[0]}"
        if values['menubar'].find("_NEWS_") != -1:
          self._LoadNewMP3(window_data.scrapper.EntryNumberByTitle(menubar_item))
        if values['menubar'].find("_THEME_") != -1:
          self._SwitchTheme(menubar_item)
          return
  
  def _RefreshWindow(self, all=False, metadata=False, timer=False, volume=False, progressbar=False, playpause=False, statusbar=False):
    """Refresh one (or all) elements on the window

    Args:
        all (bool, optional): Force a full refresh. If True, the others parameters are useless. Defaults to False.
        metadata (bool, optional): Include Title and Datetime. Defaults to False.
        timer (bool, optional): Include MP3 timer. Defaults to False.
        volume (bool, optional): Include Volume. Defaults to False.
        progressbar (bool, optional): Include Progress bar. Defaults to False.
        playpause (bool, optional): Include Play/Pause button. Defaults to False.
        statusbar (bool, optional): Include Status bar. Defaults to False.
    """
    if metadata or all:
      self.window['title'].update(window_data.title_str)
      self.window['datetime'].update(window_data.datetime_str)
      self.window.refresh()
    if timer or all:
      window_data.mp3time_str = f"{time.strftime('%M:%S', time.gmtime(window_data.mp3time_values['elapsed']))} / {time.strftime('%M:%S', time.gmtime(window_data.mp3time_values['length']))}"
      self.window['mp3time'].update(window_data.mp3time_str)
    if volume or all: self.window['mp3volume'].update(window_data.mp3volume_str)
    if progressbar or all: self.window['progressbar'].update_bar(window_data.mp3time_values['elapsed'], window_data.mp3time_values['length'])
    if playpause or all: self.window['playpause'].update(image_data=window_data.playpause)
    if statusbar or all:
      self.window['statusbar'].update(window_data.statusbar_str)
      self.window.refresh()
  
  def _LoadNewMP3(self, entry_number=0):
    global window_data, switch_theme
    """Load a new MP3 into player.

    Args:
        entry_number (int, optional): Number obtained from Scrapper.EntryNumberByTitle() method. Defaults to 0 (most recent).
    """
    if not switch_theme:
      # Reset all values
      window_data.title_str = window_data.DEFAULT_TITLE_STR
      window_data.datetime_str = window_data.DEFAULT_DATETIME_STR
      window_data.mp3time_str = window_data.DEFAULT_MP3TIME_STR
      window_data.mp3volume_str = window_data.DEFAULT_MP3VOLUME_STR
      window_data.playpause = Images.base64_play
      window_data.mp3time_values['elapsed'] = 0.0
      window_data.mp3time_values['length'] = 0.0
      window_data.statusbar_str = "Loading new MP3..."
      self._RefreshWindow(all=True)

      # Updating values (1/2)
      window_data.statusbar_str = "Extracting data..."
      window_data.title_str, window_data.datetime_str = window_data.scrapper.ExtractDataByNumber(entry_number)
      self._RefreshWindow(statusbar=True, metadata=True)
      self.window.move(default_location[0] - self.window.size[0], default_location[1])

      # Download and updating values (2/2)
      window_data.statusbar_str = "Downloading..."
      window_data.mp3handler = MP3Handler(window_data.scrapper.ExtractUrl(entry_number))
      window_data.mp3handler.DownloadMP3()
      window_data.mp3time_values['length'] = window_data.mp3handler.mp3_length
      self._RefreshWindow(statusbar=True, timer=True)

      # Loading MP3
      window_data.statusbar_str = "Loading..."
      window_data.mp3handler.LoadMP3()
      window_data.mp3volume_str = "Volume: {:.0f}".format(window_data.mp3handler.volume)
      self._RefreshWindow(statusbar=True, volume=True)

      # Playing MP3
      window_data.statusbar_str = "Playing..."
      window_data.playpause = Images.base64_pause
      window_data.mp3handler.Play()
      self._RefreshWindow(statusbar=True, playpause=True)
    else:
      switch_theme = False
      self._RefreshWindow(all=True)

  def _SwitchTheme(self, new_theme):
    global window_data, switch_theme
    window_data.theme = new_theme
    switch_theme = True
    self.window.close()
  
  def _GenerateThemesMenu(self):
    themes_menu = []
    themes_count = len(sg.theme_list())
    i = 0
    while i < themes_count:
      menu_content = []
      for _ in range(0, 30):
        if i < themes_count:
          menu_content.append(sg.theme_list()[i-1] + "::_THEME_")
          i+=1
        else: break
      menu_title = f"{i-29}-{i}" if (i % 30) == 0 else f"{i-(i % 30)}-{i}"
      themes_menu.append(menu_title)
      themes_menu.append(menu_content)
    return themes_menu
  

if __name__ == "__main__":
  settings.LoadSettings(window_data)
  GUI()
  while switch_theme: GUI()
  settings.SaveSettings(window_data)