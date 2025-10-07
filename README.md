# MitiTithi - Nepali Calendar Desktop Widget

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/MitiTithi-v2.0.0-orange)

A sophisticated, feature-rich desktop widget that displays the Nepali (Bikram Sambat) date, Tithi, and upcoming events directly on your Windows desktop. Built with Python and PySide6, this application is designed to be both beautiful and functional, featuring a polished UI, smooth animations, and an offline-first data architecture.

---

## Screenshots

<img width="5757" height="2300" alt="Image-Preview" src="https://github.com/user-attachments/assets/48341a1d-59fe-4ec5-821b-b1f12941b658" />

## Features

1. Multiple Views:
   - Widget View: A compact, elegant rectangle showing the current Nepali date, weekday, Tithi, Gregorian date, and a live clock for the Asia/Kathmandu timezone.
   - Minimized View: A tiny square widget displaying just the Nepali month, day, and time.
   - Calendar View: A full-featured calendar application with month navigation and an event list.
   - Event Pop-up: An independent, draggable pop-up that displays only the current day's events, accessible from the context menu.

2. Interactive Calendar:
   - Displays a full Nepali month, with corresponding Gregorian dates.
   - Highlights the current day, Saturdays, and all national holidays.
   - Click any day to see a detailed popup with its full date info, Tithi, and events.
   - Click the month/year header to jump to any date in the past or future.
   - Quick Navigation: Instantly jump back to today's date from anywhere in the calendar with a "Show Today" button.
   - Events Panel: Lists all festivals and events for the selected month.
   - Collapsible Interface: Hide the events panel for a more compact and focused calendar view.

3. Advanced Customization & Control:
   - Dual Themes: Switch between a polished Dark Mode and a clean Light Mode.
   - Flexible Placement: Let the widget float freely or lock it to any corner of your screen (e.g., top-right, bottom-left).
   - Resizable Windows: Enable resizing to make any view (widget, minimized, or calendar) perfectly fit your desktop space. The app remembers your preferred sizes.

4. Built-in Productivity Tools:
   - Date Converter: Quickly look up the corresponding Gregorian (AD) date for any Nepali (BS) date, and vice-versa.
   - Age Calculator: Instantly calculate an age in years, months, and days from a birth date.
   - Date Difference: Find the exact duration between any two dates.

5. Personal Reminder System:
   - Set & Forget: Create reminders for important events, appointments, or deadlines with specific dates and times.
   - Persistent Storage: Your reminders are saved locally and are reloaded every time you start your computer.
   - Alert System: Receive a distinct pop-up notification with a system beep when a reminder is due, ensuring you never miss a thing.

6. Smart Data Management:
   - Offline-First Architecture: Scrapes and caches years of calendar data locally for incredibly fast, offline performance after the initial sync.
   - Smart Background Sync: All data fetching happens on a background thread, so the UI never freezes.
   - Force Resync: Manually re-download and update a year's calendar data to get the latest holiday and event information after it's officially released.

## Requirements

Python3.10 with the following dependencies installed.
```
requests==2.32.4
beautifulsoup4==4.13.4
PySide6==6.9.1
pywin32==311
pytz==2025.2
python-dateutil==2.9.0.post0
```

## Setup and Usage

SETUP:  
1. Ensure you have Python installed on your system. (Recommended <a href="https://www.python.org/downloads/release/python-31010/">Python 3.10.10</a>)
2. <a href="https://github.com/SubhojitGhimire/Miti-Tithi/archive/refs/heads/main.zip">Download this Repository</a>. Unzip it. (Ensure folder name is Miti-Tithi-main , if not, rename the folder to Miti-Tithi-main)
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
