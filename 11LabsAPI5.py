# Import necessary libraries
import requests  # Used for making HTTP requests
import json  # Used for working with JSON data
import os
import glob
import time  # For adding delay
from datetime import datetime  # For working with date and time

# Define constants for the script
CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
XI_API_KEY = ""  # Your API key for authentication
VOICE_ID = ""  # ID of the voice model to use
SOURCE_FOLDER = r'E:\AIVtuber\Version1.8\RAGSourceText'  # Folder containing response text files
FOLLOW_SUB_FOLDER = r'E:\AIVtuber\Version1.8\FollowSubMessg'  # Folder containing follow/subscription text files
OUTPUT_FOLDER = r"E:\AIVtuber\Version1.8\generated_audio"  # Folder to save output audio files

# Find the most recent text file in the specified folder
def get_latest_text_file(folder_path):
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    if not txt_files:
        return None
    return max(txt_files, key=os.path.getmtime)

# Process the text file to generate audio
def generate_audio_from_text(file_path):
    # Read the content of the text file
    with open(file_path, 'r', encoding='utf-8') as file:
        text_to_speak = file.read().strip()

    # Construct the URL for the Text-to-Speech API request
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

    # Set up headers for the API request, including the API key for authentication
    headers = {
        "Accept": "application/json",
        "xi-api-key": XI_API_KEY
    }

    # Set up the data payload for the API request, including the text and voice settings
    data = {
        "text": text_to_speak,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }

    # Make the POST request to the TTS API with headers and data, enabling streaming response
    response = requests.post(tts_url, headers=headers, json=data, stream=True)

    # Check if the request was successful
    if response.ok:
        # Use the original filename minus the extension for the output audio file
        output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".mp3"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Open the output file in write-binary mode
        with open(output_path, "wb") as f:
            # Read the response in chunks and write to the file
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)
        # Inform the user of success
        print(f"Audio stream saved successfully as {output_filename}.")
    else:
        # Print the error message if the request was not successful
        print("Error in TTS generation:", response.text)

# Main loop to continuously check for new text files
# Initialize with files that exist when the script starts, to ignore them
processed_files = set(glob.glob(os.path.join(SOURCE_FOLDER, "*.txt")) +
                      glob.glob(os.path.join(FOLLOW_SUB_FOLDER, "*.txt")))

while True:
    # Find the most recent text file in the source folder
    latest_file = get_latest_text_file(SOURCE_FOLDER)
    latest_follow_sub_file = get_latest_text_file(FOLLOW_SUB_FOLDER)

    # Process the latest files if they exist and haven't been processed yet
    if latest_file and latest_file not in processed_files:
        print(f"New file detected in RAGSourceText: {latest_file}")
        generate_audio_from_text(latest_file)
        processed_files.add(latest_file)  # Mark file as processed

    if latest_follow_sub_file and latest_follow_sub_file not in processed_files:
        print(f"New file detected in FollowSubMessg: {latest_follow_sub_file}")
        generate_audio_from_text(latest_follow_sub_file)
        processed_files.add(latest_follow_sub_file)  # Mark file as processed

    # Wait for a few seconds before checking again
    time.sleep(5)
