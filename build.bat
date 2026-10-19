@echo off
rem Build a single-file Windows exe with the carousel icon
python -m pip install pywebview pyinstaller
python -m PyInstaller --onefile --noconsole --name AMYCarousel --icon AMYCarousel.ico --add-data "AMYCarousel.htm;." amycarousel_app.py
