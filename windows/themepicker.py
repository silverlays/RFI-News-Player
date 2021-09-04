import PySimpleGUI as sg
from utils.settings import Settings


class ThemePickerWindow():
  def __init__(self, parent_window: sg.Window, settings: Settings):
    self.parent_window = parent_window
    self.settings = settings
    self.window = self._CreateWindow()
    
    while(True):
      event, values = self.window.read()
      #print(event, values)

      if event in (sg.WIN_CLOSED, "save_button"):
        settings.Set("theme", values['new_theme'])
        self.window.close()
        break
      if event == "Down:40": self._NextTheme()
      if event == "Up:38": self._PreviousTheme()
      if event == "new_theme":
        sg.theme(values['new_theme'])
        self._RefreshWindow()
  
  def _CreateWindow(self) -> sg.Window:
    layout = [
      [sg.Text(self._SetThemeLabel(), key="theme_label", expand_x=True, justification="center")],
      [sg.Combo(sg.theme_list(), key="new_theme", default_value=sg.theme(), expand_x=True, change_submits=True)],
      [sg.Ok(button_text="Sauvegarder", key="save_button", font=("", 10, "bold"), focus=True)]
    ]
    return sg.Window(title="Select a new theme...", layout=layout, modal=True, return_keyboard_events=True, use_custom_titlebar=False, disable_close=True, disable_minimize=True, size=self._SetSize(), location=self._SetLocation(), auto_size_buttons=False, default_button_element_size=(10, 0))

  def _RefreshWindow(self):
    self.window.close()
    self.window = self._CreateWindow()

  def _SetSize(self) -> tuple[int, int]:
    width = self.parent_window.size[0]
    height = 100
    return (width, height)

  def _SetLocation(self) -> tuple[int, int]:
    parent_size_y = self.parent_window.size[1]
    parent_location_x, parent_location_y = self.parent_window.CurrentLocation()
    x = parent_location_x
    y = (parent_location_y + parent_size_y) + 35
    return (x, y)
  
  def _SetThemeLabel(self, update=False):
    position = sg.theme_list().index(sg.theme()) + 1
    count = len(sg.theme_list())
    label_text = f"Theme {position}/{count}"
    if update:
      self.window['theme_label'].update(label_text)
      self.window.read(0)
    else: return label_text

  def _NextTheme(self):
    current_index = sg.theme_list().index(self.window['new_theme'].DefaultValue)
    try: new_theme = sg.theme_list()[current_index+1]
    except IndexError: new_theme = sg.theme_list()[0]
    sg.theme(new_theme)
    self._RefreshWindow()

  def _PreviousTheme(self):
    current_index = sg.theme_list().index(self.window['new_theme'].DefaultValue)
    new_theme = sg.theme_list()[current_index-1]
    sg.theme(new_theme)
    self._RefreshWindow()