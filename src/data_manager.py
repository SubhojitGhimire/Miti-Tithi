import os
import json
import time
from datetime import datetime
from src.scraper import CalendarScraper
from PySide6.QtCore import QObject, Signal, Slot

class DataManager(QObject):
    sync_progress = Signal(str)
    sync_finished = Signal()

    def __init__(self, data_dir="data"):
        super().__init__()
        self.data_dir = data_dir
        self.calendar_data = {}
        self.sorted_dates = []
        self.scraper = CalendarScraper()
        self.nepali_to_gregorian_map = {}
        os.makedirs(self.data_dir, exist_ok=True)
        self.load_all_data()

    def get_data_for_date(self, date_str):
        return self.calendar_data.get(date_str)

    def lookup_bs_to_ad(self, year, month_index, day):
        key = f"{year}-{month_index + 1:02d}-{day:02d}"
        return self.nepali_to_gregorian_map.get(key)
    
    def get_data_for_nepali_month(self, year, month_index):
        month_days = []
        for date_str in self.sorted_dates:
            data = self.calendar_data[date_str]
            if data.get('nepali_year') == year and data.get('nepali_month_index') == month_index:
                month_days.append(data)
        return month_days

    def get_upcoming_events(self, from_date_str, limit=10):
        upcoming_events = []
        try:
            start_index = self.sorted_dates.index(from_date_str)
        except ValueError:
            start_index = 0

        for date_str in self.sorted_dates[start_index:]:
            data = self.calendar_data[date_str]
            if data.get('events'):
                upcoming_events.append(data)
            if len(upcoming_events) >= limit:
                break
        return upcoming_events

    def load_all_data(self):
        self.calendar_data = {}
        self.nepali_to_gregorian_map = {}
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".jsonl"):
                try:
                    with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                        for line in f:
                            data_dict = json.loads(line)
                            self.calendar_data.update(data_dict)
                            for greg_date, nep_data in data_dict.items():
                                key = f"{nep_data['nepali_year']}-{nep_data['nepali_month_index'] + 1:02d}-{nep_data['nepali_day']:02d}"
                                self.nepali_to_gregorian_map[key] = nep_data
                except (json.JSONDecodeError, IndexError):
                    print(f"Warning: Could not parse or invalid filename: {filename}")
        
        self.sorted_dates = sorted(self.calendar_data.keys())
        print(f"Loaded {len(self.calendar_data)} days of data. Mapped {len(self.nepali_to_gregorian_map)} BS dates.")

    @Slot(int, int, bool)
    def run_sync(self, start_year, end_year, force=False):
        for year in range(start_year, end_year + 1):
            year_data_path = os.path.join(self.data_dir, f"calendar_{year}.jsonl")

            if os.path.exists(year_data_path) and not force:
                self.sync_progress.emit(f"Data for {year} B.S. exists. Skipping sync.")
                continue
            
            if force:
                self.sync_progress.emit(f"Force resyncing data for {year} B.S....")

            all_year_data = {}
            for i, month_name in enumerate(self.scraper.NEPALI_MONTHS_LIST):
                self.sync_progress.emit(f"Fetching {month_name} {year}...")
                month_data = self.scraper.scrape_month(year, month_name, i)
                if month_data:
                    all_year_data.update(month_data)
                else:
                    self.sync_progress.emit(f"Failed {month_name} {year}. Retrying...")
                    time.sleep(5)
                    month_data = self.scraper.scrape_month(year, month_name, i)
                    if month_data:
                        all_year_data.update(month_data)

                time.sleep(1)

            if all_year_data:
                with open(year_data_path, 'w', encoding='utf-8') as f:
                    for key, value in all_year_data.items():
                        json.dump({key:value}, f, ensure_ascii=False)
                        f.write("\n")
                self.sync_progress.emit(f"Saved data for {year} B.S.")

        self.load_all_data()
        self.sync_finished.emit()
