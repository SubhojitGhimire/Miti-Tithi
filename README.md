# MitiTithi - Nepali Calendar Desktop Widget

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

A sophisticated, feature-rich desktop widget that displays the Nepali (Bikram Sambat) date, Tithi, and upcoming events directly on your Windows desktop. Built with Python and PySide6, this application is designed to be both beautiful and functional, featuring a polished UI, smooth animations, and an offline-first data architecture.

---

## Screenshots

<img width="5800" height="2250" alt="Image-Preview" src="https://github.com/user-attachments/assets/3214de63-c662-49e5-a4b1-71f1b0e91034" />

## Features

1. Multiple Views:
   - Widget View: A compact, elegant rectangle showing the current Nepali date, weekday, Tithi, Gregorian date, and a live clock for the Asia/Kathmandu timezone.
   - Minimized View: A tiny square widget displaying just the Nepali month, day, and time.
   - Calendar View: A full-featured calendar application view.

2. Interactive Calendar:
   - Displays a full Nepali month, with corresponding Gregorian dates.
   - Highlights the current day, Saturdays, and all national holidays.
   - Click any day to see a detailed popup with its full date info, Tithi, and events.
   - Click the month/year header to jump to any date in the past or future.
   - Lists all festivals and events for the selected month.

3. Customization & Themes:
   - Switch between a polished Dark Mode and a clean Light Mode.

4. Offline-First Architecture:
   - The application scrapes and caches over 100 years of calendar data locally.
   - It is incredibly fast and works perfectly without an internet connection after the initial sync.

5. Smart Background Sync:
   - All data fetching happens on a background thread, so the UI never freezes.
   - Automatically syncs new data on startup and on-demand.

## Requirements

Python3.10 with the following dependencies installed.
```
requests==2.32.4
beautifulsoup4==4.13.4
PySide6==6.9.1
pywin32==311
pytz==2025.2
```

## Setup and Usage

SETUP:  
1. Ensure you have Python installed on your system. (Recommended <a href="https://www.python.org/downloads/release/python-31010/">Python 3.10.10</a>)
2. Download this Repository. Unzip it. (Ensure folder name is Miti-Tithi-main , if not, rename the folder to Miti-Tithi-main)
3. Open Folder and Run setup.exe.bat file as administrator. (Right-click -> Show More Options -> Run As Administrator)  
All Set! Restart your PC and the widget will appear automatically!

To run the application on-demand, simply execute the main.py script from the root directory: ```python main.py```

To run the application automatically:
- In the calendar view settings, you can enable "run on startup" to run the calendar automatically. (This may not work on some systems, depending on the Windows Restrictions Set)
- OR, Edit the ```mitiTithi.exe.vbs``` file in notepad, choose the correct path, then copy the vbs file to startup folder as such,
  ```
      Win + R to open "Run" systems app. OR search for "Run" on Start Menu Search Functionality.
      Type "shell:startup" and hit enter to open the startup folder. Generally located at C:\Users\SubhojitGhimire\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
  ```

## Acknowledgement
1. The Calendar Data was scraped off of <a href="https://www.ashesh.com.np/nepali-calendar/">Ashesh's Blog</a>

<h1></h1>

**This README.md file has been improved for overall readability (grammar, sentence structure, and organization) using AI tools.*
