import bs4
import json
import re
import urllib.request as request

class Scrapper():
  def __init__(self, base_url: str):
    with request.urlopen(base_url) as response: 
      html_data = bs4.BeautifulSoup(response.read(), "html.parser")
    list = html_data.select("div.o-layout-list script")
    self._entries = [json.loads(item.contents[0]) for item in list]
  
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
