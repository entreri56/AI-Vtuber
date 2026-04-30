@echo off

:: Run the first Python program
start python TwitchAPIFinal4.py

:: Wait for 30 seconds
timeout /t 30 /nobreak

:: Run the next three Python programs
start python Model6.py
start python 11LabsAPI5.py
start python WAVPlayer2.py

echo All programs have been executed.
pause
