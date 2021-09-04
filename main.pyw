# Changes compared to v1.0:
#
# - Add possibility to select any of available MP3.
# - Cleanup code (separate classes for Scrapper and MP3)
# - Base64 icons for reliability.
# - Added documentation


import bs4, json, re, time, os
import urllib.request as request
import PySimpleGUI as sg
from mutagen.mp3 import MP3
from audioplayer import AudioPlayer

version = "1.1"
program_title = f"RFI News Player v{version}"

default_url = "https://www.rfi.fr/fr/journaux-monde/"
default_location = (1612, 0)

class GUI():
  def __init__(self):
    self.update_tick = 100
    self.elapsed_secs = 0
    self.scrapper = Scrapper(default_url)
    self.mp3 = MP3Handler()
    self.window = sg.Window(program_title, location=default_location)
    self.window.Font = "Lucida"

    self.col1 = sg.Column([
      [sg.Button(key="playpause", border_width=0, image_data=Images.base64_play), sg.Button(key="stop", border_width=0, image_data=Images.base64_stop)],
      [sg.Slider(range=(0, 100), key="volumeslider", default_value=100, enable_events=True, size=(0, 10), orientation="horizontal", disable_number_display=True, expand_x=True, relief=sg.RELIEF_FLAT)]
    ], pad=(0, 0))

    self.col2 = sg.Column([
      [sg.ProgressBar(100, key="progressbar", size=(10, 0), border_width=1, relief=sg.RELIEF_RAISED, expand_x=True, expand_y=True)]
    ], vertical_alignment="center", expand_x=True, expand_y=True, pad=(0, 0))

    self.col3 = sg.Column([
      [sg.Text("00:00 / n/a", key="mp3time", font=("", 10))],
      [sg.Text("Volume: n/a", key="mp3volume", font=("", 10))]
    ], vertical_alignment="center", pad=(0, 0))

    self.menubar = [
      ["&Les journaux Monde", [ ["{} {}".format(*self.scrapper.ExtractDataByItem(item)) for item in self.scrapper.Entries] ]]
    ]

    self.layout = [
      [sg.MenubarCustom(self.menubar, key="menubar", bar_font=("", 10), bar_background_color=sg.theme_background_color(), bar_text_color=sg.theme_text_color())],
      [sg.HorizontalSeparator()],
      [sg.Text("N/A", key="title", font=("", 20, "bold"), justification="center", expand_x=True, pad=(0, 0))],
      [sg.Text("N/A", key="datetime", font=("", 14, "bold"), justification="center", expand_x=True, pad=(0, 0))],
      [sg.HorizontalSeparator()],
      [self.col1, self.col2, self.col3],
      [sg.HorizontalSeparator()],
      [sg.StatusBar("Downloading...", key="status", justification="center", expand_x=True, relief=sg.RELIEF_RAISED)]
    ]

    self.window.layout(self.layout)
    self.window.read(self.update_tick)
    self._LoadNewMP3()

    while True:
      event, values = self.window.read(1000)
      print(event, values)
      if event == sg.WIN_CLOSED:
        self.mp3.Detroy()
        break
      elif event == "playpause":
        if self.mp3.playing:
          self.mp3.PauseResume()
          self.window['playpause'].update(image_data=Images.base64_play)
          self.window['status'].update("Paused...")
        elif not self.mp3.playing:
          self.mp3.Play() if self.mp3.stopped else self.mp3.PauseResume()
          self.window['playpause'].update(image_data=Images.base64_pause)
          self.window['status'].update("Playing...")
      elif event == "stop":
        self.mp3.Stop()
        self.elapsed_secs = 0
        self.window['playpause'].update(image_data=Images.base64_play)
        self.window['status'].update("Stopped...")
        self._UpdateTimer()
      elif event == "volumeslider":
        self.mp3.ChangeVolume(int(values["volumeslider"]))
        self._UpdateVolume()
      elif event == "__TIMEOUT__":
        if self.elapsed_secs >= self.mp3.mp3_length: self.window["stop"].click()
        elif self.mp3.playing: self.elapsed_secs += 1
        self._UpdateTimer()
        self._UpdateProgressBar()
        self._UpdateVolume()
      else:
        self.window['status'].update("Loading new...")
        self._LoadNewMP3(self.scrapper.EntryNumberByTitle(event))
  
  def _LoadNewMP3(self, entry_number=0) -> None:
    """Load a new MP3 into player.

    Args:
        entry_number (int, optional): Number obtained from Scrapper.EntryNumberByTitle() method. Defaults to 0 (most recent).
    """
    # Reset all values
    self.elapsed_secs = 0
    self.window['title'].update("N/A")
    self.window['datetime'].update("N/A")
    self.window['mp3time'].update("00:00 / n/a")
    self.window['mp3volume'].update("Volume: n/a")
    self.window['progressbar'].update_bar(0, 0)

    # Updating values (1/2) 
    self.title, self.datetime = self.scrapper.ExtractDataByNumber(entry_number)
    self.window['title'].update(self.title)
    self.window['datetime'].update(self.datetime)
    self.window.read(self.update_tick)
    self.window.Move(default_location[0] - self.window.size[0], default_location[1])

    # Download and updating values (2/2)
    self.window['status'].update("Downloading...")
    self.mp3 = MP3Handler(self.scrapper.ExtractUrl(entry_number))
    self.mp3.DownloadMP3()
    self._UpdateTimer()
    self._UpdateProgressBar()
    self.window.read(self.update_tick)

    # Playing MP3
    self.window['status'].update("Loading player...")
    self.mp3.LoadMP3()
    self.window.read(self.update_tick)
    self.mp3.Play()
    self.window['playpause'].update(image_data=Images.base64_pause)
    self.window['status'].update("Playing...")

  def _UpdateTimer(self) -> None:
    elapsed = time.strftime("%M:%S", time.gmtime(self.elapsed_secs))
    total = time.strftime("%M:%S", time.gmtime(self.mp3.mp3_length))
    self.window['mp3time'].update(f"{elapsed} / {total}")
  
  def _UpdateProgressBar(self) -> None:
    self.window['progressbar'].update_bar(self.elapsed_secs, self.mp3.mp3_length)
  
  def _UpdateVolume(self) -> None:
    self.window['mp3volume'].update(f"Volume: {self.mp3.mp3_player.volume}")


