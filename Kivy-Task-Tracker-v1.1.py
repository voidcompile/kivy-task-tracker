# task_timer_kivy.py
import json
import os
import traceback
from datetime import datetime, timedelta
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse

# ---------- THEME (dark + neon) ----------
Window.clearcolor = (0.03, 0.04, 0.07, 1)

COLOR_CARD = (0.06, 0.08, 0.12, 1)
COLOR_PANEL = (0.04, 0.06, 0.10, 0.95)
COLOR_NEON = (0.0, 0.79, 0.95, 0.95)
COLOR_TEXT = (0.92, 0.96, 1.0, 1)
COLOR_SUBTEXT = (0.72, 0.82, 0.9, 1)

COLOR_START = (0.0, 0.45, 0.0, 1)
COLOR_START_H = (0.0, 0.65, 0.15, 1)
COLOR_STOP = (0.0, 0.15, 0.6, 1)
COLOR_STOP_H = (0.0, 0.35, 0.9, 1)
COLOR_DELETE = (0.85, 0.2, 0.2, 1)
COLOR_DELETE_H = (0.95, 0.3, 0.3, 1)

DATA_FILE = "tasks_data.json"
ERROR_LOG = "error.log"


def log_error(e: Exception):
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - ERROR:\n")
        f.write(traceback.format_exc())
        f.write("\n\n")


def safe_load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("data root is not a dict")
            return data
    except Exception as e:
        try:
            backup_name = f"{DATA_FILE}.backup.{int(datetime.now().timestamp())}"
            os.rename(DATA_FILE, backup_name)
        except Exception:
            pass
        log_error(e)
        return {}


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(e)


def format_seconds(sec: int) -> str:
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h}:{m:02d}:{s:02d}"


def format_hours_decimal(sec: int) -> str:
    return f"{sec / 3600.0:.2f}"


# ---------- RoundedButton (with hover animation) ----------
class RoundedButton(ButtonBehavior, Label):
    """
    Fixed RoundedButton:
    - Do NOT manually dispatch on_press/on_release (avoid double triggers).
    - Hover animation still updates the background color.
    """
    def __init__(self, text="", bg_color=(0.2, 0.2, 0.2, 1), hover_color=None, radius=12, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.halign = "center"
        self.valign = "middle"
        self.color = (1, 1, 1, 1)
        self.padding = (10, 6)
        self.font_size = kwargs.get("font_size", 14)

        self.bg_color = bg_color
        # compute default hover if not provided
        if hover_color is None:
            hover_color = tuple(min(1, c + 0.15) for c in bg_color[:3]) + (bg_color[3],)
        self.hover_color = hover_color
        self.radius = radius
        self._hover = False

        # draw rounded background
        with self.canvas.before:
            self._col = Color(*self.bg_color)
            try:
                self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            except Exception:
                # fallback if RoundedRectangle unavailable
                from kivy.graphics import Rectangle
                self._rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_rect, size=self._update_rect)
        Window.bind(mouse_pos=self._on_mouse_pos)

    def _update_rect(self, *a):
        try:
            self._rect.pos = self.pos
            self._rect.size = self.size
        except Exception:
            pass

    def _on_mouse_pos(self, window, pos):
        # don't proceed if widget not in window yet
        if not self.get_root_window():
            return
        inside = self.collide_point(*self.to_widget(*pos))
        if inside and not self._hover:
            self._hover = True
            Animation.cancel_all(self._col)
            Animation(r=self.hover_color[0], g=self.hover_color[1],
                      b=self.hover_color[2], a=self.hover_color[3], d=0.14, t='out_quad').start(self._col)
        elif not inside and self._hover:
            self._hover = False
            Animation.cancel_all(self._col)
            Animation(r=self.bg_color[0], g=self.bg_color[1],
                      b=self.bg_color[2], a=self.bg_color[3], d=0.14, t='out_quad').start(self._col)



