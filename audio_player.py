"""
Audio Player
Plays generated MP3 files through a virtual audio device (e.g. VB-Cable),
and updates a subtitles file for OBS overlay.
"""
from pydub import AudioSegment
import pyaudio
import wave
import os
import io
import time

from config import (
    GENERATED_AUDIO_DIR, RAG_SOURCE_DIR, SUBTITLES_FILE,
    VIRTUAL_AUDIO_DEVICE,
)



def play_audio(file_path, virtual_device_name=VIRTUAL_AUDIO_DEVICE):
    """Play an MP3 file through the specified virtual audio device."""
    audio = AudioSegment.from_file(file_path, format="mp3")

    p = pyaudio.PyAudio()
    virtual_device_index = None
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if virtual_device_name.lower() in dev_info["name"].lower():
            virtual_device_index = i
            print(f"[INFO] Using virtual device: {dev_info['name']}")
            break

    if virtual_device_index is None:
        print(f"[WARNING] Virtual device '{virtual_device_name}' not found.")
        print("          Make sure VB-Cable or similar is installed.")
        return

    audio_data = io.BytesIO()
    audio.export(audio_data, format="wav")
    audio_data.seek(0)
    wf = wave.open(audio_data, 'rb')

    stream = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True,
        output_device_index=virtual_device_index,
    )

    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()



def get_newest_mp3(folder_path, played_files):
    """Find the newest unplayed MP3 file."""
    mp3_files = [
        f for f in os.listdir(folder_path)
        if f.endswith(".mp3") and f not in played_files
    ]
    if not mp3_files:
        return None
    newest_file = max(mp3_files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
    return os.path.join(folder_path, newest_file)



def update_subtitle_file(mp3_file, text_folder, subtitle_file):
    """Match MP3 to its text source and update the subtitles file."""
    txt_filename = os.path.splitext(os.path.basename(mp3_file))[0] + ".txt"
    txt_file_path = os.path.join(text_folder, txt_filename)

    if os.path.exists(txt_file_path):
        with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
            text_content = txt_file.read()

        # Ensure subtitle directory exists
        os.makedirs(os.path.dirname(subtitle_file), exist_ok=True)

        with open(subtitle_file, 'w', encoding='utf-8') as sub_file:
            sub_file.write(text_content)
        print(f"[INFO] Subtitles updated from: {txt_filename}")
    else:
        print(f"[INFO] No matching text file for: {txt_filename}")



# --- Main ---
if __name__ == "__main__":
    played_files = set()

    while True:
        newest_file = get_newest_mp3(GENERATED_AUDIO_DIR, played_files)

        if newest_file:
            print(f"[INFO] New audio detected: {newest_file}")

            # Update subtitles
            update_subtitle_file(newest_file, RAG_SOURCE_DIR, SUBTITLES_FILE)

            # Small delay before playing
            time.sleep(4)

            print(f"[INFO] Playing: {newest_file}")
            play_audio(newest_file)

            played_files.add(os.path.basename(newest_file))
        else:
            print("No new audio files. Waiting...")
            time.sleep(5)