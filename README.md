# Kivy Task Tracker

A lightweight daily task tracker built with **Python** and **Kivy** for desktop (Windows/Linux/Mac).

You can add unlimited tasks, track time spent on each task with a start/stop timer, write descriptions of your work, navigate between different days, and delete tasks with confirmation. All data is stored locally in JSON format and can be viewed day-by-day.

---

## Release v1.2 — Summary
✅ Added (New Features)

Notepad (Daily Notepad)

Added a notepad screen accessible from the menu for quick daily reminders.

Each note is saved per date in tasks_data.json (key _note).

Quick access button Open Notepad added at the top of the main screen.

All Task Summary — readable card layout

Redesigned summary screen: clean card layout, header for each task, days count, total hours, and per-day breakdown.

Rounded buttons + hover effect

All buttons are now rounded with a smooth hover animation.

A global HoverManager handles hover state efficiently with only one mouse listener.

Neon / Space-themed dark background

Modern neon-dark "futuristic" theme with animated blue/purple blobs.

Export CSV (aggregated)

Added the ability to export aggregated task statistics into tasks_aggregated.csv.

Safe JSON handling & backups

safe_load_data function now prevents crashes if the JSON file is corrupted.

Automatic .backup.<timestamp> creation on failure.

Error logging

All unexpected errors are logged to error.log for debugging.

Robust screen navigation

Replaced direct switch_to() calls with safe_switch_to() for more stable navigation.

## 🐞 Fixed (Bug Fixes)

Double-trigger click issue resolved — buttons no longer trigger actions twice.

Fixed ScreenManagerException crashes when navigating back from Summary or Notepad.

Fixed crashes when re-opening Summary multiple times in a row.

Description editing text visibility — now uses black text on white background for clarity.

Hidden menu panel — fully hidden when closed (width=0, opacity=0, disabled=True).

Safe JSON recovery — corrupted tasks_data.json no longer crashes the app.

## ⚠️ Known Issues

Older Kivy versions may not render RoundedRectangle properly (fallback partially in place).

HoverManager currently keeps references to all rounded buttons; dynamically removing many widgets may require unregister cleanup.

Simultaneous multiple timers work but have not been heavily stress-tested.

Task deletion is permanent — no undo/archive feature yet.

On very small resolutions, Summary cards may look compact (needs responsive tweaks).

## 🧪 Test Checklist

Open/close Menu — panel should be fully hidden when closed.

Add tasks across multiple days, start/stop timers, open All Task Summary — totals and per-day breakdown should be correct.

Open Notepad, add text, save, switch days, and return — note should persist per date.

Hover over buttons — color change should be smooth and responsive.

Delete a task — confirmation prompt should appear, task removed from JSON.

Corrupt tasks_data.json manually, restart — app should back up the file and load with empty data; error in error.log.

Export CSV — open tasks_aggregated.csv to verify aggregated stats.

## 📝 Version & File Info

Version: v1.2

Main file: task_timer_kivy_v1.2.py

Data file: tasks_data.json (backups as tasks_data.json.backup.<timestamp>)

Upgrade tip: commit changes and back up tasks_data.json before replacing files.

## ✨ Suggested Next Features

Undo / Archive instead of permanent delete.

Search & Filter in Summary (by task name or date range).

Charts (daily/weekly hours per task).

Customizable theme (colors, hover speed, corner radius).

Optional cloud sync with encryption.

## ▶️ Usage
Run the application with:
```
python task_timer_kivy.py
```

## 📜 License
This project is licensed under the MIT License — feel free to use and modify it.

## 💻 voidcompile
Stay updated with daily Python & AI projects on our channel:

📢 [telegram](https://t.me/voidcompile)  
💻 [github](https://github.com/voidcompile)  
▶️ [youtube](https://youtube.com/@voidcompile)  
✉️ [gmail](mailto:voidcompile@gmail.com)  

