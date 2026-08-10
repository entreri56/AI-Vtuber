"""
Twitch Chat Bot
Connects to a Twitch channel's chat via IRC, saves messages,
and handles follow/subscription notifications from StreamElements.
"""
import requests
import time
import socket
from datetime import datetime
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import (
    TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_REDIRECT_URI,
    TWITCH_NICKNAME, TWITCH_CHANNEL, STREAMER_NAME,
    CHAT_MESSAGES_DIR, FOLLOW_SUB_DIR, CHROME_USER_DATA_DIR,
    validate_config,
)

# --- Validate config on startup ---
warnings = validate_config()
for w in warnings:
    if "Twitch" in w:
        print(f"[WARNING] {w}")

# --- Setup the browser for OAuth ---
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36")

if CHROME_USER_DATA_DIR:
    options.add_argument(f"user-data-dir={CHROME_USER_DATA_DIR}")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# --- OAuth Authorization ---
url = (
    f"https://id.twitch.tv/oauth2/authorize"
    f"?client_id={TWITCH_CLIENT_ID}"
    f"&redirect_uri={TWITCH_REDIRECT_URI}"
    f"&response_type=code"
    f"&scope=chat:read+channel:read:subscriptions"
)

driver.get(url)
print("[INFO] Waiting 30 seconds for you to log in to Twitch...")
time.sleep(30)

current_url = driver.current_url
if "code=" in current_url:
    auth_code = current_url.split("code=")[1].split("&")[0]
    print(f"[INFO] Authorization code obtained.")
else:
    print("[ERROR] Authorization code not found in the current URL.")
    driver.quit()
    exit(1)

driver.quit()

# --- Twitch API & IRC settings ---
HOST = 'irc.chat.twitch.tv'
PORT = 6667
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

os.makedirs(CHAT_MESSAGES_DIR, exist_ok=True)
os.makedirs(FOLLOW_SUB_DIR, exist_ok=True)


def get_access_token():
    """Request the access token using the authorization code."""
    data = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': TWITCH_REDIRECT_URI,
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token'], token_data['refresh_token'], token_data['expires_in']
    else:
        print("[ERROR] Failed to get access token:", response.json())
        return None, None, None


def refresh_access_token(refresh_token):
    """Refresh the access token periodically."""
    data = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token'], token_data['refresh_token'], token_data['expires_in']
    else:
        print("[ERROR] Failed to refresh access token:", response.json())
        return None, None, None


def connect_to_twitch_chat(sock, token):
    """Connect to Twitch chat with the provided token."""
    sock.send(f"PASS oauth:{token}\n".encode('utf-8'))
    sock.send(f"NICK {TWITCH_NICKNAME}\n".encode('utf-8'))
    sock.send(f"JOIN {TWITCH_CHANNEL}\n".encode('utf-8'))
    print(f"[INFO] Connected to Twitch chat as {TWITCH_NICKNAME} in {TWITCH_CHANNEL}")


def save_message_to_file(username, message):
    """Save a chat message to a timestamped file for each user."""
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"{username}_{timestamp}.txt"
    filepath = os.path.join(CHAT_MESSAGES_DIR, filename)
    with open(filepath, 'a', encoding='utf-8') as file:
        file.write(f"{message}\n")


def save_stream_elements_message(message):
    """Save a message from StreamElements to a timestamped file."""
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"StreamElements_{timestamp}.txt"
    filepath = os.path.join(FOLLOW_SUB_DIR, filename)
    with open(filepath, 'a', encoding='utf-8') as file:
        file.write(f"{message}\n")


# --- Main ---
if __name__ == "__main__":
    access_token, refresh_token, expires_in = get_access_token()
    if access_token is None:
        print("[ERROR] Could not obtain access token. Exiting.")
        exit(1)

    sock = socket.socket()
    sock.connect((HOST, PORT))
    connect_to_twitch_chat(sock, access_token)

    last_refresh_time = time.time()

    while True:
        try:
            response = sock.recv(2048).decode('utf-8')
            if response:
                print("Received response:", response)

            # PING-PONG
            if response.startswith('PING'):
                sock.send("PONG :tmi.twitch.tv\n".encode('utf-8'))
                print("Sent PONG response")

            # Extract username and message
            parts = response.split(':')
            if len(parts) > 2:
                username = parts[1].split('!')[0]
                message = ':'.join(parts[2:])

                # Skip own messages and server messages
                if username.lower() == STREAMER_NAME or 'tmi.twitch.tv' in username:
                    continue

                print(f"{username}: {message}")
                save_message_to_file(username, message)

                if username.lower() == 'streamelements':
                    save_stream_elements_message(message)

            # Refresh token every 60 minutes
            if time.time() - last_refresh_time > 3600:
                new_access_token, new_refresh_token, _ = refresh_access_token(refresh_token)
                if new_access_token:
                    access_token, refresh_token = new_access_token, new_refresh_token
                    last_refresh_time = time.time()
                    print("[INFO] Access token refreshed.")
                else:
                    print("[ERROR] Failed to refresh access token.")

        except socket.error as e:
            print("Socket error occurred:", e)
            break
        except KeyboardInterrupt:
            print("Exiting.")
            break