@echo off

call %~dp0Translate_bot/venv/Scripts/activate

cd %~dp0Translate_bot

set TOKEN=5599960657:AAE95FnQ6WsLU0iWFfOBGyqqbwX57oqwLA4

python bot_telegram.py
python tasks.py

pause