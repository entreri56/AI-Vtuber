@echo off
echo ============================================
echo   AI VTuber - Run Test (no Twitch)
echo ============================================

:: Start Ollama (if not already running)
start "" ollama serve

:: Start AI Model, TTS, and Audio Player
start "AI Model" python rag_model.py
start "TTS Generator" python tts_generator.py
start "Audio Player" python audio_player.py

echo All programs started. Check each window for status.
pause