class Scrapper():
  def __init__(self, base_url: str):
    with request.urlopen(base_url) as response: 
      html_data = bs4.BeautifulSoup(response.read(), "html.parser")
    list = html_data.select("div.o-layout-list script")
    self._entries = [json.loads(item.contents[0]) for item in list]
    pass
  
  def ExtractDataByItem(self, item: dict) -> tuple[str, str]:
    """Extract title and datetime from an <self.Entries> item.

    Args:
        item (dict): <self.Entries> item.

    Returns:
        tuple[str, str]: Tuple including title, datetime.
    """
    groups = re.findall("([\s\S]+) ([0-9]{2}/[0-9]{2}/{0,1}[0-9]{0,}) ([\s\S]+)", item['diffusion']['title'])
    title, date, time = groups[0]
    return title, f"{date} {time}"

  def ExtractDataByNumber(self, entry_number: int) -> tuple[str, str]:
    """Extract title and datetime from an <self.Entries> index.

    Args:
        entry_number (int): <self.Entries> index.

    Returns:
        tuple[str, str]: Tuple including title, datetime.
    """
    groups = re.findall("([\s\S]+) ([0-9]{2}/[0-9]{2}/{0,1}[0-9]{0,}) ([\s\S]+)", self._entries[entry_number]['diffusion']['title'])
    title, date, time = groups[0]
    return title, f"{date} {time}"
  
  def EntryNumberByTitle(self, title: str) -> int:
    """Searches for an entry number from a title.

    Args:
        title (str): EXACT title of the show.

    Returns:
        int: <self.Entries> index.
    """
    return [i for i in range(len(self._entries)) if self._entries[i]['diffusion']['title'] == title][0]
  
  def ExtractUrl(self, entry_number: int) -> str:
    """Extract URL from an entry index.

    Args:
        entry_number (int): Entry index.

    Returns:
        str: the URL of the show.
    """
    entry = self._entries[entry_number] 
    return entry['sources'][0]['url']
  
  @property
  def Entries(self):
    """
    Full list of shows (JSON format).
    """
    return self._entries


