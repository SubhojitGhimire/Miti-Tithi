import os
import sys
import json
import platform

class SettingsManager:
    def __init__(self, app_name="NepaliCalendarDesktopWidget"):
        if platform.system() == "Windows":
            self.settings_dir = os.path.join(os.environ['APPDATA'], app_name)
        else:
            self.settings_dir = os.path.join(os.path.expanduser("~"), '.config', app_name)
        
        os.makedirs(self.settings_dir, exist_ok=True)
        self.settings_file = os.path.join(self.settings_dir, "settings.json")
        self.app_name = app_name
        self.settings = self._load_settings()

    def _get_default_settings(self):
        return {
            "run_on_startup": False,
            "theme": "Light",
            "sync_start_year": 2070,
            "sync_end_year": 2090,
            "widget_position": None
        }

    def _load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                defaults = self._get_default_settings()
                defaults.update(settings)
                return defaults
        except (FileNotFoundError, json.JSONDecodeError):
            return self._get_default_settings()

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key):
        return self.settings.get(key)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def set_startup(self, enable):
        if platform.system() != "Windows":
            print("Run on startup is only supported on Windows.")
            return

        import winreg
        
        app_path = os.path.abspath(sys.argv[0])
        run_command = f'"{sys.executable}" "{app_path}"'
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, run_command)
                else:
                    winreg.DeleteValue(key, self.app_name)
            self.set("run_on_startup", enable)
        except FileNotFoundError:
             if not enable:
                 print("Already removed from startup or key not found.")
             else:
                 print("Error: Could not find the startup registry key.")
        except Exception as e:
            print(f"Failed to set startup preference: {e}")

