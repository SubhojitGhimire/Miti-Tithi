import sys
import json
import pytz
import platform
import uuid
from PySide6.QtWidgets import QStyle
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


from src.data_manager import DataManager
from src.settings_manager import SettingsManager

from PySide6.QtCore import Qt, QTimer, QPoint, QThread, Signal, QSize, QDate, QTime
from PySide6.QtGui import QIcon, QAction, QScreen, QPainter, QColor, QFont, QMouseEvent, QCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QFrame, QSystemTrayIcon, QMenu, QDialog, QDialogButtonBox,
                                QComboBox, QGridLayout, QScrollArea, QPushButton, QListWidget,
                                QListWidgetItem, QSpinBox, QCheckBox, QStyle, QSizeGrip, QTabWidget,
                                QDateEdit, QMessageBox, QLineEdit, QTimeEdit)

try:
    with open("src/styles/light_theme.css", "r") as f:
        LIGHT_THEME_STYLESHEET = f.read()
    with open("src/styles/dark_theme.css", "r") as f:
        DARK_THEME_STYLESHEET = f.read()
except FileNotFoundError:
    print("Error: Stylesheet files not found. Make sure they are in src/styles/")
    LIGHT_THEME_STYLESHEET = ""
    DARK_THEME_STYLESHEET = ""

class DayWidget(QFrame):
    clicked = Signal(dict)

    def __init__(self, day_data):
        super().__init__()
        self.day_data = day_data
        self.setObjectName("DayWidget")
        self.setProperty("isHoliday", day_data.get("is_holiday", False))
        self.setProperty("isToday", day_data.get("is_today", False))

        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2,2,2,2)
        layout.setSpacing(0)
        
        nep_day_label = QLabel(str(day_data['nepali_day']))
        nep_day_label.setObjectName("NepDayLabel")
        nep_day_label.setAlignment(Qt.AlignCenter)
        nep_day_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        eng_day = datetime.strptime(day_data['gregorian_date'], "%Y-%m-%d").day
        eng_day_label = QLabel(str(eng_day))
        eng_day_label.setAlignment(Qt.AlignCenter)
        eng_day_label.setStyleSheet("font-size: 10px;")

        layout.addWidget(nep_day_label)
        layout.addWidget(eng_day_label)

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit(self.day_data)
        super().mousePressEvent(event)

class DayDetailDialog(QDialog):
    def __init__(self, day_data, parent=None):
        super().__init__(parent)
        self.setObjectName("DayDetailDialog")
        self.setWindowTitle("Day Details")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.Popup)
        
        layout = QVBoxLayout(self)
        
        nep_date_str = f"{day_data['nepali_month']} {day_data['nepali_day']}, {day_data['nepali_year']}"
        nep_date_label = QLabel(nep_date_str)
        nep_date_label.setStyleSheet("font-size: 16px; font-weight: bold; color:#777")
        
        eng_date_obj = datetime.strptime(day_data['gregorian_date'], "%Y-%m-%d")
        eng_date_str = eng_date_obj.strftime("%A, %B %d, %Y")
        eng_date_label = QLabel(eng_date_str)
        eng_date_label.setStyleSheet("font-size: 12px; color: #777;")

        tithi_label = QLabel(day_data['tithi'])
        tithi_label.setStyleSheet("font-size: 14px; font-style: italic; color: #777")

        layout.addWidget(nep_date_label)
        layout.addWidget(eng_date_label)
        layout.addWidget(tithi_label)

        if day_data['events']:
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            layout.addWidget(line)
            for event in day_data['events']:
                event_label = QLabel(event)
                event_label.setStyleSheet("font-size: 14px; font-style: italic; color: #777")
                layout.addWidget(event_label)

    def mousePressEvent(self, event):
        self.close()

class DateSelectionDialog(QDialog):
    date_selected = Signal(int, int)

    def __init__(self, current_year, current_month_index, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date")
        
        layout = QGridLayout(self)
        
        layout.addWidget(QLabel("Year (B.S.):"), 0, 0)
        self.year_combo = QComboBox()
        years = [str(y) for y in range(2000, 2101)]
        self.year_combo.addItems(years)
        self.year_combo.setCurrentText(str(current_year))
        layout.addWidget(self.year_combo, 0, 1)

        layout.addWidget(QLabel("Month:"), 1, 0)
        self.month_combo = QComboBox()
        from src.scraper import CalendarScraper
        self.month_combo.addItems(CalendarScraper.NEPALI_MONTHS_LIST)
        self.month_combo.setCurrentIndex(current_month_index)
        layout.addWidget(self.month_combo, 1, 1)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box, 2, 0, 1, 2)

    def accept(self):
        year = int(self.year_combo.currentText())
        month_index = self.month_combo.currentIndex()
        self.date_selected.emit(year, month_index)
        super().accept()

