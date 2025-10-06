import re
import os
import json
import pytz
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class CalendarScraper:
    BASE_URL = "https://www.ashesh.com.np/nepali-calendar/"
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    HOLIDAY_COLOR = "#FF4D00"
    NEPALI_MONTHS_LIST = [
        "Baishakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin", 
        "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
    ]
    NEPALI_MONTHS_MAP = {name: f"{i+1:02d}" for i, name in enumerate(NEPALI_MONTHS_LIST)}
    NEPALI_MONTHS_ALIAS = {
    "Baishakh": ["Baishakh", "Baisakh", "Baisakh"],
    "Jestha": ["Jestha", "Jeth", "Jeshtha", "Jestha"],
    "Ashadh": ["Ashadh", "Asar", "Ashar", "Ashaar", "Aashadh"],
    "Shrawan": ["Shrawan", "Shawn", "Saaun", "Srawan"],
    "Bhadra": ["Bhadra", "Bhadaau", "Bhaadra"],
    "Ashwin": ["Ashwin", "Asoj", "Ashvin"],
    "Kartik": ["Kartik", "Kaattik", "Kartika"],
    "Mangsir": ["Mangsir", "Mangshir", "Maarga"],
    "Poush": ["Poush", "Paush", "Push"],
    "Magh": ["Magh", "Magghe"],
    "Falgun": ["Falgun", "Faagun", "Faalgun"],
    "Chaitra": ["Chaitra", "Chait"]
    }
    ENGLISH_MONTHS_MAP = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    DAYS_IN_MONTH = {
        1: 31,  # January
        2: 28,  # February (we'll adjust for leap years below)
        3: 31,  # March
        4: 30,  # April
        5: 31,  # May
        6: 30,  # June
        7: 31,  # July
        8: 31,  # August
        9: 30,  # September
        10: 31,  # October
        11: 30,  # November
        12: 31   # December
    }
    
    def __adjust_for_english_date(self, days_data, english_month, english_year):
        def __is_leap_year(year):
            year = int(year)
            return year%4==0 and (year % 100 != 0 or year % 400 == 0)
        self.DAYS_IN_MONTH[2] = 29 if __is_leap_year(english_year) else 28

        monthly_data_list = []
        for nepali_day in days_data.keys():
            english_day = days_data[nepali_day]["gregorian_date_placeholder"]
            if english_day > self.DAYS_IN_MONTH[english_month]:
                english_day = english_day - self.DAYS_IN_MONTH[english_month-1] if english_month > 1 else english_day - 31
            english_date = f"{english_day:02d}-{english_month:02d}-{english_year}"
            english_date = datetime.strptime(english_date, r"%d-%m-%Y")
            del(days_data[nepali_day]["gregorian_date_placeholder"])
            days_data[nepali_day]["gregorian_date"] = english_date.strftime(r"%Y-%m-%d")
            days_data[nepali_day]["gregorian_date_expanded"] = english_date.strftime(r"%d %B, %Y")
            if english_day == self.DAYS_IN_MONTH[english_month]:
                english_month += 1
                if english_month == 13:
                    english_month = 1
                    english_year = f"{int(english_year)+1}"
            monthly_data_list.append(days_data[nepali_day])
        return monthly_data_list
    
    def __get_page_content(self, year, month):
        try:
            time.sleep(2)
            url = f"{self.BASE_URL}?year={year}&month={month}"
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching data for {month} {year}: {e}")
            return None
    
    def __comb_through_alias(self, month_name):
        for this_month in self.NEPALI_MONTHS_ALIAS.keys():
            if month_name in self.NEPALI_MONTHS_ALIAS[this_month]:
                return this_month
        return month_name
    
    def scrape_month(self, year, month_name, month_index):
        try:
            html = self.__get_page_content(year, month_name)
            if not html: return {}
            soup = BeautifulSoup(html, 'html.parser')

            date_header = soup.find("div", class_="cal_left").get_text().strip()
            month_year = date_header.split()
            year = month_year[1]
            month_text = month_year[0].title()
            if month_text not in self.NEPALI_MONTHS_LIST:
                month_text = self.__comb_through_alias(month_text)

            days_data = {}
            calendar_table = soup.find('table', id='calendartable')
            for row in calendar_table.find_all('tr')[2:]:
                cells = row.find_all('td')
                for cell in cells:
                    day = cell.find("div", class_="date_np")
                    events = []
                    if day:
                        english_day = cell.find("div", class_="date_en")
                        tithi = cell.find("div", class_="tithi").get_text().strip()
                        weekday = cells.index(cell)
                        holiday = (weekday==6) or (str(day.get('style')).replace(" ","")==f"color:{self.HOLIDAY_COLOR}")
                        
                        event1 = cell.find("div", class_="event_one").get_text().strip()
                        if event1:
                            events.append(event1)
                        event2 = cell.find("div", class_="rotate_left").get_text().strip()
                        if event2:
                            events.append(event2)
                        event3 = cell.find("div", class_="rotate_right").get_text().strip()
                        if event3:
                            events.append(event3)
                        if month_index==2 and day.get_text().strip()=='11':   events.append("सुभोजितको जन्मदिन")
                        
                        days_data[int(day.get_text().strip())] = {
                            "gregorian_date": None,
                            "gregorian_date_expanded": None,
                            "nepali_date": f"{year}-{self.NEPALI_MONTHS_MAP[month_text]}-{int(day.get_text().strip()):02d}",
                            "nepali_date_expanded": f"{int(day.get_text().strip()):02d} {month_text}, {year}",
                            "nepali_year": int(year),
                            "nepali_month": month_text,
                            "nepali_month_index": month_index,
                            "nepali_day": int(day.get_text().strip()),
                            "weekday": self.WEEKDAYS[weekday],
                            "tithi": tithi,
                            "is_holiday": holiday,
                            "events": list(set(events)),
                            "gregorian_date_placeholder": int(english_day.get_text().strip())
                        }
            days_data = dict(sorted(days_data.items()))

            english_date_header = soup.find('div', class_='cal_right').get_text().strip()  
            english_month = self.ENGLISH_MONTHS_MAP[re.match(r"([A-Za-z]+)", english_date_header).group(1).title()] 
            english_year = re.match(r"[^0-9]+(\d{4})", english_date_header).group(1) 

            monthly_data_list = self.__adjust_for_english_date(days_data, english_month, english_year)
            monthly_data = {}
            for daily_data in monthly_data_list:
                monthly_data[daily_data["gregorian_date"]] = daily_data
            
            return monthly_data
        except Exception as e:
            print(f"Failed to scrape {month_name} {year}: {e}")
            return {}
