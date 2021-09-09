import time
import PySimpleGUI as sg
import utils.images as images
import utils.scrapper as scrapper
import utils.settings as settings
from windows.themepicker import ThemePickerWindow
from utils.mp3handler import MP3Handler


window_title = ""
font = "Lucida"
theme = settings.json_settings['theme']
location = settings.json_settings['location']
window: sg.Window = None
mp3handler: MP3Handler = None
playpause = images.base64_play
title_str = "N/A"
datetime_str = "N/A"
timer_str = "00:00 / 00:00"
progressbar_values = {'actual': 0, 'max': 0}
statusbar_str = "{}".format(' ' * 40)

scrapper.load(settings.json_settings['url'])


def show():
  global window, mp3handler, location, timer_str

  window = _create_window()
  _load_new_MP3()
  location = window.CurrentLocation()

  while True:
    event, values = window.read(100)
    #print(event, values)

    if event == "__TIMEOUT__":
      if mp3handler.Position == mp3handler.Length: window['stop'].click()
      else:
        try: timer_str = f"{time.strftime('%M:%S', time.gmtime(mp3handler.Position))} / {time.strftime('%M:%S', time.gmtime(mp3handler.Length))}"
        except: timer_str = "00:00 / 00:00"
        _update_window(timer=True, progress_slider=True)
    if event == sg.WIN_CLOSED:
      del mp3handler
      break
    if event == "Left:37":
      mp3handler.Position -= 5
    if event == "Right:39":
      mp3handler.Position += 5
    if event == "playpause":
      if mp3handler.Status == mp3handler.STATUS_PLAYING: mp3handler.pause()
      elif mp3handler.Status == mp3handler.STATUS_PAUSED: mp3handler.resume()
      elif mp3handler.Status == mp3handler.STATUS_STOPPED: mp3handler.play()
      _update_window(playpause=True, statusbar=True)
    if event == "stop":
      try: mp3handler.stop()
      except: pass
      _update_window(timer=True, progress_slider=True, playpause=True, statusbar=True)
    if event == "rewind" and mp3handler.Status == mp3handler.STATUS_PLAYING:
      mp3handler.Position -= 30
    if event == "forward" and mp3handler.Status == mp3handler.STATUS_PLAYING:
      mp3handler.Position += 30
    if event == "progress_slider":
      mp3handler.Position = values['progress_slider']
    if event == "volumeslider":
      mp3handler.Volume = values['volumeslider']
    if values['menubar']:
      menubar_item = f"{str(values['menubar']).split('::')[0]}"
      if str(values['menubar']).find("_NEWS_") != -1:
        _load_new_MP3(scrapper.entry_number_by_title(menubar_item))
      if str(values['menubar']).find("_THEME_") != -1:
        ThemePickerWindow(window)
        window.close()
        window = _create_window()


def _create_window() -> sg.Window:
  col1 = sg.Column([
    [sg.Button(key="playpause", border_width=0, image_data=playpause), sg.Button(key="stop", border_width=0, image_data=images.base64_stop)],
    [sg.Button(key="rewind", border_width=0, image_data=images.base64_rewind), sg.Button(key="forward", border_width=0, image_data=images.base64_forward)],
  ], pad=(0, 0))

  col2 = sg.Column([
    [sg.Text("00:00 / 00:00", key="mp3time", font=("Courrier New", 22, "bold"), expand_x=True, justification="center")],
    [sg.Slider(range=(0, 100), key="progress_slider", default_value=0, enable_events=True, size=(0, 15), orientation="horizontal", disable_number_display=True, expand_x=True, relief=sg.RELIEF_FLAT)]
  ], vertical_alignment="center", expand_x=True, expand_y=True, pad=(0, 0))

  col3 = sg.Column([
    [sg.Slider(range=(0, 100), key="volumeslider", default_value=100, enable_events=True, size=(3, 10), pad=(0, 5), orientation="vertical", disable_number_display=False, relief=sg.RELIEF_FLAT)],
  ], vertical_alignment="top", pad=(0, 0))

  menubar = [
    ["&Les journaux Monde", [ ["{} {}::_NEWS_".format(*scrapper.extract_data_by_item(item)) for item in scrapper.entries] ]],
    ["&Themes", ["Select new theme::_THEME_"]]
  ]

  layout = [
    [sg.MenubarCustom(menubar, key="menubar", bar_font=("", 10), bar_background_color=sg.theme_background_color(), bar_text_color=sg.theme_text_color())],
    [sg.HorizontalSeparator()],
    [sg.Text(title_str, key="title", font=("", 20, "bold"), justification="center", expand_x=True, pad=(0, 0))],
    [sg.Text(datetime_str, key="datetime", font=("", 14, "italic"), justification="center", expand_x=True, pad=(0, 0))],
    [sg.HorizontalSeparator()],
    [col1, col2, col3],
    [sg.HorizontalSeparator()],
    [sg.StatusBar(statusbar_str, key="statusbar", justification="center", relief=sg.RELIEF_RAISED, expand_x=True)]
  ]
  return sg.Window(window_title, font=font, layout=layout, return_keyboard_events=True, location=location, finalize=True)


def _update_window(metadata=False, timer=False, progress_slider=False, volumeslider=False, playpause=False, statusbar=False):
  global statusbar_str
  if metadata:
    window['title'].update(title_str)
    window['datetime'].update(datetime_str)
  if timer: window['mp3time'].update(timer_str)
  if progress_slider:
    if mp3handler.Status == mp3handler.STATUS_PLAYING: window['progress_slider'].update(disabled=False)
    if mp3handler.Status == mp3handler.STATUS_PAUSED: window['progress_slider'].update(disabled=True)
    if mp3handler.Status == mp3handler.STATUS_STOPPED: window['progress_slider'].update(disabled=True)
    try: window['progress_slider'].update(range=(0, mp3handler.Length), value=mp3handler.Position)
    except: window['progress_slider'].update(range=(0, 0), value=0)
  if volumeslider: window['volumeslider'].update(mp3handler.Volume)
  if playpause:
    if mp3handler.Status == mp3handler.STATUS_PLAYING:
      playpause = images.base64_pause
      statusbar_str = "Playing..."
    if mp3handler.Status == mp3handler.STATUS_PAUSED:
      playpause = images.base64_play
      statusbar_str = "Paused..."
    if mp3handler.Status == mp3handler.STATUS_STOPPED:
      playpause = images.base64_play
      statusbar_str = "Stopped..."
    window['playpause'].update(image_data=playpause)
  if statusbar: window['statusbar'].update(statusbar_str)
  window.refresh()


def _load_new_MP3(entry_number=0):
  global mp3handler, statusbar_str, timer_str, title_str, datetime_str

  del mp3handler
  statusbar_str = "Loading new MP3..."
  timer_str = "00:00 / 00:00"
  title_str = "N/A"
  datetime_str = "N/A"
  _update_window(statusbar=True, timer=True, metadata=True)

  statusbar_str = "Extracting data..."
  title_str, datetime_str = scrapper.extract_data_by_number(entry_number)
  _update_window(statusbar=True, metadata=True)
  window.move(settings.json_settings['location'][0] - window.size[0], settings.json_settings['location'][1])

  statusbar_str = "Downloading..."
  mp3handler = MP3Handler(scrapper.extract_url(entry_number))
  mp3handler.download_MP3()
  _update_window(statusbar=True, timer=True)

  statusbar_str = "Loading..."
  mp3handler.load_MP3()
  _update_window(statusbar=True)
  
  playpause_button: sg.Button = window['playpause']
  playpause_button.click()