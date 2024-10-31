from flask import Flask, request, jsonify, session
import threading
import logging
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def get_abholtermine(street_url):
    response = requests.get(street_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    abholtermine = {
        "Gelbe Tonne 🟨": [],
        "Altpapier 📄": [],
        "Restabfall (bis 240 Liter) 🗑️": [],
        "Bio-Abfälle 🌱": []
    }

    divs = soup.find_all('div', style=lambda value: value and 'margin-top:25px;' in value)
    category_order = ["Gelbe Tonne 🟨", "Altpapier 📄", "Restabfall (bis 240 Liter) 🗑️", "Bio-Abfälle 🌱"]

    for idx, div in enumerate(divs):
        current_category = category_order[idx % len(category_order)]
        div_content = div.get_text(separator="\n").split("\n")
        dates = [d.strip() for d in div_content if d.strip() and d.strip().isdigit() == False and d.strip().count('.') == 2]
        
        abholtermine[current_category].extend(dates)

    for category in abholtermine:
        abholtermine[category] = sorted(abholtermine[category], key=lambda date: datetime.strptime(date, "%d.%m.%Y"))

    return abholtermine

def get_street_web_address(street_name):
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
    return street_options

def get_abholtermine(street_url):
    response = requests.get(street_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    abholtermine = {
        "Gelbe Tonne 🟨": [],
        "Altpapier 📄": [],
        "Restabfall (bis 240 Liter) 🗑️": [],
        "Bio-Abfälle 🌱": []
    }

    divs = soup.find_all('div', style=lambda value: value and 'margin-top:25px;' in value)
    category_order = ["Gelbe Tonne 🟨", "Altpapier 📄", "Restabfall (bis 240 Liter) 🗑️", "Bio-Abfälle 🌱"]

    for idx, div in enumerate(divs):
        current_category = category_order[idx % len(category_order)]
        div_content = div.get_text(separator="\n").split("\n")
        dates = [d.strip() for d in div_content if d.strip() and d.strip().isdigit() == False and d.strip().count('.') == 2]
        
        abholtermine[current_category].extend(dates)

    for category in abholtermine:
        abholtermine[category] = sorted(abholtermine[category], key=lambda date: datetime.strptime(date, "%d.%m.%Y"))

    return abholtermine

def clean_street_name(street_name):
    # Remove numbers and extra spaces from the street name
    #cleaned_name = re.sub(r'\d+', '', street_name).strip()
    cleaned_name = re.sub(r'[^a-zA-ZäöüßÄÖÜ\s]', '', street_name).strip()
    return cleaned_name

street_choice = 'Alzeyer Straße 156-184'
         
streetChoiceURLs = get_street_web_address(clean_street_name(street_choice))
allLinks = "\n".join([f"{StreetName}: '{Links}'" for StreetName, Links in streetChoiceURLs.items()])

street_url = streetChoiceURLs.get(street_choice)
print(street_url)
if street_url:
            abholtermine = get_abholtermine(street_url)
            for category, dates in abholtermine.items():
                response_message = f"{category}:\n"
                response_message += "\n".join(dates)
                print(response_message)