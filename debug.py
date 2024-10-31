import requests
from bs4 import BeautifulSoup


street_name = 'worms'
url = f"https://www.ebwo.de/de/abfallkalender/2024/?sTerm={street_name}"
response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, 'html.parser')

list_entries = soup.find_all('li', class_='listEntryObject-news')
street_options = {}
for entry in list_entries:
    if street_name.lower() in entry.get_text(strip=True).lower():
        street_url = entry.get('data-url')
        if street_url:
            full_street_url = f"https://www.ebwo.de{street_url}"
            street_options[entry.get_text(strip=True)] = full_street_url
allLinks = "\n".join([f"{StreetName}: '{Links}'" for StreetName, Links in street_options.items()])

print(allLinks)