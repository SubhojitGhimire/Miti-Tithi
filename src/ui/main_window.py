import sys
import json
import pytz
import platform
from PySide6.QtWidgets import QStyle
from datetime import datetime, timedelta

from src.data_manager import DataManager
from src.settings_manager import SettingsManager

from PySide6.QtCore import Qt, QTimer, QPoint, QThread, Signal, QSize
from PySide6.QtGui import QIcon, QAction, QScreen, QPainter, QColor, QFont, QMouseEvent, QCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QSystemTrayIcon, QMenu, QDialog, QDialogButtonBox,
                               QComboBox, QGridLayout, QScrollArea, QPushButton, QListWidget,
                               QListWidgetItem, QSpinBox, QCheckBox, QStyle)

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
        self.startup_checkbox = QCheckBox("Run automatically on Windows startup")
        if platform.system() == "Windows": 
            self.startup_checkbox.setChecked(self.settings_manager.get("run_on_startup"))
        else: 
            self.startup_checkbox.setEnabled(False)
        self.startup_checkbox.setToolTip("This feature is only available on Windows.")
        layout.addWidget(self.startup_checkbox)
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
    def accept(self):
        self.settings_manager.set("theme", self.theme_combo.currentText())
        if platform.system() == "Windows": 
            self.settings_manager.set_startup(self.startup_checkbox.isChecked())
        self.settings_manager.set("sync_start_year", self.start_year_spin.value())
        self.settings_manager.set("sync_end_year", self.end_year_spin.value())
        super().accept()

class MainWindow(QMainWindow):
    start_sync_signal = Signal(int, int)
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
        self.force_sync()
    
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
        self.layout_stack = QVBoxLayout(self.main_frame)
        self.layout_stack.setContentsMargins(0,0,0,0)
        self.widget_view = self.create_widget_view()
        self.minimized_view = self.create_minimized_view()
        self.calendar_view = self.create_calendar_view()
        self.layout_stack.addWidget(self.widget_view)
        self.layout_stack.addWidget(self.minimized_view)
        self.layout_stack.addWidget(self.calendar_view)
        self.set_view_mode('widget')
        
    def set_view_mode(self, mode):
        self.widget_view.hide()
        self.minimized_view.hide()
        self.calendar_view.hide()
        if mode == 'widget':
            self.is_maximized_mode = False
            self.is_minimized_mode = False
            self.widget_view.show()
            self.setFixedSize(260, 80)
        elif mode == 'minimized':
            self.is_maximized_mode = False
            self.is_minimized_mode = True
            self.minimized_view.show()
            self.setFixedSize(80, 80)
        elif mode == 'calendar':
            self.is_maximized_mode = True
            self.is_minimized_mode = False
            self.calendar_view.show()
            self.setFixedSize(800, 550)
            self.populate_calendar()
    
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
        nav_layout.addWidget(prev_button)
        nav_layout.addWidget(header_widget, 1)
        nav_layout.addWidget(next_button)
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
        event_panel = QWidget()
        event_layout = QVBoxLayout(event_panel)
        event_header_layout = QHBoxLayout()
        event_header_label = QLabel("Events")
        event_header_label.setObjectName("EventHeader")
        self.settings_button = QPushButton()
        self.settings_button.setObjectName("SettingsButton")
        self.settings_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.settings_button.setFixedSize(24,24)
        self.settings_button.clicked.connect(self.show_settings_menu)
        event_header_layout.addWidget(event_header_label)
        event_header_layout.addStretch()
        event_header_layout.addWidget(self.settings_button)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.event_list_widget = QWidget()
        self.event_list_layout = QVBoxLayout(self.event_list_widget)
        self.event_list_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(self.event_list_widget)
        event_layout.addLayout(event_header_layout)
        event_layout.addWidget(scroll_area)
        main_layout.addWidget(calendar_panel, 2)
        main_layout.addWidget(event_panel, 1)
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
    
    def show_day_detail(self, day_data):
        dialog = DayDetailDialog(day_data, self)
        day_widget = self.sender()
        global_pos = day_widget.mapToGlobal(QPoint(0, day_widget.height()))
        dialog.move(global_pos)
        dialog.exec()
    
    def create_system_tray_icon(self):
        icon_path = "src/ui/icon.png"
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        menu = QMenu()
        show_action = QAction("Show Widget", self)
        show_action.triggered.connect(self.showNormal)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
    
    def position_widget(self):
        pos = self.settings_manager.get("widget_position")
        if pos: 
            self.move(QPoint(pos[0], pos[1]))
        else: 
            screen_geo = self.screen().availableGeometry()
            self.move(screen_geo.width() - self.width() - 10, screen_geo.height() - self.height() - 10)
    
    def apply_theme(self):
        theme = self.settings_manager.get("theme")
        self.setStyleSheet(DARK_THEME_STYLESHEET if theme == "Dark" else LIGHT_THEME_STYLESHEET)
    
    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec(): 
            self.theme_changed.emit()
        self.force_sync()
    
    def force_sync(self):
        start = self.settings_manager.get("sync_start_year")
        end = self.settings_manager.get("sync_end_year")
        self.start_sync_signal.emit(start, end)
    
    def update_sync_status(self, message): 
        print(f"Sync: {message}")
    
    def on_sync_finished(self):
        print("Sync complete. Data reloaded.")
        today_data = self.data_manager.get_data_for_date(self.today_gregorian_str)
        if today_data: 
            self.current_calendar_nep_year = today_data['nepali_year']
            self.current_calendar_nep_month_index = today_data['nepali_month_index']
        self.update_date_display()
    
    def show_settings_menu(self):
        menu = QMenu(self)
        sync_action = menu.addAction("Sync Now")
        settings_action = menu.addAction("Settings...")
        action = menu.exec(self.settings_button.mapToGlobal(QPoint(0, self.settings_button.height())))
        if action == sync_action: 
            self.force_sync()
        elif action == settings_action: 
            self.open_settings()
    
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
        if not self.is_maximized_mode: 
            pos = self.pos()
            self.settings_manager.set("widget_position", (pos.x(), pos.y()))
        event.accept()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.set_view_mode('calendar' if not self.is_maximized_mode else 'widget')
        event.accept()
    
    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        toggle_view_action = context_menu.addAction("Show Calendar" if not self.is_maximized_mode else "Show Widget")
        minimize_action = context_menu.addAction("Minimize Widget" if not self.is_minimized_mode else "Restore Widget")
        quit_action = context_menu.addAction("Quit")
        action = context_menu.exec(self.mapToGlobal(event.pos()))
        if action == toggle_view_action: 
            self.mouseDoubleClickEvent(event)
        elif action == minimize_action: 
            self.set_view_mode('minimized' if not self.is_minimized_mode else 'widget')
        elif action == quit_action: 
            QApplication.instance().quit()
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("Nepali Calendar Widget", "The application is still running in the system tray.", QSystemTrayIcon.Information, 2000)
