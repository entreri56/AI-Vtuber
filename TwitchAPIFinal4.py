import requests
import time
import socket
from datetime import datetime
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup the browser
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Uncomment if you want headless mode
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36")
options.add_argument('--disable-infobars')
options.add_argument('--start-maximized')
options.add_argument('--disable-extensions')
options.add_argument('--disable-blink-features=AutomationControlled')  # Prevent automation detection
options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Disable the automation switch
options.add_experimental_option("useAutomationExtension", False)  # Disable the automation extension
options.add_argument('--window-size=1920,1080')  # Set window size

# Use a specific user data directory
options.add_argument(r"user-data-dir=C:\Users\Admin\AppData\Local\Google\Chrome\User Data")  # Adjust this path to your Chrome user profile

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Navigate to the Twitch authorization URL
client_id = ""
redirect_uri = "http://localhost:3000"
url = f"https://id.twitch.tv/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=chat:read+channel:read:subscriptions"

driver.get(url)

# Wait for the user to log in
time.sleep(30)  # Adjust as necessary for login time

# Get the current URL to extract the authorization code
current_url = driver.current_url
if "code=" in current_url:
    auth_code = current_url.split("code=")[1].split("&")[0]  # Extract only the code part
    print(auth_code)  # Print only the authorization code
else:
    print("Authorization code not found in the current URL.")

# Close the browser
driver.quit()

# Twitch API credentials and settings
client_id = ""
client_secret = ""
redirect_uri = "http://localhost:3000"
code = auth_code  # Authorization code from the first step

# Directory to save chat messages
save_directory = r"E:\AIVtuber\Version1.8\ChatMessages"
stream_elements_directory = r"E:\AIVtuber\Version1.8\FollowSubMessg"
os.makedirs(save_directory, exist_ok=True)

# Twitch IRC settings
HOST = 'irc.chat.twitch.tv'
PORT = 6667
NICK = 'dexztii'  # Your Twitch username
CHANNEL = '#dexztii'  # Channel you want to join

# URL for requesting and refreshing tokens
token_url = "https://id.twitch.tv/oauth2/token"

def get_access_token():
    """Request the access token using the authorization code."""
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token'], token_data['refresh_token'], token_data['expires_in']
    else:
        print("Failed to get access token:", response.json())
        return None, None, None

def refresh_access_token(refresh_token):
    """Refresh the access token periodically."""
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token'], token_data['refresh_token'], token_data['expires_in']
    else:
        print("Failed to refresh access token:", response.json())
        return None, None, None

# Get the initial access token
access_token, refresh_token, expires_in = get_access_token()

# Connect to the Twitch IRC server
sock = socket.socket()
sock.connect((HOST, PORT))

def connect_to_twitch_chat(token):
    """Connect to Twitch chat with the provided token."""
    sock.send(f"PASS oauth:{token}\n".encode('utf-8'))
    sock.send(f"NICK {NICK}\n".encode('utf-8'))
    sock.send(f"JOIN {CHANNEL}\n".encode('utf-8'))
    print("Connected to Twitch chat")

# Connect to chat using the initial token
connect_to_twitch_chat(access_token)

def save_message_to_file(username, message):
    """Save a chat message to a timestamped file for each user."""
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"{username}_{timestamp}.txt"
    filepath = os.path.join(save_directory, filename)
    with open(filepath, 'a', encoding='utf-8') as file:
        file.write(f"{message}\n")

def save_stream_elements_message(message):
    """Save a message from StreamElements to a timestamped file."""
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"StreamElements_{timestamp}.txt"
    filepath = os.path.join(stream_elements_directory, filename)
    with open(filepath, 'a', encoding='utf-8') as file:
        file.write(f"{message}\n")

# Listen for messages and refresh the token in the background
last_refresh_time = time.time()

while True:
    try:
        # Listen for chat messages
        response = sock.recv(2048).decode('utf-8')
        if response:
            print("Received response:", response)  # Debug: Check received data

        # Respond to PING messages from Twitch
        if response.startswith('PING'):
            sock.send("PONG :tmi.twitch.tv\n".encode('utf-8'))
            print("Sent PONG response")  # Debug: PING-PONG

        # Extract username and message
        parts = response.split(':')
        if len(parts) > 2:
            username = parts[1].split('!')[0]  # Get the username
            message = ':'.join(parts[2:])  # Get the message
            
            # Skip messages from the channel owner or server messages
            if username.lower() == 'dexztii' or 'tmi.twitch.tv' in username:
                print("Skipping message from:", username)  # Debug: Skipping owner or server messages
                continue
            
            print(f"{username}: {message}")  # Debug: Show chat message
            
            # Save message to a timestamped file for each user
            save_message_to_file(username, message)

            # If the message is from StreamElements, save it in the specified directory
            if username.lower() == 'streamelements':
                save_stream_elements_message(message)

        # Refresh token if the refresh interval has passed (e.g., every 60 minutes)
        if time.time() - last_refresh_time > 3600:
            new_access_token, new_refresh_token, _ = refresh_access_token(refresh_token)
            if new_access_token:
                access_token, refresh_token = new_access_token, new_refresh_token
                last_refresh_time = time.time()
            else:
                print("Failed to refresh access token.")

    except socket.error as e:
        print("Socket error occurred:", e)
        break  # Exit on socket error
    except KeyboardInterrupt:
        print("Exiting.")
        break
