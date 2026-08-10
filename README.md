# AI VTuber

An open-source AI VTuber that connects to Twitch chat, generates AI responses using a local LLM (Ollama) with RAG (Retrieval Augmented Generation), speaks them via ElevenLabs TTS, and routes audio through a virtual cable so your VTuber model lip-syncs in real time.

## Full Pipeline

```
Twitch Chat → twitch_chat.py → ChatMessages/
                                    ↓
                              rag_model.py (FAISS + Ollama)
                                    ↓
                              RAGSourceText/ (response .txt)
                                    ↓
                              tts_generator.py (ElevenLabs)
                                    ↓
                              generated_audio/ (.mp3)
                                    ↓
                              audio_player.py
                                    ↓
                           VB-Cable "CABLE Input" (virtual speaker)
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
        StreamLabs/OBS                          VTuber Studio
        (Mic/Aux = CABLE Output)               or VSeeFace
                                                    ↓
                                            VTuber model lip-syncs
                                            as the AI speaks
```

## Prerequisites

### Software You Need

| Software | Purpose | Link |
|---|---|---|
| **Python 3.8+** | Runs the AI scripts | [python.org](https://python.org) |
| **Ollama** | Local LLM for AI responses | [ollama.com](https://ollama.com) |
| **ElevenLabs** | Text-to-speech voice generation | [elevenlabs.io](https://elevenlabs.io) |
| **VB-Cable** | Virtual audio cable (routes TTS audio) | [vb-audio.com/Cable](https://vb-audio.com/Cable/) |
| **StreamLabs** or **OBS Studio** | Streaming/recording software | [streamlabs.com](https://streamlabs.com) |
| **VTuber Studio** or **VSeeFace** | VTuber avatar with lip-sync | [VTuber Studio](https://store.steampowered.com/app/2313820/) / [VSeeFace](https://www.vseeface.icu/) |
| **Twitch Developer App** | API access for chat bot | [dev.twitch.tv/console](https://dev.twitch.tv/console/apps) |

### How the Audio Routing Works

This is the most important part to understand:

1. **`audio_player.py`** plays the generated MP3 through **VB-Cable's "CABLE Input"** (a virtual speaker)
2. VB-Cable loops that audio internally to **"CABLE Output"** (a virtual microphone)
3. **StreamLabs/OBS** uses "CABLE Output" as its **Mic/Aux audio source** → your stream hears the AI
4. **VTuber Studio / VSeeFace** also listens to "CABLE Output" as its **microphone input** → your avatar's mouth moves in sync with the AI's voice

> **Key point:** The AI's voice goes to BOTH your stream audio AND your VTuber's lip-sync — all through one virtual cable.

## Quick Start

### 1. Clone & Install Dependencies

```bash
git clone <your-repo-url>
cd AI-Vtuber-main
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
ELEVENLABS_API_KEY=sk_xxxx
ELEVENLABS_VOICE_ID=xxxx
TWITCH_CLIENT_ID=xxxx
TWITCH_CLIENT_SECRET=xxxx
TWITCH_NICKNAME=your_twitch_username
TWITCH_CHANNEL=#your_twitch_username
VIRTUAL_AUDIO_DEVICE=CABLE Input
```

### 3. Pull an Ollama Model

```bash
ollama pull nemotron-mini
```

### 4. Set Up Your AI Personality

Edit `RAGSourceText/ai_personality.txt` with your VTuber's personality, rules, and example interactions.

### 5. Configure Your Streaming Software

**StreamLabs / OBS:**
- Go to **Settings → Audio**
- Set **Mic/Auxiliary Device** to **"CABLE Output"** (VB-Audio Virtual Cable)
- This makes the AI's voice part of your stream audio

**VTuber Studio / VSeeFace:**
- Go to microphone settings
- Set the **microphone input** to **"CABLE Output"** (VB-Audio Virtual Cable)
- Your avatar will now lip-sync whenever the AI speaks

### 6. Run

**For full Twitch streaming:**
```bash
start_stream.bat
```

**For local testing (no Twitch):**
```bash
run_test.bat
```

## File Structure

| File | Purpose |
|---|---|
| `config.py` | Central configuration loaded from `.env` |
| `twitch_chat.py` | Connects to Twitch IRC, captures chat messages |
| `rag_model.py` | AI brain: FAISS vector search + Ollama LLM |
| `tts_generator.py` | Converts AI responses to speech (ElevenLabs) |
| `audio_player.py` | Plays TTS audio through virtual cable + subtitles |
| `start_stream.bat` | Launch all modules for streaming |
| `run_test.bat` | Launch modules for offline testing (no Twitch) |
| `RAGSourceText/` | Knowledge base for the AI's personality |

## Configuration Reference

All settings in `.env`:

| Variable | Description | Default |
|---|---|---|
| `ELEVENLABS_API_KEY` | Your ElevenLabs API key | *(required)* |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice model ID | *(required)* |
| `TWITCH_CLIENT_ID` | Twitch app client ID | *(required)* |
| `TWITCH_CLIENT_SECRET` | Twitch app client secret | *(required)* |
| `TWITCH_NICKNAME` | Your Twitch username (lowercase) | *(required)* |
| `TWITCH_CHANNEL` | Channel to join (e.g. `#username`) | `#your_nickname` |
| `OLLAMA_API_URL` | Ollama API endpoint | `http://127.0.0.1:11434/api/generate` |
| `OLLAMA_MODEL` | Ollama model name | `nemotron-mini` |
| `VIRTUAL_AUDIO_DEVICE` | Virtual audio device name | `CABLE Input` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `RAG_TOP_K` | Number of knowledge chunks retrieved | `5` |

## Troubleshooting

**"Virtual device not found" error:**
- Make sure [VB-Cable](https://vb-audio.com/Cable/) is installed
- After install, restart your PC
- Verify "CABLE Input" and "CABLE Output" appear in Windows Sound settings

**VTuber not lip-syncing:**
- Check VTuber Studio / VSeeFace microphone is set to "CABLE Output"
- Make sure the audio is actually playing (check the audio_player.py console window)

**No audio in stream:**
- In StreamLabs/OBS, check Settings → Audio → Mic/Aux is "CABLE Output"
- Make sure the audio source isn't muted in your mixer
