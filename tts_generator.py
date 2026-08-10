"""TTS Generator"""
import requests
import os
import glob
import time

from config import (
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
    RAG_SOURCE_DIR, FOLLOW_SUB_DIR, GENERATED_AUDIO_DIR,
    TTS_MODEL_ID, TTS_STABILITY, TTS_SIMILARITY_BOOST,
    TTS_STYLE, TTS_USE_SPEAKER_BOOST,
    validate_config,
)

CHUNK_SIZE = 1024

# --- Validate config ---
warnings = validate_config()
for w in warnings:
    if "ElevenLabs" in w or "TTS" in w:
        print(f"[WARNING] {w}")

# --- Ensure output folder exists ---
os.makedirs(GENERATED_AUDIO_DIR, exist_ok=True)



def get_latest_text_file(folder_path):
    """Find the most recent text file in the specified folder."""
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    if not txt_files:
        return None
    return max(txt_files, key=os.path.getmtime)



def generate_audio_from_text(file_path):
    """Send text to ElevenLabs TTS API and save the resulting MP3."""
    with open(file_path, 'r', encoding='utf-8') as file:
        text_to_speak = file.read().strip()

    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"

    headers = {
        "Accept": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }

    data = {
        "text": text_to_speak,
        "model_id": TTS_MODEL_ID,
        "voice_settings": {
            "stability": TTS_STABILITY,
            "similarity_boost": TTS_SIMILARITY_BOOST,
            "style": TTS_STYLE,
            "use_speaker_boost": TTS_USE_SPEAKER_BOOST,
        }
    }

    response = requests.post(tts_url, headers=headers, json=data, stream=True)

    if response.ok:
        output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".mp3"
        output_path = os.path.join(GENERATED_AUDIO_DIR, output_filename)

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)

        print(f"[INFO] Audio saved: {output_filename}")
    else:
        print(f"[ERROR] TTS generation failed: {response.text}")



# --- Main loop ---
if __name__ == "__main__":
    processed_files = set(
        glob.glob(os.path.join(RAG_SOURCE_DIR, "*.txt")) +
        glob.glob(os.path.join(FOLLOW_SUB_DIR, "*.txt"))
    )

    while True:
        latest_file = get_latest_text_file(RAG_SOURCE_DIR)
        latest_follow_sub_file = get_latest_text_file(FOLLOW_SUB_DIR)

        if latest_file and latest_file not in processed_files:
            print(f"[INFO] New file detected: {latest_file}")
            generate_audio_from_text(latest_file)
            processed_files.add(latest_file)

        if latest_follow_sub_file and latest_follow_sub_file not in processed_files:
            print(f"[INFO] New follow/sub file detected: {latest_follow_sub_file}")
            generate_audio_from_text(latest_follow_sub_file)
            processed_files.add(latest_follow_sub_file)

        time.sleep(5)