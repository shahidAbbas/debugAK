from flask import Flask, request, jsonify, session
import threading
import logging
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = '4c3d2e1f0a9b8c7d6e5f4g3h2i1j0k9l'  # Replace with your generated secret key

# Shared list to store messages
# Shared list to store messages
# Shared list to store messages
messages = []
lock = threading.Lock()

# Configure logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Constants
TENANT_NAME = "worms"
TOKEN_URL = f"https://idp.mycityapp.cloud.test.kobil.com/auth/realms/{TENANT_NAME}/protocol/openid-connect/token/"
CLIENT_ID = "bec2a19b-8b1d-4665-b9bd-5cf5f86dbcda"
CLIENT_SECRET = "2e5f8551-82f2-460d-98e2-1b90deed3b03"
USERNAME = "integration"
PASSWORD = "MhNBBhA7hvZNGuJZ"

def get_access_token():
    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'client_id': CLIENT_ID,
        'grant_type': 'password',
        'client_secret': CLIENT_SECRET
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }

    response = requests.post(TOKEN_URL, data=payload, headers=headers)
    response_data = response.json()
    return response_data.get("access_token")

def send_message(to_user_id, message_text):
    access_token = get_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f"Bearer {access_token}"
    }
    payload = {
        "serviceUuid": CLIENT_ID,
        "messageType": "processChatMessage",
        "version": 3,
        "messageContent": {
            "messageText": message_text
        }
    }
    url = f"https://idp.mycityapp.cloud.test.kobil.com/auth/realms/{TENANT_NAME}/mpower/v1/users/{to_user_id}/message/"
    response = requests.post(url, json=payload, headers=headers)

def send_choice_message(to_user_id, message_text, choices):
    access_token = get_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f"Bearer {access_token}"
    }
    payload = {
        "serviceUuid": CLIENT_ID,
        "messageType": "choiceRequest",
        "version": 3,
        "messageContent": {
            "messageText": message_text,
            "choices": [{"text": choice} for choice in choices]
        }
    }
    url = f"https://idp.mycityapp.cloud.test.kobil.com/auth/realms/{TENANT_NAME}/mpower/v1/users/{to_user_id}/message/"
    response = requests.post(url, json=payload, headers=headers)

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
    cleaned_name = re.sub(r'\d+', '', street_name).strip()
    return cleaned_name

@app.route('/')
def index():
    return jsonify({"message": "Willkommen beim Chat-Service"}), 200

@app.route('/chat_callback', methods=['POST'])
def chat_callback():
    json_data = request.get_json()

    message_content = json_data.get("message", {}).get("content", {}).get("messageContent", {}).get("messageText", "")
    message_type = json_data.get("message", {}).get("content", {}).get("messageType", "")
    user_id = json_data.get("message", {}).get("from", {}).get("userId", "")
    conversation_id = json_data.get("message", {}).get("conversationId", "")

    if message_type == "init":
        # Ask for the user's street name
        send_message(user_id, "🛤️ Bitte geben Sie Ihren Straßennamen ein.")
        send_message(user_id, "Siiiii")
    elif message_type == "processChatMessage" and message_content:
        # Process the user's response (assume it's the street name)
        street_name = clean_street_name(message_content.strip())

        street_options = get_street_web_address(street_name)

        if len(street_options) == 1:
            street_url = list(street_options.values())[0]
            abholtermine = get_abholtermine(street_url)
            for category, dates in abholtermine.items():
                response_message = f"{category}:\n"
                response_message += "\n".join(dates) + "\n"
                send_message(user_id, response_message)
        elif len(street_options) > 1:
            session[f'{conversation_id}_street_options'] = street_options
            send_message(user_id, "Bitte wählen Sie eine der folgenden Straßenoptionen:")
            send_choice_message(user_id, "Bitte wählen Sie Ihre Straße:", list(street_options.keys()))
        else:
            send_message(user_id, "❌ Straße nicht gefunden. Bitte versuchen Sie es erneut.")
    elif message_type == "choiceResponse" and message_content:
        street_choice = message_content.strip()
        send_message(user_id, f"Sie haben gewählt: {street_choice}")

        street_options = session.pop(f'{conversation_id}_street_options', {})

        street_url = street_options.get(street_choice)
        if street_url:
            abholtermine = get_abholtermine(street_url)
            for category, dates in abholtermine.items():
                response_message = f"{category}:\n"
                response_message += "\n".join(dates) + "\n"
                send_message(user_id, response_message)
        else:
            send_message(user_id, "❌ Auswahl ungültig. Bitte versuchen Sie es erneut.")
    else:
        send_message(user_id, "Unbekannte Anfrage. Bitte versuchen Sie es erneut.")

    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    app.run(debug=True)