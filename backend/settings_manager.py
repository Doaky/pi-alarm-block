import json

class SettingsManager:
    def __init__(self, file_path="data/settings.json"):
        self.file_path = file_path
        self.settings = self.load_settings()

    def load_settings(self):
        """Load settings from JSON file."""
        try:
            with open(self.file_path, "r") as file:
                settings = json.load(file)
                print(f"Settings loaded: {settings}")
                return settings
        except (OSError):
            print("Could not open/read file: ", self.file_path,"\n Defaulting to Primary/On")
            return {"schedule": "Primary", "global_status": "On"}

    def save_settings(self, settings):
        """Save settings to JSON file."""
        try:
            with open(self.file_path, "w") as file:
                json.dump(settings, file, indent=4)
            self.settings = settings
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_is_primary_schedule(self):
        """Return the current alarm schedule."""
        return self.settings.get("is_primary_schedule")

    def set_is_primary_schedule(self, is_primary):
        """Sets the alarm schedule."""
        self.settings["is_primary_schedule"] = is_primary
        self.save_settings(self.settings)

    def get_is_global_on(self):
        """Return the global alarm status."""
        return self.settings.get("is_global_on")

    def set_is_global_on(self, is_on):
        """Sets the global alarm status."""
        self.settings["is_global_on"] = is_on
        self.save_settings(self.settings)
