@echo off
echo ============================================
echo   AI VTuber - Start Stream
echo ============================================

:: 1. Start Twitch Chat Bot
start "Twitch Chat" python twitch_chat.py

:: Wait for Twitch auth
echo Waiting 30 seconds for Twitch OAuth login...
timeout /t 30 /nobreak

:: 2. Start AI Model, TTS, and Audio Player
start "AI Model" python rag_model.py
start "TTS Generator" python tts_generator.py
start "Audio Player" python audio_player.py

echo All programs started. Check each window for status.
pause