class MP3Handler():
  def __init__(self, mp3_url=None, mp3_filename="rfitemp.mp3") -> None:
    self.mp3_url = mp3_url
    self.mp3_filename = mp3_filename
    self.volume_step = 2
    self.mp3_player = None # Will be instanced after downloading
  
  def DownloadMP3(self) -> None:
    self.mp3_file = request.urlretrieve(url=self.mp3_url, filename=self.mp3_filename)[0]
    self.mp3_length = MP3(self.mp3_file).info.length
  
  def LoadMP3(self) -> None:
    self.mp3_player = AudioPlayer(self.mp3_file)
    self.playing = False
    self.stopped = True
  
  def Play(self) -> None:
    if self.mp3_player:
      self.mp3_player.play()
      self.playing = True
      self.stopped = False
  
  def PauseResume(self) -> None:
    if self.mp3_player:
      if not self.stopped and self.playing:
        self.mp3_player.pause()
        self.playing = False
      elif not self.stopped and not self.playing:
        self.mp3_player.resume()
        self.playing = True
  
  def Stop(self) -> None:
    if self.mp3_player:
      self.mp3_player.stop()
      self.playing = False
      self.stopped = True

  def ChangeVolume(self, new_value) -> None:
    if self.mp3_player: self.mp3_player.volume = new_value
  
  def Detroy(self) -> None:
    if self.mp3_player: self.mp3_player.close()
    if os.path.exists(self.mp3_filename): os.remove(self.mp3_filename)


