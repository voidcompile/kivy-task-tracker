# task_timer_kivy.py
import json
import os
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window

# optional: set window size for desktop
Window.size = (900, 600)

DATA_FILE = "tasks_data.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def format_seconds(sec: int) -> str:
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h}:{m:02d}:{s:02d}"


class TaskWidget(BoxLayout):
    def __init__(self, task_name, date_str, app, initial_seconds=0, description="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 44
        self.spacing = 6
        self.padding = [4, 4, 4, 4]

        self.app = app
        self.task_name = task_name
        self.date_str = date_str

        # persistent total seconds (saved) and running session start
        self.total_seconds = int(initial_seconds or 0)
        self.session_start = None  # datetime when current session started
        self.event = None  # Clock event

        # UI elements (all English)
        self.name_label = Label(text=task_name, size_hint_x=0.38, halign="left", valign="middle")
        self.name_label.bind(size=self._update_label_text_size)
        self.time_label = Label(text=format_seconds(self.total_seconds), size_hint_x=0.2, halign="center", valign="middle")
        self.time_label.bind(size=self._update_label_text_size)

        self.start_btn = Button(text="Start", size_hint_x=0.10)
        self.stop_btn = Button(text="Stop", size_hint_x=0.10)
        self.desc_btn = Button(text="Edit", size_hint_x=0.12)
        self.delete_btn = Button(text="Delete", size_hint_x=0.10, background_color=(1, 0.3, 0.3, 1))

        self.start_btn.bind(on_press=self.start_timer)
        self.stop_btn.bind(on_press=self.stop_timer)
        self.desc_btn.bind(on_press=self.open_description_popup)
        self.delete_btn.bind(on_press=self.confirm_delete)

        self.add_widget(self.name_label)
        self.add_widget(self.time_label)
        self.add_widget(self.start_btn)
        self.add_widget(self.stop_btn)
        self.add_widget(self.desc_btn)
        self.add_widget(self.delete_btn)

        # description (loaded)
        self.description = description or ""

    def _update_label_text_size(self, instance, value):
        instance.text_size = (instance.width - 8, None)

    def start_timer(self, instance):
        if self.session_start is None:
            self.session_start = datetime.now()
            # update display every 0.5s for smoother update
            self.event = Clock.schedule_interval(self.update_time_display, 0.5)

    def stop_timer(self, instance):
        if self.session_start is not None:
            now = datetime.now()
            delta = int((now - self.session_start).total_seconds())
            # add only the session delta to total
            self.total_seconds += delta
            self.session_start = None
            if self.event:
                self.event.cancel()
                self.event = None
            # update UI and save
            self.time_label.text = format_seconds(self.total_seconds)
            self.save_task_time()

    def update_time_display(self, dt):
        # show total + running session elapsed
        elapsed = 0
        if self.session_start is not None:
            elapsed = int((datetime.now() - self.session_start).total_seconds())
        display = self.total_seconds + elapsed
        self.time_label.text = format_seconds(display)

    def save_task_time(self):
        data = load_data()
        if self.date_str not in data:
            data[self.date_str] = {}
        if self.task_name not in data[self.date_str]:
            data[self.date_str][self.task_name] = {"seconds": 0, "description": ""}
        # overwrite with current total_seconds (keeps sums consistent)
        data[self.date_str][self.task_name]["seconds"] = int(self.total_seconds)
        data[self.date_str][self.task_name]["description"] = self.description
        save_data(data)

    def open_description_popup(self, instance):
        # Popup with existing description loaded
        content = BoxLayout(orientation="vertical", spacing=8, padding=8)
        txt = TextInput(text=self.description or "", multiline=True, size_hint_y=0.8)
        btn_layout = BoxLayout(size_hint_y=0.2, spacing=8)
        save_btn = Button(text="Save")
        cancel_btn = Button(text="Cancel")
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(txt)
        content.add_widget(btn_layout)

        popup = Popup(title=f"Edit description - {self.task_name}",
                      content=content,
                      size_hint=(0.8, 0.6))

        def do_save(instance):
            self.description = txt.text
            self.save_task_time()
            popup.dismiss()

        def do_cancel(instance):
            popup.dismiss()

        save_btn.bind(on_press=do_save)
        cancel_btn.bind(on_press=do_cancel)
        popup.open()

    def confirm_delete(self, instance):
        # Confirmation popup before actual deletion
        content = BoxLayout(orientation="vertical", spacing=8, padding=8)
        lbl = Label(text=f"Delete task '{self.task_name}'?\nThis action cannot be undone.", halign="center")
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=8)
        yes_btn = Button(text="Yes, delete")
        no_btn = Button(text="Cancel")
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        content.add_widget(lbl)
        content.add_widget(btn_layout)

        popup = Popup(title="Confirm delete", content=content, size_hint=(0.7, 0.35))

        def do_delete(_):
            # stop timer if running
            if self.session_start is not None:
                self.session_start = None
                if self.event:
                    self.event.cancel()
                    self.event = None
            # remove from UI
            try:
                self.app.task_list_layout.remove_widget(self)
            except Exception:
                # fallback: try parent removal
                if self.parent:
                    try:
                        self.parent.remove_widget(self)
                    except Exception:
                        pass
            # remove from data file
            data = load_data()
            if self.date_str in data and self.task_name in data[self.date_str]:
                del data[self.date_str][self.task_name]
                if not data[self.date_str]:
                    del data[self.date_str]
                save_data(data)
            popup.dismiss()

        def do_cancel(_):
            popup.dismiss()

        yes_btn.bind(on_press=do_delete)
        no_btn.bind(on_press=do_cancel)
        popup.open()


