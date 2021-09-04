# Changes compared to v1.4:
#
# - Can now handle multiple windows
# - Added <Theme Picker> window
# - Cleaned code (again)


import PySimpleGUI as sg
from windows.mainwindow import MainWindow
from utils.images import Images
from utils.settings import Settings


__version__ = "1.5"
__program_title__ = f"RFI News Player v{__version__}"


settings = Settings()
sg.SetGlobalIcon(Images.base64_app)
sg.theme(settings.Get("theme"))
MainWindow(__program_title__, settings)
settings.SaveSettings()