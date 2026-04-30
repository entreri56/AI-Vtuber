@echo off

:: Run ollama serve in a new window
start "" ollama serve

:: Run the Python programs in new windows
start "" python Model6.py
start "" python 11LabsAPI5.py
start "" python WAVPlayer3.py

echo All programs have been executed.
pause