# ---------- Task widget ----------
class TaskWidget(BoxLayout):
    def __init__(self, task_name, date_str, app, initial_seconds=0, description="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 52
        self.spacing = 10
        self.padding = [6, 6, 6, 6]
        self.app = app
        self.task_name = task_name
        self.date_str = date_str

        self.total_seconds = int(initial_seconds or 0)
        self.session_start = None
        self.event = None
        self.description = description or ""

        self.name_label = Label(text=task_name, size_hint_x=0.40, halign="left", valign="middle", color=COLOR_TEXT)
        self.name_label.bind(size=self._update_label_text_size)

        self.time_label = Label(text=format_seconds(self.total_seconds), size_hint_x=0.22, halign="center", valign="middle", color=COLOR_NEON)
        self.time_label.bind(size=self._update_label_text_size)

        self.start_btn = RoundedButton(text="Start", bg_color=COLOR_START, hover_color=COLOR_START_H, radius=14, size_hint_x=0.09)
        self.stop_btn = RoundedButton(text="Stop", bg_color=COLOR_STOP, hover_color=COLOR_STOP_H, radius=14, size_hint_x=0.09)
        self.desc_btn = RoundedButton(text="Edit", bg_color=(0.08,0.12,0.18,1), hover_color=COLOR_NEON, radius=14, size_hint_x=0.10)
        self.delete_btn = RoundedButton(text="Delete", bg_color=COLOR_DELETE, hover_color=COLOR_DELETE_H, radius=14, size_hint_x=0.10)

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

    def _update_label_text_size(self, instance, value):
        instance.text_size = (instance.width - 4, None)

    def start_timer(self, instance):
        if self.session_start is None:
            self.session_start = datetime.now()
            self.event = Clock.schedule_interval(self.update_time_display, 0.5)
            self.app.update_summary()

    def stop_timer(self, instance):
        if self.session_start is not None:
            now = datetime.now()
            delta = int((now - self.session_start).total_seconds())
            self.total_seconds += delta
            self.session_start = None
            if self.event:
                self.event.cancel()
                self.event = None
            self.time_label.text = format_seconds(self.total_seconds)
            self.save_task_time()
            self.app.update_summary()

    def update_time_display(self, dt):
        elapsed = 0
        if self.session_start is not None:
            elapsed = int((datetime.now() - self.session_start).total_seconds())
        display = self.total_seconds + elapsed
        self.time_label.text = format_seconds(display)
        self.app.update_summary()

    def save_task_time(self):
        try:
            data = safe_load_data()
            if self.date_str not in data:
                data[self.date_str] = {}
            data[self.date_str][self.task_name] = {
                "seconds": int(self.total_seconds),
                "description": self.description
            }
            save_data(data)
        except Exception as e:
            log_error(e)

    def open_description_popup(self, instance):
        content = BoxLayout(orientation="vertical", spacing=8, padding=8)
        txt = TextInput(
            text=self.description or "",
            multiline=True,
            size_hint_y=0.78,
            foreground_color=(0, 0, 0, 1),
            background_color=(1, 1, 1, 1)
        )
        btn_layout = BoxLayout(size_hint_y=0.22, spacing=8)
        save_btn = RoundedButton(text="Save", bg_color=COLOR_NEON, hover_color=(0.3,1,1,1), radius=12)
        cancel_btn = RoundedButton(text="Cancel", bg_color=COLOR_CARD, hover_color=(0.12,0.18,0.28,1), radius=12)
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(txt)
        content.add_widget(btn_layout)

        popup = Popup(title=f"Edit description - {self.task_name}", content=content, size_hint=(0.8, 0.6))

        def do_save(inst):
            self.description = txt.text
            self.save_task_time()
            popup.dismiss()
            self.app.update_summary()

        def do_cancel(inst):
            popup.dismiss()

        save_btn.bind(on_press=do_save)
        cancel_btn.bind(on_press=do_cancel)
        popup.open()

    def confirm_delete(self, instance):
        content = BoxLayout(orientation="vertical", spacing=8, padding=8)
        lbl = Label(text=f"Delete task '{self.task_name}'?\nThis action cannot be undone.", halign="center", color=COLOR_TEXT)
        btn_layout = BoxLayout(size_hint_y=None, height=42, spacing=8)
        yes_btn = RoundedButton(text="Yes, delete", bg_color=COLOR_DELETE, hover_color=COLOR_DELETE_H, radius=12)
        no_btn = RoundedButton(text="Cancel", bg_color=COLOR_CARD, hover_color=(0.12,0.18,0.28,1), radius=12)
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        content.add_widget(lbl)
        content.add_widget(btn_layout)
        popup = Popup(title="Confirm delete", content=content, size_hint=(0.7, 0.38))

        def do_delete(_):
            try:
                if self.session_start is not None:
                    self.session_start = None
                    if self.event:
                        self.event.cancel()
                        self.event = None
                if self in self.app.task_list_layout.children:
                    self.app.task_list_layout.remove_widget(self)
                else:
                    try:
                        self.parent.remove_widget(self)
                    except Exception:
                        pass
                data = safe_load_data()
                if self.date_str in data and self.task_name in data[self.date_str]:
                    del data[self.date_str][self.task_name]
                    if not data[self.date_str]:
                        del data[self.date_str]
                    save_data(data)
                popup.dismiss()
                self.app.update_summary()
            except Exception as e:
                log_error(e)
                popup.dismiss()
                Popup(title="Error", content=Label(text="Delete failed. See error.log"), size_hint=(0.6, 0.3)).open()

        def do_cancel(_):
            popup.dismiss()

        yes_btn.bind(on_press=do_delete)
        no_btn.bind(on_press=do_cancel)
        popup.open()


# ---------- Screens ----------
class MainScreen(Screen):
    pass


class SummaryScreen(Screen):
    pass


# ---------- App ----------
class TaskApp(App):
    def build(self):
        self.current_date = datetime.now().date()
        self.side_open = False
        self.sm = ScreenManager()

        # main screen
        main_screen = MainScreen(name="main")
        root = BoxLayout(orientation="horizontal", padding=10, spacing=10)

        # background canvas (spacey neon blobs)
        with root.canvas.before:
            Color(0.03, 0.04, 0.07, 1)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
            Color(COLOR_NEON[0], COLOR_NEON[1], COLOR_NEON[2], 0.12)
            self._blob1 = Ellipse(pos=(root.x + 80, root.y + root.height * 0.5), size=(420, 420))
            Color(0.0, 0.15, 0.4, 0.10)
            self._blob2 = Ellipse(pos=(root.x + 300, root.y + root.height * 0.1), size=(600, 600))

        def _update_bg(*args):
            try:
                self._bg_rect.pos = root.pos
                self._bg_rect.size = root.size
                w, h = root.size
                self._blob1.pos = (root.x + int(w * 0.03), root.y + int(h * 0.35))
                self._blob1.size = (int(w * 0.45), int(h * 0.65))
                self._blob2.pos = (root.x + int(w * 0.35), root.y + int(h * 0.05))
                self._blob2.size = (int(w * 0.6), int(h * 0.6))
            except Exception as e:
                log_error(e)

        root.bind(pos=_update_bg, size=_update_bg)

        # left main area
        main_area = BoxLayout(orientation="vertical", spacing=10)

        # top controls
        top_controls = BoxLayout(size_hint_y=None, height=46, spacing=8)
        menu_btn = RoundedButton(text="Menu", bg_color=COLOR_PANEL, hover_color=(0.06,0.12,0.18,1), radius=14, size_hint_x=0.12)
        prev_btn = RoundedButton(text="Prev Day", bg_color=COLOR_CARD, hover_color=(0.12,0.18,0.28,1), radius=14, size_hint_x=0.14)
        next_btn = RoundedButton(text="Next Day", bg_color=COLOR_CARD, hover_color=(0.12,0.18,0.28,1), radius=14, size_hint_x=0.14)
        self.date_label = Label(text=self.current_date.isoformat(), size_hint_x=0.6, color=COLOR_TEXT)
        menu_btn.bind(on_press=self.toggle_side_panel)
        prev_btn.bind(on_press=self.prev_day)
        next_btn.bind(on_press=self.next_day)
        top_controls.add_widget(menu_btn)
        top_controls.add_widget(prev_btn)
        top_controls.add_widget(self.date_label)
        top_controls.add_widget(next_btn)

        # task input
        task_input = BoxLayout(size_hint_y=None, height=46, spacing=8)
        self.task_name_input = TextInput(hint_text="Task name...", multiline=False, foreground_color=COLOR_TEXT, background_color=COLOR_CARD)
        add_task_btn = RoundedButton(text="Add", bg_color=COLOR_NEON, hover_color=(0.3,1,1,1), radius=14, size_hint_x=0.18)
        add_task_btn.bind(on_press=self.add_task)
        task_input.add_widget(self.task_name_input)
        task_input.add_widget(add_task_btn)

        # task list
        container = BoxLayout(orientation="vertical", size_hint_y=None)
        container.bind(minimum_height=container.setter('height'))
        self.task_list_layout = container
        scroll = ScrollView()
        scroll.add_widget(container)

        # bottom summary bar
        summary_bar = BoxLayout(size_hint_y=None, height=44, spacing=8, padding=[6, 6, 6, 6])
        self.running_label = Label(text="Running: 0", size_hint_x=0.25, color=COLOR_TEXT)
        self.total_label = Label(text="Total (H:MM:SS): 0:00:00 | Hours: 0.00", size_hint_x=0.75, color=COLOR_NEON)
        summary_bar.add_widget(self.running_label)
        summary_bar.add_widget(self.total_label)

        main_area.add_widget(top_controls)
        main_area.add_widget(task_input)
        main_area.add_widget(scroll)
        main_area.add_widget(summary_bar)

        # right side panel
        self.side_panel = BoxLayout(orientation="vertical", size_hint_x=None, width=0, spacing=8, padding=[10,10,10,10], opacity=0)
        self.side_panel.disabled = True
        header_lbl = Label(text="Menu", size_hint_y=None, height=30, color=COLOR_NEON)
        self.side_panel.add_widget(header_lbl)
        all_summary_btn = RoundedButton(text="All Task Summary", bg_color=COLOR_PANEL, hover_color=(0.06,0.12,0.18,1), radius=14, size_hint_y=None, height=44)
        all_summary_btn.bind(on_press=self.open_summary_screen)
        self.side_panel.add_widget(all_summary_btn)
        export_btn = RoundedButton(text="Export CSV (All)", bg_color=COLOR_PANEL, hover_color=(0.06,0.12,0.18,1), radius=14, size_hint_y=None, height=44)
        export_btn.bind(on_press=self.export_csv_all)
        self.side_panel.add_widget(export_btn)
        self.side_panel.add_widget(Label(text="Tip:", size_hint_y=None, height=24, color=COLOR_SUBTEXT))
        self.side_panel.add_widget(Label(text="- Click Start/Stop to record\n- Use Delete to remove", size_hint_y=None, color=COLOR_SUBTEXT))

        root.add_widget(main_area)
        root.add_widget(self.side_panel)

        main_screen.add_widget(root)
        self.sm.add_widget(main_screen)

        # SUMMARY SCREEN
        summary_screen = SummaryScreen(name="summary")
        summary_root = BoxLayout(orientation="vertical", padding=8, spacing=8)
        with summary_root.canvas.before:
            Color(0.02, 0.03, 0.05, 1)
            self._summary_bg_rect = Rectangle(pos=summary_root.pos, size=summary_root.size)

        def _update_summary_bg(*args):
            try:
                self._summary_bg_rect.pos = summary_root.pos
                self._summary_bg_rect.size = summary_root.size
            except Exception as e:
                log_error(e)

        summary_root.bind(pos=_update_summary_bg, size=_update_summary_bg)

        header = BoxLayout(size_hint_y=None, height=46, spacing=8)
        back_btn = RoundedButton(text="Back", bg_color=COLOR_PANEL, hover_color=(0.06,0.12,0.18,1), radius=14, size_hint_x=0.14)
        header_label = Label(text="All Tasks Summary", size_hint_x=0.7, color=COLOR_NEON)
        refresh_btn = RoundedButton(text="Refresh", bg_color=COLOR_PANEL, hover_color=(0.06,0.12,0.18,1), radius=14, size_hint_x=0.16)
        header.add_widget(back_btn)
        header.add_widget(header_label)
        header.add_widget(refresh_btn)

        self.summary_container = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.summary_container.bind(minimum_height=self.summary_container.setter('height'))
        summary_scroll = ScrollView()
        summary_scroll.add_widget(self.summary_container)

        bottom_row = BoxLayout(size_hint_y=None, height=46, spacing=8)
        export_csv_btn = RoundedButton(text="Export CSV (All)", bg_color=COLOR_NEON, hover_color=(0.3,1,1,1), radius=14)
        export_csv_btn.bind(on_press=self.export_csv_all)
        bottom_row.add_widget(export_csv_btn)

        summary_root.add_widget(header)
        summary_root.add_widget(summary_scroll)
        summary_root.add_widget(bottom_row)
        summary_screen.add_widget(summary_root)
        self.sm.add_widget(summary_screen)

        back_btn.bind(on_press=lambda *_: self.sm.switch_to(main_screen))
        refresh_btn.bind(on_press=lambda *_: self.safe_build_summary_screen())

        self.load_tasks_for_date()
        self.update_summary()
        return self.sm

    def toggle_side_panel(self, instance):
        try:
            if self.side_open:
                anim = Animation(width=0, opacity=0, d=0.22, t='out_quad')
                def _on_complete(anim, widget):
                    widget.disabled = True
                anim.bind(on_complete=_on_complete)
                anim.start(self.side_panel)
                self.side_open = False
                instance.text = "Menu"
            else:
                self.side_panel.disabled = False
                anim = Animation(width=320, opacity=1, d=0.22, t='out_quad')
                anim.start(self.side_panel)
                self.side_open = True
                instance.text = "Close"
        except Exception as e:
            log_error(e)

    def load_tasks_for_date(self):
        try:
            self.task_list_layout.clear_widgets()
            date_str = self.current_date.isoformat()
            data = safe_load_data()
            if date_str in data:
                for task_name, info in data[date_str].items():
                    seconds = info.get("seconds", 0)
                    desc = info.get("description", "")
                    widget = TaskWidget(task_name, date_str, self, initial_seconds=seconds, description=desc)
                    widget.time_label.text = format_seconds(int(seconds))
                    self.task_list_layout.add_widget(widget)
            self.update_summary()
        except Exception as e:
            log_error(e)
            Popup(title="Error", content=Label(text="Failed to load tasks. See error.log"), size_hint=(0.6, 0.3)).open()

    def add_task(self, instance):
        try:
            task_name = self.task_name_input.text.strip()
            if not task_name:
                return
            date_str = self.current_date.isoformat()
            widget = TaskWidget(task_name, date_str, self, initial_seconds=0, description="")
            self.task_list_layout.add_widget(widget)
            data = safe_load_data()
            if date_str not in data:
                data[date_str] = {}
            if task_name not in data[date_str]:
                data[date_str][task_name] = {"seconds": 0, "description": ""}
                save_data(data)
            self.task_name_input.text = ""
            self.update_summary()
        except Exception as e:
            log_error(e)
            Popup(title="Error", content=Label(text="Failed to add task. See error.log"), size_hint=(0.6, 0.3)).open()

    def prev_day(self, instance):
        self.current_date -= timedelta(days=1)
        self.date_label.text = self.current_date.isoformat()
        self.load_tasks_for_date()

    def next_day(self, instance):
        self.current_date += timedelta(days=1)
        self.date_label.text = self.current_date.isoformat()
        self.load_tasks_for_date()

    def update_summary(self):
        try:
            running_count = 0
            total_seconds = 0
            for child in list(self.task_list_layout.children):
                if isinstance(child, TaskWidget):
                    if child.session_start is not None:
                        running_count += 1
                        elapsed = int((datetime.now() - child.session_start).total_seconds())
                    else:
                        elapsed = 0
                    total_seconds += child.total_seconds + elapsed

            hours_decimal = total_seconds / 3600.0
            self.running_label.text = f"Running: {running_count}"
            self.total_label.text = f"Total (H:MM:SS): {format_seconds(total_seconds)} | Hours: {hours_decimal:.2f}"
        except Exception as e:
            log_error(e)

    def safe_build_summary_screen(self):
        try:
            self.build_summary_screen()
        except Exception as e:
            log_error(e)
            Popup(title="Error", content=Label(text="Failed to build summary. See error.log"), size_hint=(0.7, 0.3)).open()

    def open_summary_screen(self, instance):
        self.safe_build_summary_screen()
        self.sm.current = "summary"

    def build_summary_screen(self):
        self.summary_container.clear_widgets()
        data = safe_load_data()
        agg = {}
        for date_str, tasks in data.items():
            if not isinstance(tasks, dict):
                continue
            for tname, info in tasks.items():
                try:
                    sec = int(info.get("seconds", 0) or 0)
                except Exception:
                    sec = 0
                if tname not in agg:
                    agg[tname] = {"total_seconds": 0, "per_day": {}}
                agg[tname]["total_seconds"] += sec
                if sec > 0:
                    agg[tname]["per_day"][date_str] = sec

        if not agg:
            self.summary_container.add_widget(Label(text="No tasks recorded yet.", size_hint_y=None, height=30, color=COLOR_TEXT))
            return

        for tname, info in sorted(agg.items(), key=lambda x: x[0].lower()):
            total = info["total_seconds"]
            days_count = len(info["per_day"])
            header_box = BoxLayout(size_hint_y=None, height=34, padding=[6, 6, 6, 6], spacing=8)
            header_lbl = Label(text=f"{tname}", halign="left", valign="middle", color=COLOR_NEON)
            header_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
            sub_lbl = Label(text=f"Total: {format_seconds(total)} | Days: {days_count} | Hours: {format_hours_decimal(total)}", halign="right", valign="middle", color=COLOR_TEXT)
            sub_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
            header_box.add_widget(header_lbl)
            header_box.add_widget(sub_lbl)
            self.summary_container.add_widget(header_box)

            if days_count > 0:
                for dstr, sec in sorted(info["per_day"].items()):
                    row = BoxLayout(size_hint_y=None, height=22, padding=[8, 0, 6, 0])
                    lbl_date = Label(text=dstr, size_hint_x=0.4, halign="left", valign="middle", color=COLOR_SUBTEXT)
                    lbl_time = Label(text=format_seconds(sec), size_hint_x=0.25, halign="center", valign="middle", color=COLOR_TEXT)
                    lbl_hours = Label(text=f"{format_hours_decimal(sec)} h", size_hint_x=0.35, halign="right", valign="middle", color=COLOR_SUBTEXT)
                    lbl_date.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
                    lbl_time.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
                    lbl_hours.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
                    row.add_widget(lbl_date)
                    row.add_widget(lbl_time)
                    row.add_widget(lbl_hours)
                    self.summary_container.add_widget(row)
            else:
                self.summary_container.add_widget(Label(text="  (no recorded days)", size_hint_y=None, height=22, color=COLOR_SUBTEXT))

    def export_csv_all(self, instance):
        try:
            data = safe_load_data()
            agg = {}
            for date_str, tasks in data.items():
                if not isinstance(tasks, dict):
                    continue
                for tname, info in tasks.items():
                    sec = int(info.get("seconds", 0) or 0)
                    if tname not in agg:
                        agg[tname] = {"total_seconds": 0, "per_day": {}}
                    agg[tname]["total_seconds"] += sec
                    if sec > 0:
                        agg[tname]["per_day"][date_str] = sec

            lines = ["task_name,total_seconds,days_count,per_day_breakdown"]
            for tname, info in agg.items():
                per_day_str = ";".join([f"{d}:{info['per_day'][d]}" for d in sorted(info["per_day"].keys())])
                lines.append(f"\"{tname}\",{info['total_seconds']},{len(info['per_day'])},\"{per_day_str}\"")

            out_file = "tasks_aggregated.csv"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            Popup(title="Export complete", content=Label(text=f"Exported to {out_file}"), size_hint=(0.6, 0.32)).open()
        except Exception as e:
            log_error(e)
            Popup(title="Error", content=Label(text="Export failed. See error.log"), size_hint=(0.6, 0.3)).open()

    def on_start(self):
        Clock.schedule_interval(lambda dt: self.update_summary(), 1.0)


if __name__ == "__main__":
    TaskApp().run()
