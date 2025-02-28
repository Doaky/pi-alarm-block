from typing import List
import uuid

class Alarm:
    def __init__(self, id: str, hour: int, minute: int, days: List[int], is_primary_schedule: bool, active: bool):
        self.id = id if id else str(uuid.uuid4())
        self.hour = hour
        self.minute = minute
        self.days = days
        self.is_primary_schedule = is_primary_schedule
        self.active = active

    def to_dict(self) -> dict:
        """Convert the Alarm object to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "hour": self.hour,
            "minute": self.minute,
            "days": self.days,
            "is_primary_schedule": self.is_primary_schedule,
            "active": self.active
        }

    @classmethod
    def from_dict(cls, alarm_dict: dict):
        """Create an Alarm object from a dictionary loaded from JSON."""
        return cls(
            alarm_dict["id"],
            alarm_dict["hour"],
            alarm_dict["minute"],
            alarm_dict["days"],
            alarm_dict["is_primary_schedule"],
            alarm_dict["active"])

    def __repr__(self):
        """Return a string representation of the Alarm object."""
        return f"Alarm(id: {self.id}, time: {self.hour}:{self.minute}, days: {self.days}, primary: {self.is_primary_schedule}, active: {self.active})"
