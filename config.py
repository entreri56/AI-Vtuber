import os
from dotenv import load_dotenv

# Load .env file from the project root
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# --- Project Root ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def _resolve_path(path: str) -> str:
    """Resolve a path: if absolute, use as-is; if relative, make relative to PROJECT_ROOT."""
    if not path:
        return path
    if os.path.isabs(path):
        return path
    return os.path.join(PROJECT_ROOT, path)

# --- ElevenLabs TTS ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

# --- Twitch ---
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
TWITCH_REDIRECT_URI = os.getenv("TWITCH_REDIRECT_URI", "http://localhost:3000")
TWITCH_NICKNAME = os.getenv("TWITCH_NICKNAME", "").lower()
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", f"#{TWITCH_NICKNAME}" if TWITCH_NICKNAME else "")

# --- Ollama ---
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "nemotron-mini")

# --- Directories ---
CHAT_MESSAGES_DIR = _resolve_path(os.getenv("CHAT_MESSAGES_DIR", "ChatMessages"))
RAG_SOURCE_DIR = _resolve_path(os.getenv("RAG_SOURCE_DIR", "RAGSourceText"))
FOLLOW_SUB_DIR = _resolve_path(os.getenv("FOLLOW_SUB_DIR", "FollowSubMessg"))
GENERATED_AUDIO_DIR = _resolve_path(os.getenv("GENERATED_AUDIO_DIR", "generated_audio"))
SUBTITLES_FILE = _resolve_path(os.getenv("SUBTITLES_FILE", "Subtitles/Subtitles.txt"))

# --- Audio ---
VIRTUAL_AUDIO_DEVICE = os.getenv("VIRTUAL_AUDIO_DEVICE", "CABLE Input")

# --- Chrome ---
CHROME_USER_DATA_DIR = os.getenv("CHROME_USER_DATA_DIR", "")

# --- RAG ---
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# --- TTS Settings ---
TTS_MODEL_ID = os.getenv("TTS_MODEL_ID", "eleven_multilingual_v2")
TTS_STABILITY = float(os.getenv("TTS_STABILITY", "0.5"))
TTS_SIMILARITY_BOOST = float(os.getenv("TTS_SIMILARITY_BOOST", "0.8"))
TTS_STYLE = float(os.getenv("TTS_STYLE", "0.0"))
TTS_USE_SPEAKER_BOOST = os.getenv("TTS_USE_SPEAKER_BOOST", "True").lower() == "true"

# --- Streamer name (used to skip own messages) ---
STREAMER_NAME = TWITCH_NICKNAME if TWITCH_NICKNAME else "streamer"

# Validate critical settings (warn, don't crash)
def validate_config():
    warnings = []
    if not ELEVENLABS_API_KEY:
        warnings.append("ELEVENLABS_API_KEY is not set. TTS will not work.")
    if not ELEVENLABS_VOICE_ID:
        warnings.append("ELEVENLABS_VOICE_ID is not set. TTS will not work.")
    if not TWITCH_CLIENT_ID:
        warnings.append("TWITCH_CLIENT_ID is not set. Twitch integration will not work.")
    if not TWITCH_CLIENT_SECRET:
        warnings.append("TWITCH_CLIENT_SECRET is not set. Twitch integration will not work.")
    if not TWITCH_NICKNAME:
        warnings.append("TWITCH_NICKNAME is not set. Twitch integration will not work.")
    return warnings