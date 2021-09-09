# Changes compared to v1.4:
#
# - Can now handle multiple windows
# - Added <Theme Picker> window
# - Cleaned code (again)


import PySimpleGUI as sg
import windows.mainwindow as mainwindow
import utils.images as images
import utils.settings as settings


__version__ = "1.5"
__program_title__ = f"RFI News Player v{__version__}"


settings.load_settings()
sg.SetGlobalIcon(images.base64_app)
sg.theme(settings.json_settings['theme'])
mainwindow.window_title = __program_title__
mainwindow.show()
settings.save_settings()