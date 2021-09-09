import bs4, json, re
import urllib.request as request


entries = { }


def load(base_url: str):
  global entries

  with request.urlopen(base_url) as response: 
    html_data = bs4.BeautifulSoup(response.read(), "html.parser")
  list = html_data.select("div.o-layout-list script")
  entries = [json.loads(item.contents[0]) for item in list]
  pass


def extract_data_by_item(item: dict) -> tuple[str, str]:
  """Extract title and datetime from an <Entries> item.

  Args:
      item (dict): <Entries> item.

  Returns:
      tuple[str, str]: Tuple including title, datetime.
  """
  groups = re.findall("([\\s\\S]+) ([0-9]{2}/[0-9]{2}/{0,1}[0-9]{0,}) ([\\s\\S]+)", item['diffusion']['title'])
  title, date, time = groups[0]
  return title, f"{date} {time}"


def extract_data_by_number(entry_number: int) -> tuple[str, str]:
  """Extract title and datetime from an <Entries> index.

  Args:
      entry_number (int): <Entries> index.

  Returns:
      tuple[str, str]: Tuple including title, datetime.
  """
  groups = re.findall("([\\s\\S]+) ([0-9]{2}/[0-9]{2}/{0,1}[0-9]{0,}) ([\\s\\S]+)", entries[entry_number]['diffusion']['title'])
  title, date, time = groups[0]
  return title, f"{date} {time}"


def entry_number_by_title(title: str) -> int:
  """Searches for an entry number from a title.

  Args:
      title (str): EXACT title of the show.

  Returns:
      int: <Entries> index.
  """
  return [i for i in range(len(entries)) if entries[i]['diffusion']['title'] == title][0]


def extract_url(entry_number: int) -> str:
  """Extract URL from an entry index.

  Args:
      entry_number (int): Entry index.

  Returns:
      str: the URL of the show.
  """
  entry = entries[entry_number] 
  return entry['sources'][0]['url']
