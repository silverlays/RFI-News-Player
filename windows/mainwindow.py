import time
import PySimpleGUI as sg
from utils.images import Images
from utils.scrapper import Scrapper
from utils.mp3handler import MP3Handler
from utils.settings import Settings
from windows.themepicker import ThemePickerWindow


class MainWindow():
  def __init__(self, window_title, settings: Settings):
    self.window_title = window_title
    self.settings = settings
    
    self.font = "Lucida"
    self.theme = settings.Get("theme")
    self.location = settings.Get("default_location")
    self.scrapper = Scrapper(settings.Get("default_url"))
    self.mp3handler = MP3Handler
    self.playpause = Images.base64_play
    self.title_str = "N/A"
    self.datetime_str = "N/A"
    self.timer_str = "00:00 / 00:00"
    self.progressbar_values = {'actual': 0, 'max': 0}
    self.statusbar_str = "{}".format(' ' * 40)

    self.window = self._CreateWindow()
    self._LoadNewMP3()
    self.location = self.window.CurrentLocation()

    while True:
      event, values = self.window.read(100)
      #print(event, values)

      if event == "__TIMEOUT__":
        if self.mp3handler.position == self.mp3handler.length: self.window['stop'].click()
        else:
          try: self.timer_str = f"{time.strftime('%M:%S', time.gmtime(self.mp3handler.position))} / {time.strftime('%M:%S', time.gmtime(self.mp3handler.length))}"
          except: self.timer_str = "00:00 / 00:00"
          self._UpdateWindow(timer=True, progress_slider=True)
      if event == sg.WIN_CLOSED:
        del self.mp3handler
        break
      if event == "Left:37":
        self.mp3handler.position -= 5
      if event == "Right:39":
        self.mp3handler.position += 5
      if event == "playpause":
        if self.mp3handler.status == self.mp3handler.STATUS_PLAYING: self.mp3handler.Pause()
        elif self.mp3handler.status == self.mp3handler.STATUS_PAUSED: self.mp3handler.Resume()
        elif self.mp3handler.status == self.mp3handler.STATUS_STOPPED: self.mp3handler.Play()
        self._UpdateWindow(playpause=True, statusbar=True)
      if event == "stop":
        try: self.mp3handler.Stop()
        except: pass
        self._UpdateWindow(timer=True, progress_slider=True, playpause=True, statusbar=True)
      if event == "rewind" and self.mp3handler.status == self.mp3handler.STATUS_PLAYING:
        self.mp3handler.position -= 30
      if event == "forward" and self.mp3handler.status == self.mp3handler.STATUS_PLAYING:
        self.mp3handler.position += 30
      if event == "progress_slider":
        self.mp3handler.position = values['progress_slider']
      if event == "volumeslider":
        self.mp3handler.volume = values['volumeslider']
      if values['menubar']:
        menubar_item = f"{values['menubar'].split('::')[0]}"
        if values['menubar'].find("_NEWS_") != -1:
          self._LoadNewMP3(self.scrapper.EntryNumberByTitle(menubar_item))
        if values['menubar'].find("_THEME_") != -1:
          ThemePickerWindow(self.window, self.settings)
          self.window.close()
          self.window = self._CreateWindow()

  def _CreateWindow(self) -> sg.Window:
    col1 = sg.Column([
      [sg.Button(key="playpause", border_width=0, image_data=self.playpause), sg.Button(key="stop", border_width=0, image_data=Images.base64_stop)],
      [sg.Button(key="rewind", border_width=0, image_data=Images.base64_rewind), sg.Button(key="forward", border_width=0, image_data=Images.base64_forward)],
    ], pad=(0, 0))

    col2 = sg.Column([
      [sg.Text("00:00 / 00:00", key="mp3time", font=("Courrier New", 22, "bold"), expand_x=True, justification="center")],
      [sg.Slider(range=(0, 100), key="progress_slider", default_value=0, enable_events=True, size=(0, 15), orientation="horizontal", disable_number_display=True, expand_x=True, relief=sg.RELIEF_FLAT)]
    ], vertical_alignment="center", expand_x=True, expand_y=True, pad=(0, 0))

    col3 = sg.Column([
      [sg.Slider(range=(0, 100), key="volumeslider", default_value=100, enable_events=True, size=(3, 10), pad=(0, 5), orientation="vertical", disable_number_display=False, relief=sg.RELIEF_FLAT)],
    ], vertical_alignment="top", pad=(0, 0))

    menubar = [
      ["&Les journaux Monde", [ ["{} {}::_NEWS_".format(*self.scrapper.ExtractDataByItem(item)) for item in self.scrapper.Entries] ]],
      ["&Themes", ["Select new theme::_THEME_"]]
    ]

    layout = [
      [sg.MenubarCustom(menubar, key="menubar", bar_font=("", 10), bar_background_color=sg.theme_background_color(), bar_text_color=sg.theme_text_color())],
      [sg.HorizontalSeparator()],
      [sg.Text(self.title_str, key="title", font=("", 20, "bold"), justification="center", expand_x=True, pad=(0, 0))],
      [sg.Text(self.datetime_str, key="datetime", font=("", 14, "italic"), justification="center", expand_x=True, pad=(0, 0))],
      [sg.HorizontalSeparator()],
      [col1, col2, col3],
      [sg.HorizontalSeparator()],
      [sg.StatusBar(self.statusbar_str, key="statusbar", justification="center", relief=sg.RELIEF_RAISED, expand_x=True)]
    ]
    return sg.Window(self.window_title, font=self.font, layout=layout, return_keyboard_events=True, location=self.location, finalize=True)

  def _UpdateWindow(self, metadata=False, timer=False, progress_slider=False, volumeslider=False, playpause=False, statusbar=False):
    if metadata:
      self.window['title'].update(self.title_str)
      self.window['datetime'].update(self.datetime_str)
    if timer: self.window['mp3time'].update(self.timer_str)
    if progress_slider:
      if self.mp3handler.status == self.mp3handler.STATUS_PLAYING: self.window['progress_slider'].update(disabled=False)
      if self.mp3handler.status == self.mp3handler.STATUS_PAUSED: self.window['progress_slider'].update(disabled=True)
      if self.mp3handler.status == self.mp3handler.STATUS_STOPPED: self.window['progress_slider'].update(disabled=True)
      try: self.window['progress_slider'].update(range=(0, self.mp3handler.length), value=self.mp3handler.position)
      except: self.window['progress_slider'].update(range=(0, 0), value=0)
    if volumeslider: self.window['volumeslider'].update(self.mp3handler.volume)
    if playpause:
      if self.mp3handler.status == self.mp3handler.STATUS_PLAYING:
        self.playpause = Images.base64_pause
        self.statusbar_str = "Playing..."
      if self.mp3handler.status == self.mp3handler.STATUS_PAUSED:
        self.playpause = Images.base64_play
        self.statusbar_str = "Paused..."
      if self.mp3handler.status == self.mp3handler.STATUS_STOPPED:
        self.playpause = Images.base64_play
        self.statusbar_str = "Stopped..."
      self.window['playpause'].update(image_data=self.playpause)
    if statusbar: self.window['statusbar'].update(self.statusbar_str)
    self.window.refresh()

  def _LoadNewMP3(self, entry_number=0):
    del self.mp3handler
    self.statusbar_str = "Loading new MP3..."
    self.timer_str = "00:00 / 00:00"
    self.title_str = "N/A"
    self.datetime_str = "N/A"
    self._UpdateWindow(statusbar=True, timer=True, metadata=True)

    self.statusbar_str = "Extracting data..."
    self.title_str, self.datetime_str = self.scrapper.ExtractDataByNumber(entry_number)
    self._UpdateWindow(statusbar=True, metadata=True)
    self.window.move(self.settings.Get("default_location")[0] - self.window.size[0], self.settings.Get("default_location")[1])

    self.statusbar_str = "Downloading..."
    self.mp3handler = MP3Handler(self.scrapper.ExtractUrl(entry_number))
    self.mp3handler.DownloadMP3()
    self._UpdateWindow(statusbar=True, timer=True)

    self.statusbar_str = "Loading..."
    self.mp3handler.LoadMP3()
    self._UpdateWindow(statusbar=True)

    self.window['playpause'].click()