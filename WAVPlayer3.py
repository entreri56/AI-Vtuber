from pydub import AudioSegment
import pyaudio
import wave
import os
import io
import time

def play_audio(file_path, virtual_device_name="CABLE Input"):
    audio = AudioSegment.from_file(file_path, format="mp3")

    p = pyaudio.PyAudio()
    virtual_device_index = None
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if virtual_device_name.lower() in dev_info["name"].lower():
            virtual_device_index = i
            print(f"Using virtual device: {dev_info['name']}")
            break

    if virtual_device_index is None:
        print(f"Virtual device '{virtual_device_name}' not found. Ensure it is set up correctly.")
        return

    audio_data = io.BytesIO()
    audio.export(audio_data, format="wav")
    audio_data.seek(0)
    wf = wave.open(audio_data, 'rb')
    
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=virtual_device_index)

    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()

def get_newest_mp3(folder_path, played_files):
    mp3_files = [f for f in os.listdir(folder_path) if f.endswith(".mp3") and f not in played_files]
    if not mp3_files:
        return None

    newest_file = max(mp3_files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
    return os.path.join(folder_path, newest_file)

def update_subtitle_file(mp3_file, text_folder, subtitle_file):
    txt_filename = os.path.splitext(os.path.basename(mp3_file))[0] + ".txt"
    txt_file_path = os.path.join(text_folder, txt_filename)

    if os.path.exists(txt_file_path):
        with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
            text_content = txt_file.read()

        with open(subtitle_file, 'w', encoding='utf-8') as subtitle_file:
            subtitle_file.write(text_content)
        print(f"Updated subtitles with content from {txt_filename}")
    else:
        print(f"No matching text file found for {txt_filename}.")

def main(folder_path, virtual_device_name="CABLE Input"):
    played_files = set()
    text_folder = r"E:\AIVtuber\Version1.8\RAGSourceText"
    subtitle_file = r"E:\AIVtuber\Version1.8\Subtitles\Subtitles.txt"

    while True:
        newest_file = get_newest_mp3(folder_path, played_files)

        if newest_file:
            print(f"New file detected: {newest_file}")
            
            # Update the subtitles file with the matching text content
            update_subtitle_file(newest_file, text_folder, subtitle_file)
            
            # Wait for 5 seconds before playing the audio
            time.sleep(4)
            
            print(f"Playing audio file: {newest_file}")
            play_audio(newest_file, virtual_device_name=virtual_device_name)

            played_files.add(os.path.basename(newest_file))
        else:
            print("No new files to process. Waiting for new files...")
            time.sleep(5)


# Specify the path to the folder containing MP3 files and the virtual device name
audio_folder_path = "E:\\AIVtuber\\Version1.8\\generated_audio"
main(audio_folder_path, virtual_device_name="CABLE Input")