class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Settings")
        self.setMinimumWidth(350)
        layout = QVBoxLayout(self)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.setCurrentText(self.settings_manager.get("theme"))
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        placement_layout = QHBoxLayout()
        placement_layout.addWidget(QLabel("Widget Placement:"))
        self.placement_combo = QComboBox()
        self.placement_combo.addItems(["Free", "Top-Right", "Bottom-Right", "Top-Left", "Bottom-Left"])
        self.placement_combo.setCurrentText(self.settings_manager.get("widget_placement"))
        placement_layout.addWidget(self.placement_combo)
        layout.addLayout(placement_layout)

        self.startup_checkbox = QCheckBox("Run automatically on Windows startup")
        if platform.system() == "Windows": 
            self.startup_checkbox.setChecked(self.settings_manager.get("run_on_startup"))
        else: 
            self.startup_checkbox.setEnabled(False)
        self.startup_checkbox.setToolTip("This feature is only available on Windows.")
        layout.addWidget(self.startup_checkbox)
        
        resizing_layout = QHBoxLayout()
        self.resize_checkbox = QCheckBox("Allow Resizing")
        self.resize_checkbox.setChecked(self.settings_manager.get("resizing_enabled"))
        reset_button = QPushButton("Reset Sizes")
        reset_button.clicked.connect(self.reset_sizes)
        resizing_layout.addWidget(self.resize_checkbox)
        resizing_layout.addStretch()
        resizing_layout.addWidget(reset_button)
        layout.addLayout(resizing_layout)

        sync_layout = QGridLayout()
        sync_layout.addWidget(QLabel("Sync Start Year (BS):"), 0, 0)
        self.start_year_spin = QSpinBox()
        self.start_year_spin.setRange(2000, 2100)
        self.start_year_spin.setValue(self.settings_manager.get("sync_start_year"))
        sync_layout.addWidget(self.start_year_spin, 0, 1)
        sync_layout.addWidget(QLabel("Sync End Year (BS):"), 1, 0)
        self.end_year_spin = QSpinBox()
        self.end_year_spin.setRange(2000, 2100)
        self.end_year_spin.setValue(self.settings_manager.get("sync_end_year"))
        sync_layout.addWidget(self.end_year_spin, 1, 1)
        layout.addLayout(sync_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def reset_sizes(self):
        defaults = self.settings_manager._get_default_settings()
        self.settings_manager.set("widget_size", defaults["widget_size"])
        self.settings_manager.set("minimized_size", defaults["minimized_size"])
        self.settings_manager.set("calendar_size", defaults["calendar_size"])
        self.sender().setText("Sizes Reset!")
        self.sender().setEnabled(False)

    def accept(self):
        self.settings_manager.set("theme", self.theme_combo.currentText())
        self.settings_manager.set("widget_placement", self.placement_combo.currentText())
        self.settings_manager.set("resizing_enabled", self.resize_checkbox.isChecked())
        if platform.system() == "Windows": 
            self.settings_manager.set_startup(self.startup_checkbox.isChecked())
        self.settings_manager.set("sync_start_year", self.start_year_spin.value())
        self.settings_manager.set("sync_end_year", self.end_year_spin.value())
        super().accept()

class EventWidget(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EventWidget")
        self.setWindowTitle("Today's Events")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.main_frame)

        self.layout = QVBoxLayout(self.main_frame)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Today's Events")
        title.setObjectName("TodaysEvents")
        self.layout.addWidget(title)

        self.is_dragging = False
        self.drag_position = QPoint()

    def update_events(self, events):
        for i in reversed(range(1, self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)

        if events:
            for event in events:
                eventLabel = QLabel(f"• {event}")
                eventLabel.setObjectName("TodaysEvents")
                self.layout.addWidget(eventLabel)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging and event.buttons() == Qt.LeftButton: 
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_dragging = False
        event.accept()

class DateToolsDialog(QDialog):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.setWindowTitle("Date Tools")
        self.setMinimumWidth(400)

        main_layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        
        tab_widget.addTab(self._create_converter_tab(), "Converter")
        tab_widget.addTab(self._create_age_calculator_tab(), "Age Calculator")
        tab_widget.addTab(self._create_date_difference_tab(), "Date Difference")
        
        main_layout.addWidget(tab_widget)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def _create_converter_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        ad_to_bs_box = QFrame()
        ad_to_bs_box.setFrameShape(QFrame.StyledPanel)
        ad_to_bs_layout = QGridLayout(ad_to_bs_box)
        ad_to_bs_layout.addWidget(QLabel("<b>AD to BS Lookup</b>"), 0, 0, 1, 2)
        self.ad_input = QDateEdit(QDate.currentDate())
        self.ad_input.setCalendarPopup(True)
        ad_lookup_btn = QPushButton("Lookup")
        ad_lookup_btn.clicked.connect(self.lookup_ad_to_bs)
        self.ad_result_label = QLabel("Result: ...")
        ad_to_bs_layout.addWidget(QLabel("AD Date:"), 1, 0)
        ad_to_bs_layout.addWidget(self.ad_input, 1, 1)
        ad_to_bs_layout.addWidget(ad_lookup_btn, 2, 1)
        ad_to_bs_layout.addWidget(self.ad_result_label, 3, 0, 1, 2)
        layout.addWidget(ad_to_bs_box)
        
        bs_to_ad_box = QFrame()
        bs_to_ad_box.setFrameShape(QFrame.StyledPanel)
        bs_to_ad_layout = QGridLayout(bs_to_ad_box)
        bs_to_ad_layout.addWidget(QLabel("<b>BS to AD Lookup</b>"), 0, 0, 1, 3)
        self.bs_year_input = QSpinBox()
        self.bs_year_input.setRange(2000, 2100)
        self.bs_month_input = QComboBox()
        self.bs_month_input.addItems([m for m in self.data_manager.scraper.NEPALI_MONTHS_LIST])
        self.bs_day_input = QSpinBox()
        self.bs_day_input.setRange(1, 32)
        bs_lookup_btn = QPushButton("Lookup")
        bs_lookup_btn.clicked.connect(self.lookup_bs_to_ad)
        self.bs_result_label = QLabel("Result: ...")
        bs_to_ad_layout.addWidget(self.bs_year_input, 1, 0)
        bs_to_ad_layout.addWidget(self.bs_month_input, 1, 1)
        bs_to_ad_layout.addWidget(self.bs_day_input, 1, 2)
        bs_to_ad_layout.addWidget(bs_lookup_btn, 2, 2)
        bs_to_ad_layout.addWidget(self.bs_result_label, 3, 0, 1, 3)
        layout.addWidget(bs_to_ad_box)

        return tab

    def _create_age_calculator_tab(self):
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.addWidget(QLabel("<b>Age Calculator</b>"), 0, 0, 1, 2)
        layout.addWidget(QLabel("Birth Date (AD):"), 1, 0)
        self.age_input = QDateEdit(QDate.currentDate().addYears(-20))
        self.age_input.setCalendarPopup(True)
        age_calc_btn = QPushButton("Calculate Age")
        age_calc_btn.clicked.connect(self.calculate_age)
        self.age_result_label = QLabel("Result: ...")
        layout.addWidget(self.age_input, 1, 1)
        layout.addWidget(age_calc_btn, 2, 1)
        layout.addWidget(self.age_result_label, 3, 0, 1, 2)
        return tab

    def _create_date_difference_tab(self):
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.addWidget(QLabel("<b>Date Difference</b>"), 0, 0, 1, 2)
        layout.addWidget(QLabel("Start Date:"), 1, 0)
        self.diff_start_input = QDateEdit(QDate.currentDate())
        self.diff_start_input.setCalendarPopup(True)
        layout.addWidget(self.diff_start_input, 1, 1)
        layout.addWidget(QLabel("End Date:"), 2, 0)
        self.diff_end_input = QDateEdit(QDate.currentDate().addDays(10))
        self.diff_end_input.setCalendarPopup(True)
        layout.addWidget(self.diff_end_input, 2, 1)
        diff_calc_btn = QPushButton("Calculate Difference")
        diff_calc_btn.clicked.connect(self.calculate_difference)
        self.diff_result_label = QLabel("Result: ...")
        layout.addWidget(diff_calc_btn, 3, 1)
        layout.addWidget(self.diff_result_label, 4, 0, 1, 2)
        return tab

    def lookup_ad_to_bs(self):
        ad_date = self.ad_input.date().toString("yyyy-MM-dd")
        nep_data = self.data_manager.get_data_for_date(ad_date)
        if nep_data:
            self.ad_result_label.setText(f"Result: {nep_data['nepali_date_expanded']}, {nep_data['weekday']}")
        else:
            self.ad_result_label.setText("Result: Date out of sync range.")

    def lookup_bs_to_ad(self):
        nep_data = self.data_manager.lookup_bs_to_ad(
            self.bs_year_input.value(),
            self.bs_month_input.currentIndex(),
            self.bs_day_input.value()
        )
        if nep_data:
            self.bs_result_label.setText(f"Result: {nep_data['gregorian_date_expanded']}, {nep_data['weekday']}")
        else:
            self.bs_result_label.setText("Result: Invalid BS Date or out of range.")
    
    def calculate_age(self):
        birth_date = self.age_input.date().toPython()
        today = QDate.currentDate().toPython()
        delta = relativedelta(today, birth_date)
        self.age_result_label.setText(f"Result: {delta.years} years, {delta.months} months, {delta.days} days")

    def calculate_difference(self):
        start_date = self.diff_start_input.date().toPython()
        end_date = self.diff_end_input.date().toPython()
        if start_date > end_date:
            self.diff_result_label.setText("Result: Start date must be before end date.")
            return
        delta = relativedelta(end_date, start_date)
        total_days = (end_date - start_date).days
        self.diff_result_label.setText(f"Result: {delta.years}Y, {delta.months}M, {delta.days}D ({total_days} total days)")

class ReminderAlert(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reminder!")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.main_frame)

        content_layout = QVBoxLayout(self.main_frame)
        title = QLabel("⏰ Reminder!")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px; color: #b85656;")
        content_layout.addWidget(title)
        
        reminder_text = QLabel(text)
        reminder_text.setWordWrap(True)
        reminder_text.setStyleSheet("font-size: 14px; padding: 10px;")
        content_layout.addWidget(reminder_text)
        
        dismiss_button = QPushButton("Dismiss")
        dismiss_button.clicked.connect(self.accept)
        content_layout.addWidget(dismiss_button, 0, Qt.AlignRight)

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_style)
        self.is_blinked = False
        self.blink_timer.start(500)

    def toggle_style(self):
        if self.is_blinked:
            self.main_frame.setStyleSheet("")
        else:
            self.main_frame.setStyleSheet("border: 2px solid #b85656;")
        self.is_blinked = not self.is_blinked

class AddReminderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Reminder")
        layout = QGridLayout(self)
        
        layout.addWidget(QLabel("Reminder Text:"), 0, 0)
        self.text_input = QLineEdit()
        layout.addWidget(self.text_input, 0, 1)
        
        layout.addWidget(QLabel("Date:"), 1, 0)
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        layout.addWidget(self.date_input, 1, 1)

        layout.addWidget(QLabel("Time:"), 2, 0)
        self.time_input = QTimeEdit(QTime.currentTime().addSecs(3600))
        layout.addWidget(self.time_input, 2, 1)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box, 3, 0, 1, 2)

    def get_reminder_data(self):
        text = self.text_input.text()
        if not text: return None
        
        naive_dt = datetime.combine(self.date_input.date().toPython(), self.time_input.time().toPython())
        
        nepal_tz = pytz.timezone('Asia/Kathmandu')
        aware_dt = nepal_tz.localize(naive_dt)

        return {
            "id": str(uuid.uuid4()),
            "time": aware_dt.isoformat(),
            "text": text
        }

class RemindersDialog(QDialog):
    def __init__(self, reminders, parent=None):
        super().__init__(parent)
        self.reminders = sorted(reminders, key=lambda r: r['time'])
        self.setWindowTitle("Manage Reminders")
        self.setMinimumSize(450, 300)

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.populate_list()
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Reminder")
        remove_btn = QPushButton("Remove Selected")
        add_btn.clicked.connect(self.add_reminder)
        remove_btn.clicked.connect(self.remove_reminder)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(remove_btn)
        layout.addLayout(button_layout)

    def populate_list(self):
        self.list_widget.clear()
        for reminder in self.reminders:
            dt = datetime.fromisoformat(reminder['time'])
            item_text = f"{dt.strftime('%Y-%m-%d %I:%M %p')} - {reminder['text']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, reminder['id'])
            self.list_widget.addItem(item)
    
    def add_reminder(self):
        dialog = AddReminderDialog(self)
        if dialog.exec():
            new_reminder = dialog.get_reminder_data()
            if new_reminder:
                self.reminders.append(new_reminder)
                self.reminders.sort(key=lambda r: r['time'])
                self.populate_list()

    def remove_reminder(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item: return
        
        reminder_id = selected_item.data(Qt.UserRole)
        self.reminders = [r for r in self.reminders if r['id'] != reminder_id]
        self.populate_list()
    
    def get_updated_reminders(self):
        return self.reminders

class MainWindow(QMainWindow):
    start_sync_signal = Signal(int, int, bool)
    theme_changed = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.settings_manager = SettingsManager()
        self.data_manager = DataManager()
        self.is_minimized_mode = False
        self.is_maximized_mode = False
        self.is_dragging = False
        self.drag_position = QPoint()
        self.nepali_timezone = pytz.timezone('Asia/Kathmandu')
        self.today_gregorian_str = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now()
        self.current_calendar_nep_year = now.year
        self.current_calendar_nep_month_index = now.month - 1
        
        self.active_day_detail_dialog = None
        self.is_quitting = False
        self.is_event_panel_visible = True
        self.event_widget = None
        self.reminders = self.settings_manager.load_reminders()
        self.active_alerts = []
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(10000)

        self.setup_threading()
        self.setup_ui()
        self.create_system_tray_icon()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_time_and_display)
        self.update_timer.start(1000)
        self.theme_changed.connect(self.apply_theme)
        self.apply_theme()
        self.update_time_and_display()
        self.position_widget()
        self.trigger_sync()

        self.update_resize_policy()
        self.position_widget() 
        self.trigger_sync()
    
    def setup_threading(self):
        self.sync_thread = QThread()
        self.data_manager.moveToThread(self.sync_thread)
        self.start_sync_signal.connect(self.data_manager.run_sync)
        self.data_manager.sync_progress.connect(self.update_sync_status)
        self.data_manager.sync_finished.connect(self.on_sync_finished)
        self.sync_thread.start()

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.setCentralWidget(self.main_frame)
        
        main_layout = QVBoxLayout(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.layout_stack = QVBoxLayout()
        self.layout_stack.setContentsMargins(0,0,0,0)
        
        self.widget_view = self.create_widget_view()
        self.minimized_view = self.create_minimized_view()
        self.calendar_view = self.create_calendar_view()
        self.layout_stack.addWidget(self.widget_view)
        self.layout_stack.addWidget(self.minimized_view)
        self.layout_stack.addWidget(self.calendar_view)

        self.size_grip = QSizeGrip(self)
        grip_layout = QHBoxLayout()
        grip_layout.addStretch()
        grip_layout.addWidget(self.size_grip, 0, Qt.AlignBottom | Qt.AlignRight)

        main_layout.addLayout(self.layout_stack)
        main_layout.addLayout(grip_layout)

        self.set_view_mode('widget')
        
    def set_view_mode(self, mode):
        self.widget_view.hide()
        self.minimized_view.hide()
        self.calendar_view.hide()

        if mode == 'widget':
            self.is_maximized_mode = False
            self.is_minimized_mode = False
            self.widget_view.show()
            size = self.settings_manager.get("widget_size")
            self.resize(size[0], size[1])
            self.position_widget()
        elif mode == 'minimized':
            self.is_maximized_mode = False
            self.is_minimized_mode = True
            self.minimized_view.show()
            size = self.settings_manager.get("minimized_size")
            self.resize(size[0], size[1])
            self.position_widget()
        elif mode == 'calendar':
            self.is_maximized_mode = True
            self.is_minimized_mode = False
            self.calendar_view.show()
            size = self.settings_manager.get("calendar_size")
            self.resize(size[0], size[1])
            self.populate_calendar()
            self.center_window()
    
    def center_window(self):
        screen = self.screen().geometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2),
                    int((screen.height() - size.height()) / 2))

    def create_widget_view(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        time_panel = QFrame()
        time_panel.setObjectName("TimePanel")
        time_layout = QVBoxLayout(time_panel)
        time_layout.setAlignment(Qt.AlignCenter)
        self.time_label = QLabel("10:28")
        self.time_label.setObjectName("TimeLabel")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_mode_label = QLabel("Night")
        self.time_mode_label.setObjectName("TimeModeLabel")
        self.time_mode_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.time_mode_label)
        date_panel = QFrame()
        date_panel.setObjectName("DatePanel")
        date_layout = QVBoxLayout(date_panel)
        date_layout.setAlignment(Qt.AlignCenter)
        self.date_label = QLabel("Loading...")
        self.date_label.setObjectName("DateLabel")
        self.tithi_label = QLabel("...")
        self.tithi_label.setObjectName("TithiLabel")
        self.eng_date_label = QLabel("...")
        self.eng_date_label.setObjectName("EngDateLabel")
        date_layout.addWidget(self.date_label)
        date_layout.addWidget(self.tithi_label)
        date_layout.addWidget(self.eng_date_label)
        layout.addWidget(time_panel, 1)
        layout.addWidget(date_panel, 2)
        return container
    
    def create_minimized_view(self):
        container = QWidget()
        container.setObjectName("MinimizedWidget")
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(2)
        self.minimized_nep_month = QLabel("...")
        self.minimized_nep_month.setObjectName("MinimizedNepMonth")
        self.minimized_nep_month.setAlignment(Qt.AlignCenter)
        self.minimized_nep_day = QLabel("...")
        self.minimized_nep_day.setObjectName("MinimizedNepDay")
        self.minimized_nep_day.setAlignment(Qt.AlignCenter)
        self.minimized_time = QLabel("...")
        self.minimized_time.setObjectName("MinimizedTime")
        self.minimized_time.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.minimized_nep_month)
        layout.addWidget(self.minimized_nep_day)
        layout.addWidget(self.minimized_time)
        return container
    
    def create_calendar_view(self):
        container = QWidget()
        container.setObjectName("CalendarView")
        main_layout = QHBoxLayout(container)
        calendar_panel = QWidget()
        calendar_layout = QVBoxLayout(calendar_panel)
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(0)
        self.calendar_header_button = QPushButton("...")
        self.calendar_header_button.setObjectName("CalendarHeaderButton")
        self.calendar_header_button.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.calendar_header_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.calendar_header_button.clicked.connect(self.open_date_selection)
        self.gregorian_header_label = QLabel("...")
        self.gregorian_header_label.setObjectName("GregorianHeader")
        self.gregorian_header_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.calendar_header_button)
        header_layout.addWidget(self.gregorian_header_label)
        
        
        nav_layout = QHBoxLayout()
        prev_button = QPushButton("<")
        next_button = QPushButton(">")
        prev_button.clicked.connect(lambda: self.navigate_month(-1))
        next_button.clicked.connect(lambda: self.navigate_month(1))

        self.settings_button = QPushButton()
        self.settings_button.setObjectName("SettingsButton")
        self.settings_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.settings_button.setFixedSize(24, 24)
        self.settings_button.clicked.connect(self.show_settings_menu)
        
        nav_layout.addWidget(prev_button)
        nav_layout.addWidget(header_widget, 1)
        nav_layout.addWidget(next_button)
        nav_layout.addWidget(self.settings_button)

        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(5)
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(days):
            label = QLabel(day)
            label.setObjectName("CalendarWeekdayHeader")
            label.setAlignment(Qt.AlignCenter)
            self.calendar_grid.addWidget(label, 0, i)
            
        calendar_layout.addLayout(nav_layout)
        calendar_layout.addLayout(self.calendar_grid, 1)
        
        self.event_panel = QWidget()
        event_layout = QVBoxLayout(self.event_panel)
        
        event_header_label = QLabel("Events")
        event_header_label.setObjectName("EventHeader")
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.event_list_widget = QWidget()
        self.event_list_layout = QVBoxLayout(self.event_list_widget)
        self.event_list_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(self.event_list_widget)
        
        event_layout.addWidget(event_header_label)
        event_layout.addWidget(scroll_area)
        

        main_layout.addWidget(calendar_panel, 2)
        main_layout.addWidget(self.event_panel, 1)
        return container

    def update_time_and_display(self):
        now = datetime.now(self.nepali_timezone)
        time_str = now.strftime("%I:%M")
        ampm_str = now.strftime("%p")
        self.time_label.setText(time_str)
        self.minimized_time.setText(f"{time_str} {ampm_str}")
        hour = now.hour
        mode = "Night"
        if 5 <= hour < 12: 
            mode = "Morning"
        elif 12 <= hour < 17: 
            mode = "Afternoon"
        elif 17 <= hour < 21: 
            mode = "Evening"
        self.time_mode_label.setText(mode)
        today_str = now.strftime("%Y-%m-%d")
        if not hasattr(self, 'last_updated_day') or self.last_updated_day != today_str:
            self.today_gregorian_str = today_str
            self.update_date_display()
            self.last_updated_day = today_str
    
    def update_date_display(self):
        data = self.data_manager.get_data_for_date(self.today_gregorian_str)
        
        is_holiday_today = data.get("is_holiday", False) if data else False
        self.main_frame.setProperty("isHolidayToday", is_holiday_today)
        self.main_frame.style().unpolish(self.main_frame)
        self.main_frame.style().polish(self.main_frame)

        if not data: 
            self.date_label.setText("No Data")
            return
        self.date_label.setText(f"{data['weekday'][:3]}, {data['nepali_day']} {data['nepali_month']}")
        self.tithi_label.setText(data['tithi'])
        eng_date = datetime.strptime(data['gregorian_date'], "%Y-%m-%d")
        self.eng_date_label.setText(eng_date.strftime("%b %d, %Y"))
        self.minimized_nep_month.setText(data['nepali_month'])
        self.minimized_nep_day.setText(str(data['nepali_day']))
        if self.is_maximized_mode: 
            self.populate_calendar()
    
    def populate_calendar(self):
        for i in reversed(range(self.calendar_grid.count())): 
            item = self.calendar_grid.itemAt(i)
            if item and item.widget() and not item.widget().objectName() == "CalendarWeekdayHeader": 
                item.widget().setParent(None)
        for i in reversed(range(self.event_list_layout.count())): 
            self.event_list_layout.itemAt(i).widget().setParent(None)
        month_data = self.data_manager.get_data_for_nepali_month(self.current_calendar_nep_year, self.current_calendar_nep_month_index)
        if not month_data: 
            self.calendar_header_button.setText("No Data")
            self.gregorian_header_label.setText("")
            return
        month_name = month_data[0]['nepali_month']
        self.calendar_header_button.setText(f"{month_name} {self.current_calendar_nep_year}")
        start_greg = datetime.strptime(month_data[0]['gregorian_date'], "%Y-%m-%d")
        end_greg = datetime.strptime(month_data[-1]['gregorian_date'], "%Y-%m-%d")
        self.gregorian_header_label.setText(f"{start_greg.strftime('%b')} - {end_greg.strftime('%b %Y')}")
        first_day_data = month_data[0]
        weekday_of_first = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].index(first_day_data['weekday'][:3])
        events_in_month = False
        for data in month_data:
            data['is_today'] = data['gregorian_date'] == self.today_gregorian_str
            day_widget = DayWidget(data)
            day_widget.clicked.connect(self.show_day_detail)
            row = (data['nepali_day'] + weekday_of_first - 1) // 7 + 1
            col = (data['nepali_day'] + weekday_of_first - 1) % 7
            self.calendar_grid.addWidget(day_widget, row, col)
            if data['events']:
                events_in_month = True
                event_label = QLabel(f"<b>{data['nepali_day']} {month_name}:</b> {', '.join(data['events'])}")
                event_label.setObjectName("EventListLabel")
                event_label.setWordWrap(True)
                self.event_list_layout.addWidget(event_label)
        if not events_in_month:
            self.event_list_layout.addWidget(QLabel("<i>No events this month.</i>"))
            self.event_list_layout.addWidget(QLabel("<b>Upcoming Events:</b>"))
            upcoming = self.data_manager.get_upcoming_events(month_data[-1]['gregorian_date'])
            for data in upcoming:
                event_label = QLabel(f"<b>{data['nepali_day']} {data['nepali_month']}:</b> {', '.join(data['events'])}")
                event_label.setObjectName("EventListLabel")
                event_label.setWordWrap(True)
                self.event_list_layout.addWidget(event_label)
    
    def navigate_month(self, direction):
        self.current_calendar_nep_month_index += direction
        if self.current_calendar_nep_month_index > 11: 
            self.current_calendar_nep_month_index = 0
            self.current_calendar_nep_year += 1
        elif self.current_calendar_nep_month_index < 0: 
            self.current_calendar_nep_month_index = 11
            self.current_calendar_nep_year -= 1
        self.populate_calendar()
    
    def open_date_selection(self):
        dialog = DateSelectionDialog(self.current_calendar_nep_year, self.current_calendar_nep_month_index, self)
        dialog.date_selected.connect(self.jump_to_date)
        dialog.exec()
    
    def jump_to_date(self, year, month_index):
        self.current_calendar_nep_year = year
        self.current_calendar_nep_month_index = month_index
        self.populate_calendar()
    
    def show_day_detail(self, day_data, day_widget_ref=None):
        if self.active_day_detail_dialog and self.active_day_detail_dialog.isVisible():
            self.active_day_detail_dialog.close()

        dialog = DayDetailDialog(day_data, self)
        self.active_day_detail_dialog = dialog
        
        day_widget = day_widget_ref if day_widget_ref else self.sender()
        if day_widget:
            global_pos = day_widget.mapToGlobal(QPoint(0, day_widget.height()))
            dialog.move(global_pos)
        
        dialog.show()
    
    def quit_application(self):
        self.settings_manager.save_reminders(self.reminders)
        self.is_quitting = True
        self.tray_icon.hide()
        QApplication.instance().quit()
    
    def toggle_event_widget(self):
        if self.event_widget and self.event_widget.isVisible():
            self.event_widget.close()
            self.event_widget = None
        else:
            today_data = self.data_manager.get_data_for_date(self.today_gregorian_str)
            if not today_data: return
            
            self.event_widget = EventWidget(self)
            self.event_widget.setStyleSheet(self.styleSheet())
            self.event_widget.update_events(today_data.get('events', []))
            
            main_pos = self.pos()
            self.event_widget.move(main_pos.x(), main_pos.y() + self.height() + 10)
            self.event_widget.show()
    
    def show_date_tools(self):
        dialog = DateToolsDialog(self.data_manager, self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()

    def show_reminders(self):
        dialog = RemindersDialog(self.reminders, self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()
        self.reminders = dialog.get_updated_reminders()
        self.settings_manager.save_reminders(self.reminders)
    
    def check_reminders(self):
        now = datetime.now(pytz.timezone('Asia/Kathmandu'))
        due_reminders = []
        
        for reminder in self.reminders[:]:
            reminder_time = datetime.fromisoformat(reminder['time'])
            if reminder_time <= now:
                due_reminders.append(reminder)
                self.reminders.remove(reminder)

        if due_reminders:
            for reminder in due_reminders:
                self.trigger_reminder_alert(reminder)
            self.settings_manager.save_reminders(self.reminders)

    def trigger_reminder_alert(self, reminder):
        QApplication.beep()

        alert = ReminderAlert(reminder['text'], self)
        alert.setStyleSheet(self.styleSheet())
        alert.move(self.screen().geometry().center() - alert.rect().center() + QPoint(len(self.active_alerts) * 20, len(self.active_alerts) * 20))
        alert.show()
        self.active_alerts.append(alert)
        alert.finished.connect(lambda: self.active_alerts.remove(alert))

    def create_system_tray_icon(self):
        icon_path = "src/ui/icon.png"
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        menu = QMenu()
        show_action = QAction("Show Widget", self)
        show_action.triggered.connect(self.showNormal)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
    
    def position_widget(self):
        placement = self.settings_manager.get("widget_placement")
        screen_geo = self.screen().availableGeometry()
        widget_size = self.size()
        
        if placement == "Free":
            pos = self.settings_manager.get("widget_position")
            if pos:
                self.move(QPoint(pos[0], pos[1]))
            else:
                self.move(screen_geo.width() - widget_size.width() - 10, screen_geo.height() - widget_size.height() - 10)
        elif placement == "Top-Right":
            self.move(screen_geo.width() - widget_size.width() - 10, 10)
        elif placement == "Bottom-Right":
            self.move(screen_geo.width() - widget_size.width() - 10, screen_geo.height() - widget_size.height() - 40)
        elif placement == "Top-Left":
            self.move(10, 10)
        elif placement == "Bottom-Left":
            self.move(10, screen_geo.height() - widget_size.height() - 40)
    
    def apply_theme(self):
        theme = self.settings_manager.get("theme")
        self.setStyleSheet(DARK_THEME_STYLESHEET if theme == "Dark" else LIGHT_THEME_STYLESHEET)
    
    def update_resize_policy(self):
        if self.settings_manager.get("resizing_enabled"):
            self.size_grip.show()
        else:
            self.size_grip.hide()
        self.set_view_mode('widget' if not self.is_maximized_mode and not self.is_minimized_mode else
                        'minimized' if self.is_minimized_mode else 'calendar')
    
    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec(): 
            self.theme_changed.emit()
            self.update_resize_policy()
            self.position_widget()
            self.trigger_sync(force=False)
    
    def trigger_sync(self, force=False):
        start = self.settings_manager.get("sync_start_year")
        end = self.settings_manager.get("sync_end_year")
        self.start_sync_signal.emit(start, end, force)
    
    def update_sync_status(self, message): 
        print(f"Sync: {message}")
    
    def on_sync_finished(self):
        print("Sync complete. Data reloaded.")
        today_data = self.data_manager.get_data_for_date(self.today_gregorian_str)
        if today_data: 
            self.current_calendar_nep_year = today_data['nepali_year']
            self.current_calendar_nep_month_index = today_data['nepali_month_index']
        self.update_date_display()
    
    def jump_to_today(self):
        today_data = self.data_manager.get_data_for_date(self.today_gregorian_str)
        if today_data:
            self.current_calendar_nep_year = today_data['nepali_year']
            self.current_calendar_nep_month_index = today_data['nepali_month_index']
            self.populate_calendar()

            QApplication.processEvents()
            for i in range(self.calendar_grid.count()):
                widget = self.calendar_grid.itemAt(i).widget()
                if isinstance(widget, DayWidget) and widget.day_data.get('is_today', False):
                    self.show_day_detail(widget.day_data, day_widget_ref=widget)
                    break

    def toggle_event_panel(self):
        self.is_event_panel_visible = not self.is_event_panel_visible
        
        calendar_size = self.settings_manager.get("calendar_size")
        
        if self.is_event_panel_visible:
            self.event_panel.show()
            self.resize(calendar_size[0], calendar_size[1])
        else:
            self.event_panel.hide()
            collapsed_width = int(calendar_size[0] * 0.65)
            self.resize(collapsed_width, calendar_size[1])
            
        self.center_window()

    def show_settings_menu(self):
        menu = QMenu(self)
        
        sync_action = menu.addAction("Force Resync")
        settings_action = menu.addAction("Settings...")
        menu.addSeparator()
        show_today_action = menu.addAction("Show Today")
        toggle_events_text = "Hide Events Box" if self.is_event_panel_visible else "Show Events Box"
        toggle_events_action = menu.addAction(toggle_events_text)
        menu.addSeparator()

        tools_action = menu.addAction("Date Tools...")
        reminders_action = menu.addAction("Reminders...")
        
        action = menu.exec(self.settings_button.mapToGlobal(QPoint(0, self.settings_button.height())))
        
        if action == sync_action: 
            self.trigger_sync(force=True)
        elif action == settings_action: 
            self.open_settings()
        elif action == show_today_action:
            self.jump_to_today()
        elif action == toggle_events_action:
            self.toggle_event_panel()
        elif action == tools_action:
            self.show_date_tools()
        elif action == reminders_action:
            self.show_reminders()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.settings_manager.get("widget_placement") == "Free":
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging and event.buttons() == Qt.LeftButton and self.settings_manager.get("widget_placement") == "Free": 
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.is_dragging and self.settings_manager.get("widget_placement") == "Free":
            self.is_dragging = False
            if not self.is_maximized_mode: 
                pos = self.pos()
                self.settings_manager.set("widget_position", (pos.x(), pos.y()))
            event.accept()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.settings_manager.get("resizing_enabled"):
            new_size = [self.width(), self.height()]
            if self.is_maximized_mode:
                self.settings_manager.set("calendar_size", new_size)
            elif self.is_minimized_mode:
                self.settings_manager.set("minimized_size", new_size)
            else:
                self.settings_manager.set("widget_size", new_size)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.set_view_mode('calendar' if not self.is_maximized_mode else 'widget')
        event.accept()
    
    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        toggle_view_action = context_menu.addAction("Show Calendar" if not self.is_maximized_mode else "Show Widget")
        minimize_action = context_menu.addAction("Minimize Widget" if not self.is_minimized_mode else "Restore Widget")
        
        event_widget_text = "Hide Event Widget" if self.event_widget and self.event_widget.isVisible() else "Show Event Widget"
        toggle_event_widget_action = context_menu.addAction(event_widget_text)
        
        context_menu.addSeparator()
        quit_action = context_menu.addAction("Quit")
        
        action = context_menu.exec(self.mapToGlobal(event.pos()))
        
        if action == toggle_view_action: 
            self.mouseDoubleClickEvent(event)
        elif action == minimize_action: 
            self.set_view_mode('minimized' if not self.is_minimized_mode else 'widget')
        elif action == toggle_event_widget_action:
            self.toggle_event_widget()
        elif action == quit_action: 
            self.quit_application()
    
    def closeEvent(self, event):
        if self.is_quitting:
            event.accept()
        else:
            event.ignore()
            self.hide()
