# Kivy Task Tracker

A lightweight daily task tracker built with **Python** and **Kivy** for desktop (Windows/Linux/Mac).

You can add unlimited tasks, track time spent on each task with a start/stop timer, write descriptions of your work, navigate between different days, and delete tasks with confirmation. All data is stored locally in JSON format and can be viewed day-by-day.

---

## Kivy Task Tracker — v1.3

A lightweight offline task tracker built with Kivy (Python). Track unlimited tasks per day with start/stop timers, per-task descriptions, a daily notepad, aggregated summaries, CSV export — and now charts (line chart for hours-per-day + per-day pie charts).

## 🚀 What’s new in v1.3

Charts screen:

Line chart: hours-per-day (x = date, y = hours).

Daily pie charts: per-day task distribution (one pie per day).

Chart visuals use white backgrounds and cool / cold colors (blues/teals/purples).

Charts are rendered with matplotlib (Agg) and saved as PNGs in charts_images/, then displayed inside the app.

UI and data flow improvements to integrate charts safely with the existing screens.

## 🧩 Features (summary)

Unlimited daily tasks (add, rename in code, remove).

Start / Stop timers per task (session times + saved totals).

Edit and save task descriptions (saved per day, per task).

Daily Notepad (saved per date).

All Task Summary screen (card layout, per-day breakdown).

Charts (line + pie) in menu — white background, cool colors.

Export aggregated CSV (tasks_aggregated.csv).

Persistent storage in tasks_data.json.

Neon/dark theme, rounded buttons with hover effects.

Robust error logging (error.log) and safe JSON handling with automatic backups.

## ⚙️ Requirements

Python 3.8+ recommended

[Kivy] installed (the app uses standard Kivy widgets)

matplotlib required for charts:

```bash
pip install matplotlib
```
If your Kivy version does not support RoundedRectangle, the app will fall back to plain rectangles — updating Kivy is recommended for full styling.

## 📁 Data files
```bach
{
  "2025-08-18": {
    "German": {
      "seconds": 3600,
      "description": "Vocabulary drill"
    },
    "Programming": {
      "seconds": 7200,
      "description": "Refactoring module X"
    },
    "_note": "Short daily note for this date"
  },
  "2025-08-17": {
    ...
  }
}
```
## 🧭 How to use (quick)

Add a task name → click Add.

Use Start / Stop to measure working time.

Click Edit to open the description editor (black text on white background for readability).

Navigate dates with Prev Day / Next Day.

Open Menu → choose Notepad, All Task Summary, Charts, or Export CSV.

Notepad saves per-date notes (_note in JSON).

Charts builds and displays the line chart and a set of pie charts (one per day with tasks). Click a pie to open a larger popup with a legend.

## 🧾 Changelog (highlight)
v1.3

Added Charts (line chart + per-day pies using matplotlib).

Chart visuals: white background + cold color palette.

UI integration for charts, saved PNGs in charts_images/.

v1.2

Added Notepad, redesigned summary, rounded buttons with hover, Neon theme, export CSV, robust navigation, safe JSON handling, error logging.


## 📜 License
This project is licensed under the MIT License — feel free to use and modify it.

## 💻 voidcompile
Stay updated with daily Python & AI projects on our channel:

📢 [telegram](https://t.me/voidcompile)  
💻 [github](https://github.com/voidcompile)  
▶️ [youtube](https://youtube.com/@voidcompile)  
✉️ [gmail](mailto:voidcompile@gmail.com)  

