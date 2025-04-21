from datetime import time
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Dict, Literal, Set, List, Optional

DAY_ABBREVS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

class AlarmBase(BaseModel):
    """Base Pydantic model for alarm validation."""
    model_config = ConfigDict(
        from_attributes=True, 
        json_encoders={
            time: lambda v: v.strftime("%H:%M")
        },
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "hour": 7,
                "minute": 30,
                "days": [0, 1, 2, 3, 4],  # Monday-Friday as integers
                "schedule": "a",
                "active": True
            }
        }
    )
    
    id: str = Field(..., description="Unique identifier for the alarm")
    hour: int = Field(..., ge=0, le=23, description="Hour of the alarm (0-23)")
    minute: int = Field(..., ge=0, le=59, description="Minute of the alarm (0-59)")
    days: Set[int] = Field(
        ..., 
        min_items=1, 
        max_items=7, 
        description="Days of the week (0=Monday, 6=Sunday)"
    )
    
    @field_validator('days', mode='before')
    def convert_days_to_set(cls, v):
        """Convert lists to sets for days field"""
        if isinstance(v, list):
            return set(v)
        return v
        
    @field_validator('days', mode='after')
    def validate_days_range(cls, v):
        """Validate that days are in the correct range"""
        for day in v:
            if day < 0 or day > 6:
                raise ValueError(f"Day {day} is out of range (0-6)")
        return v
    schedule: Literal["a", "b"] = Field(
        "a",  # Default to "a"
        description="Schedule type ('a' or 'b')"
    )
    active: bool = Field(
        default=True,
        description="Whether the alarm is active"
    )

    def get_time(self) -> time:
        """Get the alarm time as a datetime.time object."""
        return time(hour=self.hour, minute=self.minute)

class Alarm:
    """
    Domain model representing an alarm with business logic.
    
    This class wraps the AlarmBase Pydantic model and provides
    additional methods for serialization, deserialization, and
    business operations.
    
    Attributes:
        id (str): Unique identifier for the alarm
        hour (int): Hour of the alarm (0-23)
        minute (int): Minute of the alarm (0-59)
        days (Set[int]): Days of the week the alarm is active (0=Monday, 6=Sunday)
        schedule (Literal["a", "b"]): schedule type
        active (bool): Whether the alarm is currently active
    """
    
    def to_response_model(self) -> dict:
        """Convert this Alarm to a dictionary compatible with AlarmBase.
        
        Returns:
            dict: A dictionary representation of this alarm
        """
        return {
            "id": self.id,
            "hour": self.hour,
            "minute": self.minute,
            "days": list(self.days),  # Convert set to list for JSON serialization
            "schedule": self.schedule,
            "active": self.active
        }

    def __init__(
        self,
        id: str,
        hour: int,
        minute: int,
        days: Set[int],
        schedule: Literal["a", "b"],
        active: bool = True
    ):
        """
        Initialize a new Alarm instance with validation.
        
        Args:
            id: Unique identifier for the alarm
            hour: Hour of the alarm (0-23)
            minute: Minute of the alarm (0-59)
            days: Set of days the alarm is active (0=Monday, 6=Sunday)
            schedule: Literal["a", "b"]
            active: Whether the alarm is active (default: True)
            
        Raises:
            ValueError: If any of the input values are invalid
        """
        # Create Pydantic model for validation
        alarm_data = AlarmBase(
            id=id,
            hour=hour,
            minute=minute,
            days=days,
            schedule=schedule,
            active=active
        )
        
        # Set validated values
        self.id = alarm_data.id
        self.hour = alarm_data.hour
        self.minute = alarm_data.minute
        self.days = alarm_data.days
        self.schedule = alarm_data.schedule
        self.active = alarm_data.active

    def to_dict(self) -> Dict[str, object]:
        """
        Convert the Alarm object to a dictionary for JSON serialization.
        
        Returns:
            Dict[str, object]: Dictionary representation of the alarm
        """
        return {
            "id": self.id,
            "hour": self.hour,
            "minute": self.minute,
            "days": list(self.days),  # Ensure JSON-serializable
            "schedule": self.schedule,
            "active": self.active
        }

    @classmethod
    def from_dict(cls, alarm_dict: Dict[str, object]) -> "Alarm":
        """
        Create an Alarm object from a dictionary loaded from JSON.
        
        Args:
            alarm_dict: Dictionary containing alarm data
            
        Returns:
            Alarm: New Alarm instance
            
        Raises:
            ValueError: If the dictionary contains invalid data
        """
        # Validate through Pydantic model
        alarm_data = AlarmBase(**alarm_dict)
        return cls(
            id=alarm_data.id,
            hour=alarm_data.hour,
            minute=alarm_data.minute,
            days=alarm_data.days,
            schedule=alarm_data.schedule,
            active=alarm_data.active
        )

    def to_response_model(self) -> AlarmBase:
        """
        Convert to a Pydantic response model for API responses.
        
        Returns:
            AlarmBase: Pydantic model for API responses
        """
        return AlarmBase(**self.to_dict())

    def __repr__(self) -> str:
        """
        Return a string representation of the Alarm object.
        
        Returns:
            str: Human-readable representation of the alarm
        """
        time_str = f"{self.hour:02d}:{self.minute:02d}"
        days_str = ", ".join(DAY_ABBREVS[day] for day in self.days)
        status = "Active" if self.active else "Inactive"
        return f"Alarm({self.id}) - {time_str} on {days_str} (schedule: {self.schedule}, {status})"