class TaskApp(App):
    def build(self):
        self.current_date = datetime.now().date()
        root = BoxLayout(orientation="vertical", padding=8, spacing=8)

        # Date control area
        date_control = BoxLayout(size_hint_y=None, height=44)
        prev_btn = Button(text="Prev Day", size_hint_x=0.15)
        next_btn = Button(text="Next Day", size_hint_x=0.15)
        self.date_label = Label(text=self.current_date.isoformat(), size_hint_x=0.7)
        prev_btn.bind(on_press=self.prev_day)
        next_btn.bind(on_press=self.next_day)
        date_control.add_widget(prev_btn)
        date_control.add_widget(self.date_label)
        date_control.add_widget(next_btn)

        # Task input area
        task_input = BoxLayout(size_hint_y=None, height=44)
        self.task_name_input = TextInput(hint_text="Task name...", multiline=False)
        add_task_btn = Button(text="Add", size_hint_x=0.18)
        add_task_btn.bind(on_press=self.add_task)
        task_input.add_widget(self.task_name_input)
        task_input.add_widget(add_task_btn)

        # Scrollable list of tasks
        container = BoxLayout(orientation="vertical", size_hint_y=None)
        container.bind(minimum_height=container.setter('height'))
        self.task_list_layout = container
        scroll = ScrollView()
        scroll.add_widget(container)

        # assemble
        root.add_widget(date_control)
        root.add_widget(task_input)
        root.add_widget(scroll)

        # load tasks for today
        self.load_tasks_for_date()
        return root

    def load_tasks_for_date(self):
        self.task_list_layout.clear_widgets()
        date_str = self.current_date.isoformat()
        data = load_data()
        if date_str in data:
            for task_name, info in data[date_str].items():
                seconds = info.get("seconds", 0)
                desc = info.get("description", "")
                widget = TaskWidget(task_name, date_str, self, initial_seconds=seconds, description=desc)
                # ensure label shows saved total
                widget.time_label.text = format_seconds(int(seconds))
                self.task_list_layout.add_widget(widget)

    def add_task(self, instance):
        task_name = self.task_name_input.text.strip()
        if not task_name:
            return
        date_str = self.current_date.isoformat()
        # create widget with zero initial seconds
        widget = TaskWidget(task_name, date_str, self, initial_seconds=0, description="")
        self.task_list_layout.add_widget(widget)
        # ensure data file has an entry so it persists (optional)
        data = load_data()
        if date_str not in data:
            data[date_str] = {}
        if task_name not in data[date_str]:
            data[date_str][task_name] = {"seconds": 0, "description": ""}
            save_data(data)
        self.task_name_input.text = ""

    def prev_day(self, instance):
        from datetime import timedelta
        self.current_date -= timedelta(days=1)
        self.date_label.text = self.current_date.isoformat()
        self.load_tasks_for_date()

    def next_day(self, instance):
        from datetime import timedelta
        self.current_date += timedelta(days=1)
        self.date_label.text = self.current_date.isoformat()
        self.load_tasks_for_date()


if __name__ == "__main__":
    TaskApp().run()
