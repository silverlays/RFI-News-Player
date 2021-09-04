# Changes compared to v1.3:
#
# - Added seeking.
# - Updated interface (to include seeking).
# - Changed my mind, replacing registry by json file to save settings (actual and future).
# - Added Left/Right arrow on keyboard to quick seek.


import time
import PySimpleGUI as sg
from images import Images
from windowdata import WindowData
from scrapper import Scrapper
from mp3handler import MP3Handler
from settings import Settings


version = "1.4"
program_title = f"RFI News Player v{version}"


settings = Settings()
window_data = WindowData()
window_data.url = settings.Get("default_url")
window_data.location = settings.Get("default_location")
window_data.theme = settings.Get("theme")
window_data.playpause = Images.base64_play
switch_theme = False


class GUI():
  def __init__(self):
    global window_data
    if not switch_theme: window_data.scrapper = Scrapper(window_data.url)
    sg.SetGlobalIcon(Images.base64_app)
    sg.theme(window_data.theme)

    self.col1 = sg.Column([
      [sg.Button(key="playpause", border_width=0, image_data=window_data.playpause), sg.Button(key="stop", border_width=0, image_data=Images.base64_stop)],
      [sg.Button(key="rewind", border_width=0, image_data=Images.base64_rewind), sg.Button(key="forward", border_width=0, image_data=Images.base64_forward)],
    ], pad=(0, 0))

    self.col2 = sg.Column([
      [sg.Text("00:00 / 00:00", key="mp3time", font=("Courrier New", 16, "bold"), expand_x=True, justification="center")],
      [sg.Slider(range=(0, 100), key="progress_slider", default_value=0, enable_events=True, size=(0, 15), orientation="horizontal", disable_number_display=True, expand_x=True, relief=sg.RELIEF_FLAT)]
    ], vertical_alignment="center", expand_x=True, expand_y=True, pad=(0, 0))

    self.col3 = sg.Column([
      [sg.Slider(range=(0, 100), key="volumeslider", default_value=100, enable_events=True, size=(3, 10), pad=(0, 5), orientation="vertical", disable_number_display=False, relief=sg.RELIEF_FLAT)],
    ], vertical_alignment="top", pad=(0, 0))

    self.menubar = [
      ["&Les journaux Monde", [ ["{} {}::_NEWS_".format(*window_data.scrapper.ExtractDataByItem(item)) for item in window_data.scrapper.Entries] ]],
      ["&Themes", self.GenerateThemesMenu()]
    ]

    self.layout = [
      [sg.MenubarCustom(self.menubar, key="menubar", bar_font=("", 10), bar_background_color=sg.theme_background_color(), bar_text_color=sg.theme_text_color())],
      [sg.HorizontalSeparator()],
      [sg.Text(window_data.title_str, key="title", font=("", 20, "bold"), justification="center", expand_x=True, pad=(0, 0))],
      [sg.Text(window_data.datetime_str, key="datetime", font=("", 14, "italic"), justification="center", expand_x=True, pad=(0, 0))],
      [sg.HorizontalSeparator()],
      [self.col1, self.col2, self.col3],
      [sg.HorizontalSeparator()],
      [sg.StatusBar(window_data.statusbar_str, key="statusbar", justification="center", relief=sg.RELIEF_RAISED, expand_x=True)]
    ]

    self.window = sg.Window(program_title, layout=self.layout, return_keyboard_events=True, location=window_data.location, finalize=True)
    self.LoadNewMP3()
    window_data.location = self.window.CurrentLocation()

    while True:
      event, values = self.window.read(window_data.UPDATE_TICK)
      #print(event, values)
      if event == "__TIMEOUT__":
        if isinstance(window_data.mp3handler, MP3Handler):
          if window_data.mp3handler.position == window_data.mp3handler.length: self.window['stop'].click()
          else: self.UpdateWindow(timer=True, progress_slider=True)
      if event == sg.WIN_CLOSED:
        if isinstance(window_data.mp3handler, MP3Handler): window_data.mp3handler.Detroy()
        break
      if event == "Left:37" and isinstance(window_data.mp3handler, MP3Handler):
        window_data.mp3handler.position -= 5
      if event == "Right:39" and isinstance(window_data.mp3handler, MP3Handler):
        window_data.mp3handler.position += 5
      if event == "playpause" and isinstance(window_data.mp3handler, MP3Handler):
        if window_data.mp3handler.status == window_data.mp3handler.STATUS_PLAYING: window_data.mp3handler.Pause()
        elif window_data.mp3handler.status == window_data.mp3handler.STATUS_PAUSED: window_data.mp3handler.Resume()
        elif window_data.mp3handler.status == window_data.mp3handler.STATUS_STOPPED: window_data.mp3handler.Play()
        self.UpdateWindow(playpause=True, statusbar=True)
      if event == "stop" and isinstance(window_data.mp3handler, MP3Handler):
        window_data.mp3handler.Stop()
        self.UpdateWindow(timer=True, progress_slider=True, playpause=True, statusbar=True)
      if event == "rewind" and isinstance(window_data.mp3handler, MP3Handler) and window_data.mp3handler.status == window_data.mp3handler.STATUS_PLAYING:
        window_data.mp3handler.position -= 30
      if event == "forward" and isinstance(window_data.mp3handler, MP3Handler) and window_data.mp3handler.status == window_data.mp3handler.STATUS_PLAYING:
        window_data.mp3handler.position += 30
      if event == "progress_slider" and isinstance(window_data.mp3handler, MP3Handler):
        window_data.mp3handler.position = values['progress_slider']
      if event == "volumeslider" and isinstance(window_data.mp3handler, MP3Handler):
        window_data.mp3handler.volume = values['volumeslider']
      if values['menubar']:
        menubar_item = f"{values['menubar'].split('::')[0]}"
        if values['menubar'].find("_NEWS_") != -1:
          self.LoadNewMP3(window_data.scrapper.EntryNumberByTitle(menubar_item))
        if values['menubar'].find("_THEME_") != -1:
          self._SwitchTheme(menubar_item)
          return


  def UpdateWindow(self, all=False, metadata=False, timer=False, progress_slider=False, volumeslider=False, playpause=False, statusbar=False):
    if metadata or all:
      self.window['title'].update(window_data.title_str)
      self.window['datetime'].update(window_data.datetime_str)
    if isinstance(window_data.mp3handler, MP3Handler):
      if timer or all: self.window['mp3time'].update(f"{time.strftime('%M:%S', time.gmtime(window_data.mp3handler.position))} / {time.strftime('%M:%S', time.gmtime(window_data.mp3handler.length))}")
      if progress_slider or all:
        if window_data.mp3handler.status == window_data.mp3handler.STATUS_PLAYING: self.window['progress_slider'].update(disabled=False)
        if window_data.mp3handler.status == window_data.mp3handler.STATUS_PAUSED: self.window['progress_slider'].update(disabled=True)
        if window_data.mp3handler.status == window_data.mp3handler.STATUS_STOPPED: self.window['progress_slider'].update(disabled=True)
        self.window['progress_slider'].update(range=(0, window_data.mp3handler.length), value=window_data.mp3handler.position)
      if volumeslider or all: self.window['volumeslider'].update(window_data.mp3handler.volume)
      if playpause or all:
        if window_data.mp3handler.status == window_data.mp3handler.STATUS_PLAYING:
          window_data.playpause = Images.base64_pause
          window_data.statusbar_str = "Playing..."
        if window_data.mp3handler.status == window_data.mp3handler.STATUS_PAUSED:
          window_data.playpause = Images.base64_play
          window_data.statusbar_str = "Paused..."
        if window_data.mp3handler.status == window_data.mp3handler.STATUS_STOPPED:
          window_data.playpause = Images.base64_play
          window_data.statusbar_str = "Stopped..."
        self.window['playpause'].update(image_data=window_data.playpause)
    if statusbar or all: self.window['statusbar'].update(window_data.statusbar_str)
    self.window.refresh()


  def LoadNewMP3(self, entry_number=0):
    global window_data, switch_theme
    if not switch_theme:
      # Reset all values
      window_data.statusbar_str = "Loading new MP3..."
      window_data.title_str = window_data.DEFAULT_TITLE_STR
      window_data.datetime_str = window_data.DEFAULT_DATETIME_STR
      if isinstance(window_data.mp3handler, MP3Handler): window_data.mp3handler.Detroy()
      self.UpdateWindow(all=True)

      window_data.statusbar_str = "Extracting data..."
      window_data.title_str, window_data.datetime_str = window_data.scrapper.ExtractDataByNumber(entry_number)
      self.UpdateWindow(statusbar=True, metadata=True)
      self.window.move(settings.Get("default_location")[0] - self.window.size[0], settings.Get("default_location")[1])

      window_data.statusbar_str = "Downloading..."
      window_data.mp3handler = MP3Handler(window_data.scrapper.ExtractUrl(entry_number))
      window_data.mp3handler.DownloadMP3()
      self.UpdateWindow(statusbar=True, timer=True)

      window_data.statusbar_str = "Loading..."
      window_data.mp3handler.LoadMP3()
      self.UpdateWindow(statusbar=True)

      self.window['playpause'].click()
    else:
      switch_theme = False
      self.UpdateWindow(all=True)


  def _SwitchTheme(self, new_theme):
    global window_data, switch_theme
    window_data.theme = new_theme
    settings.Set("theme", new_theme)
    switch_theme = True
    self.window.close()


  def GenerateThemesMenu(self):
    themes_menu = []
    themes_count = len(sg.theme_list())
    index = 0
    while index < themes_count:
      menu_content = []
      for _ in range(0, 30):
        if index < themes_count:
          menu_content.append(sg.theme_list()[index-1] + "::_THEME_")
          index+=1
        else: break
      menu_title = f"{index-29}-{index}" if (index % 30) == 0 else f"{index-(index % 30)}-{index}"
      themes_menu.append(menu_title)
      themes_menu.append(menu_content)
    return themes_menu
  

if __name__ == "__main__":
  GUI()
  while switch_theme: GUI()
  settings.SaveSettings()