class Images():
  base64_app = b"iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAACl1BMVEXhIBngIBviIBnbHx/gIBnhIBzhIB/hISThISXhIB7hISngICLfHwDgIAHgIAfgIADgIALgIBfgIB/lQUzoYmvqcHjqbnbkOUXkKDjkLz3kLTvkKjjhIBvhISHgIAPhIADuk5n51tj98vP/+/z////ump7iIA/4zdH98fL76+z86+376+398PH51djjISngIBHgIA3jISL3y87+/v7+//7unKHiIA364OP76OrjISzgIA/1v8P+/f3vm6H63N/75OfpbHT//P3+9/j0vcDsi5HrfYXlTVbgIB763d///f785efhISvzubz++frrf4b52dv+/Pz2xcjhLTThISbkMj/87e7tlpzmTFb+9vf//f3rd3/hIBH3zND97/H76ev76uz87vD509bhISLnV2H++vrpbHXjJDTkKjnjJjXhISjhIivnW2T++vvqb3fiJjDgIBbnWmPoWWPdHwDiIS3tj5XiISTiIADshYz2y83woabeHwDnX2jzsbftlJnump/vnKHnXWThIBfshIvum6Dtl5zumJzsiY7kN0T/9/n+7/HkLT3nW2b74eP0vsLnYWn//v7vnaP73+P85+rkNkP+9PX87u/iIBPnVl/+9vjxp6zoV2LkKDf+///53d/+9fXkIR/74+XlLUD++Pn++PjumJ3///7xo6nkIjDhJjDuh47lQ07nV2DnU13nVV/kMD7gIBP+8/X85+nsio/hJC/oZG3kPEj97/D52tzqbXXkO0bwoqbpa3TkOkbpaXLkOEX+8/TlQEzkNkTkKDn87e/jIjTgIAbaHx/eICHiISH87O7pa3PnXGbkMT/84+X629/jIjHgIAnnU1775+n87O386uzoY23kLDrkKznkLDvkLjvkLj3cICHfICH8N4UMAAAAAWJLR0QktAb5mQAAAAd0SU1FB+UIEg8KLfRRB4YAAAL2SURBVEjHvZXnX9NAGMdTuaRNfWgsDoZJi3AgIoqK4qoiOCrWjSiooFYUURQcOFDRKu4t4BYR996Ie+Hee/4xXi6h8IEWyAv9vbrL57733DPyPAyjRbpmPprONwAgpAVADMvpDQaeQDznFk++ewYQa2wORL4sQiahhSrBhLxYMHN+ILRs1bqNv4llAgKDVAW2FT1bQJLFGtwuJDQUh4ExvH1Eh0iqjlGdOkfzHgDEdenaDWMc0x33AGNsT+xWr959PABINEBfbLPJJ/oRC/2xLYbKhuM8AoweBsRjG04YOGjwEMEeOxTblPsT8TCPgOiA4eTMiJFymCTUOMDaraPwaDwGxhqTOBY1/iROGJdMLh0PDrLhUeNOSzAhBePUiWCQzaFJk9PSp1ClT51WP6yIEZ0wPQPj+BmgVz7MzAxQlTmrVuKQaMwSEWKzZifBnGwCzIV5RoeERGT3c8uO3AAScwDMjEEHYIVcGZi/QI4Sj3RQS0isBtjohcGL8vSweMnSZfnLCZC4YmVB2KrVAudas7ZwHVVhwXopR1QBDjZs3LQZtmzFeFv+9my8QwnLTnDE7qqJ0u6aKHFCUXHJnr37EvYfOCj7QIFDci2FH/aYBwKUlhwpiztKPFGAjPLyY/HHCUAyfYLKVjvTHBSllJ2MPAWnnQYapdQzZ8+dv3Dxks5LaXDgfzniylW4xjBOJazX80lUTBzyCtyowDetSSQzKlAJRsnJst6BW2n4Ni0fFbgDepKmBoC7IfgerYYagNaSV+D+g5SHpPybDjwqrnjsy2mwUFT6pOoprxXQbOHfP+nfAM80Aq7n2gDR/EIj4JL+k9Pkn35ZDeRm4JjQVyrgpbeSrlEeVWVRMv06kdxXSQGvvZUT3rx99/4DT3vrx0/Jn798Badiod7Iok8SEf/tO0saG1mapR8/g37lmUWlt9Ydiq7fSqtEFgtiEF2ayYj1zRHphqkzdpGaB7LgeQapS3mIi+qm7mCvBposneuPRkBxWgvg8xdv2kkNK0oYRwAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyMS0wOC0xOFQxNToxMDo0NCswMDowMNcL7PcAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjEtMDgtMThUMTU6MTA6NDQrMDA6MDCmVlRLAAAAAElFTkSuQmCC"
  base64_play = b"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LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIxLTA4LTE4VDE3OjM1OjQ4KzAyOjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMS0wOC0xOFQxNzozOTozMSswMjowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMS0wOC0xOFQxNzozOTozMSswMjowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6YzdmMzIxOTMtYmZiZS05YjQyLWEyZTQtMDU1ZGMzNjU5ZjkyIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOmM3ZjMyMTkzLWJmYmUtOWI0Mi1hMmU0LTA1NWRjMzY1OWY5MiIgeG1wTU06T3JpZ2luYWxEb2N1bWVudElEPSJ4bXAuZGlkOmM3ZjMyMTkzLWJmYmUtOWI0Mi1hMmU0LTA1NWRjMzY1OWY5MiI+IDx4bXBNTTpIaXN0b3J5PiA8cmRmOlNlcT4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImNyZWF0ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6YzdmMzIxOTMtYmZiZS05YjQyLWEyZTQtMDU1ZGMzNjU5ZjkyIiBzdEV2dDp3aGVuPSIyMDIxLTA4LTE4VDE3OjM1OjQ4KzAyOjAwIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+qYGrwQAAAKBJREFUSMdj+P//PwMtMcOoBSPYAiBwAWJXBiIAuRaUgPQC8Wkg5qWFBS1A/AWIN0Et6qS2BdOA+D3UDCsg/gG1KISaFnxAM6sJasklIOanhQUw0A+1aCUQq9HCAl+oBQ+A2IaaFoCS7h+o4bbUDCIOID4ENXgytSK5D4gfAnEB1ODjuPIDuRYUQw3+CsT2tMho0UBcQ7OiYrS4HrWAaAwAispUdCNjFJ8AAAAASUVORK5CYII="
  base64_pause = b"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAJnGlDQ1BaT1dJRSBYTCBMQ0QgQ29sb3IgUHJvZmlsZSxENjUwMAAASMeVlmk4lQkbgJ/3fc/uHNs59u3Y9307yHqsIfuaQse+O9aQSkYTJiVJKENGoaHRWDIlSWkxQqFSDRmhTKMpVNSZH33f1Vzf9/35nl/3dT9/nuffDUBRc2W7+6AAkJiUzvV2smMGBgUzibNABAwogAE+nJOW4u7j6AsAYOewzcvU0dAQvg4CsDYJCADAfW1XD3tb+P+GwknhpgPAJgAoZ6WnpAMgSgDA2OXrzQZAWAAkavQ/mPsPjohM4wCQ7QEglxsYFAxA7gcARvQXfgAAjF1feBEAGJyY8AgA8iYAaKVHZqcDALCTU3ZzY6Nj0plqHHWmgZ6+KdMuMsmL6ZLE0QEACAwKZn45dW3iX39qcjK4mV8cDgAADxQQAAZIgCwoghpogwGYwhawBUdwBU/wg2DYCRyIgUTgQhbkwX4oghI4AsehGuqgEZqhDTqgGy7DNbgJd2EUJmAaZmAeXsEKrMEGgiBEhIbQEQlEDlFGNBEDhIVYIQ6IG+KNBCFhSDSShGQgecgBpAQpR6qReqQZ+Qm5hFxDbiNjyCNkFllC/kI+ohhKRRmoDKqC6qIs1BZ1RX3RHWg0mormoIXoYbQKbUDPo13oNfQuOoHOoK/QVQwwPkwUk8e0MRbGxjywYCwK42L5WDFWiTVgbVgvNoTdx2awZewDjoCj45g4bZwFzhnnh+PgUnH5uFJcNe4crgs3iLuPm8Wt4D7jaXhpvCbeHO+CD8RH47PwRfhKfBO+E38DP4Gfx68RCARRgirBlOBMCCLEEXIJpYRThHZCP2GMMEdYJRKJEkRNoiXRgxhOTCcWEU8SzxOvEseJ88T3JD6SHMmA5EgKJiWRCkiVpBZSH2mctEDaIAuSlcnmZA9yBHk3uYzcSO4l3yPPkzcoQhRViiXFlxJH2U+porRRblCeUN7y8fEp8JnxefHF8u3jq+K7wHeLb5bvA1WYqkFlU0OoGdTD1LPUfuoj6lsajaZCs6EF09Jph2nNtOu0Z7T3/HR+HX4X/gj+vfw1/F384/yvBcgCygK2AjsFcgQqBS4K3BNYFiQLqgiyBcMF8wVrBC8JTgmuCtGF9IU8hBKFSoVahG4LLQoThVWEHYQjhAuFzwhfF56jY3RFOpvOoR+gN9Jv0OcZBIYqw4URxyhh/MgYYayICIsYifiLZIvUiFwRmRHFRFVEXUQTRMtEO0QnRT+KyYjZikWKHRJrExsXWxeXErcRjxQvFm8XnxD/KMGUcJCIlzgq0S3xVBInqSHpJZkleVryhuSyFEPKQoojVSzVIfVYGpXWkPaWzpU+Iz0svSojK+MkkyJzUua6zLKsqKyNbJxshWyf7JIcXc5KLlauQu6q3EumCNOWmcCsYg4yV+Sl5Z3lM+Tr5UfkNxRUFfwUChTaFZ4qUhRZilGKFYoDiitKckruSnlKrUqPlcnKLOUY5RPKQ8rrKqoqASoHVbpVFlXFVV1Uc1RbVZ+o0dSs1VLVGtQeqBPUWerx6qfURzVQDWONGI0ajXuaqKaJZqzmKc0xLbyWmVaSVoPWlDZV21Y7U7tVe1ZHVMdNp0CnW+e1rpJusO5R3SHdz3rGegl6jXrT+sL6W/UL9Hv1/zLQMOAY1Bg8MKQZOhruNewxfGOkaRRpdNrooTHd2N34oPGA8ScTUxOuSZvJkqmSaZhprekUi8HyZJWybpnhzezM9ppdNvtgbmKebt5h/qeFtkW8RYvF4hbVLZFbGrfMWSpYhlvWW85YMa3CrL63mrGWtw63brB+bqNoE2HTZLNgq24bZ3ve9rWdnh3XrtNunW3O3sPut8fsneyL7UcchB38HKodnjkqOEY7tjquOBk75Tr1O+OdXZ2POk+5yLhwXJpdVraabt2zddCV6urjWu363E3DjevW6466b3U/5v5km/K2pG3dHuDh4nHM46mnqmeq5y9eBC9PrxqvF9763nneQz50n1CfFp81XzvfMt9pPzW/DL8BfwH/EP9m//UA+4DygJlA3cA9gXeDJINig3qCicH+wU3Bq9sdth/fPh9iHFIUMrlDdUf2jts7JXcm7LwSKhAaHnoxDB8WENYSthnuEd4QvrrLZVftrhUOm3OC8yrCJqIiYinSMrI8ciHKMqo8ajHaMvpY9FKMdUxlzHIsO7Y69k2cc1xd3Hq8R/zZeF5CQEJ7IikxLPFSknBSfNJgsmxydvJYimZKUcpMqnnq8dQVriu3KQ1J25HWk85IT0kfzlDL+CZjNtMqsybzfZZ/1sVsoeyk7OHdGrsP7V7Iccz5IReXy8kdyJPP2583u8d2T30+kr8rf2Cv4t7CvfP7nPad20/ZH7//1wK9gvKCdwcCDvQWyhTuK5z7xumb1iL+Im7R1EGLg3Xf4r6N/XbkkOGhk4c+F0cU3ynRK6ks2SzllN75Tv+7qu94h6MOj5SZlJ0+QjiSdGTyqPXRc+VC5Tnlc8fcj3VVMCuKK94dDz1+u9Kosu4E5UTGiZkqt6qek0onj5zcrI6pnqixq2mvla49VLt+KuLU+Gmb0211MnUldR+/j/3+Yb1TfVeDSkPlGcKZzDMvGv0bh35g/dDcJNlU0vTpbNLZmXPe5wabTZubW6RbylrR1ozWpfMh50d/tP+xp027rb5dtL3kAlzIuPDyp7CfJjtcOwYusi62/az8c20nvbO4C+na3bXSHdM90xPUM3Zp66WBXovezl90fjl7Wf5yzRWRK2V9lL7CPt7VnKur/Sn9y9eir80NhA5MXw+8/mDQa3DkhuuNWzcdb14fsh26esvy1uXb5rcv3WHd6b5rcrdr2Hi481fjXztHTEa67pne6xk1G+0d2zLWN249fu2+/f2bD1we3J3YNjE26Tf5cCpkauZhxMPFRwmP3jzOfLwxve8J/knxU8Gnlc+knzX8pv5b+4zJzJVZ+9nh5z7Pp+c4c69+T/t9c77wBe1F5YLcQvOiweLlJcel0ZfbX86/Snm1sVz0h9Afta/VXv/8p82fwyuBK/NvuG94f5W+lXh79p3Ru4FVz9Vna4lrG+vF7yXen/vA+jD0MeDjwkbWJnGz6pP6p97Prp+f8BJ5vC8NAgAA8sEeAS4OzEA3phvbnslOTkjmMj25yVGxCZFa9ibGenr/VT8PO2wAAIDH4/GEEABBWsX/rKR/+//Yf22TxHwA01AA9MpXFx4DcHEUQGjsq1NdA2CMAvS1pkUZGnwpOKo9AP43Hu+tCgCxAuBTGY+3Uc/jfWoAwKYB+jP+BjGPnodrnb8wAAAACXBIWXMAAAsTAAALEwEAmpwYAAAE82lUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIxLTA4LTE4VDE3OjIzOjQwKzAyOjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMS0wOC0xOFQxNzozOTozMCswMjowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMS0wOC0xOFQxNzozOTozMCswMjowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6NjUxODVjNzQtZDljZi05NjRiLWJjYWEtOWIyNTAxMjg4ZWI0IiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOjY1MTg1Yzc0LWQ5Y2YtOTY0Yi1iY2FhLTliMjUwMTI4OGViNCIgeG1wTU06T3JpZ2luYWxEb2N1bWVudElEPSJ4bXAuZGlkOjY1MTg1Yzc0LWQ5Y2YtOTY0Yi1iY2FhLTliMjUwMTI4OGViNCI+IDx4bXBNTTpIaXN0b3J5PiA8cmRmOlNlcT4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImNyZWF0ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6NjUxODVjNzQtZDljZi05NjRiLWJjYWEtOWIyNTAxMjg4ZWI0IiBzdEV2dDp3aGVuPSIyMDIxLTA4LTE4VDE3OjIzOjQwKzAyOjAwIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+uriGxQAAALNJREFUSMft1L1qQkEQBtBTB58ghY3a5U1sLdNqm/ewtDQ2tmnjI6hYCIGAViE2gsFO/IEkyk3hFPbLLQK7sMywxXcYll1FUShzy0AGygXQwglHfODOdY3j/AedFKCLbzQj7D6AX7SxwzAFGOAtQtdo3AAwwSgF6GMRYVvUor9EneE1A6UCz3iPsA3q0Z+jTlMvuYcvVLBH9WaCB3ziJQV4xAFLrAKCeTy8E57yZ5eBfw78AQRHw9cjAXawAAAAAElFTkSuQmCC"
  base64_stop = b"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LTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIxLTA4LTE4VDE3OjIzOjQ4KzAyOjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMS0wOC0xOFQxNzozOTozMSswMjowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMS0wOC0xOFQxNzozOTozMSswMjowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MDg2NGNhZmYtNDU0MS0xNDQ0LWFlYzgtZTY4YjZkNzdhNjkyIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOjA4NjRjYWZmLTQ1NDEtMTQ0NC1hZWM4LWU2OGI2ZDc3YTY5MiIgeG1wTU06T3JpZ2luYWxEb2N1bWVudElEPSJ4bXAuZGlkOjA4NjRjYWZmLTQ1NDEtMTQ0NC1hZWM4LWU2OGI2ZDc3YTY5MiI+IDx4bXBNTTpIaXN0b3J5PiA8cmRmOlNlcT4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImNyZWF0ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6MDg2NGNhZmYtNDU0MS0xNDQ0LWFlYzgtZTY4YjZkNzdhNjkyIiBzdEV2dDp3aGVuPSIyMDIxLTA4LTE4VDE3OjIzOjQ4KzAyOjAwIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+VhlGygAAAIFJREFUSMft1KENwlAUhtGzBROwAuyBZoCm8yBQ2Co8c1DTBRC0afAIHqaqaTEvT5Dcm3z6/OpKKSmZAAIoC+CCB57oFxrQ5ABv3FChnlXhhDEHeOFg/TZoc4B+Wrt2+wCKAyOOP4BtLvDBGbtp7bwaQw7QoMMd7UIdrvHsAvhz4AvaCLcAbAXalAAAAABJRU5ErkJggg=="
  

if __name__ == "__main__":
  sg.theme("DarkGrey12")
  sg.SetGlobalIcon(Images.base64_app)
  GUI()