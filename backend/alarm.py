from typing import List, Optional
import uuid
from datetime import time
from pydantic import BaseModel, Field, validator

class AlarmBase(BaseModel):
    """Base Pydantic model for alarm validation."""
    hour: int = Field(..., ge=0, le=23, description="Hour of the alarm (0-23)")
    minute: int = Field(..., ge=0, le=59, description="Minute of the alarm (0-59)")
    days: List[int] = Field(
        ...,
        min_items=1,
        max_items=7,
        description="Days of the week (0=Monday, 6=Sunday)"
    )
    is_primary_schedule: bool = Field(
        ...,
        description="Whether this alarm belongs to the primary schedule"
    )
    active: bool = Field(
        True,
        description="Whether the alarm is active"
    )

    @validator('days')
    def validate_days(cls, v):
        """Validate that days are within range and unique."""
        if not v:
            raise ValueError("At least one day must be selected")
        if not all(0 <= day <= 6 for day in v):
            raise ValueError("Days must be between 0 (Monday) and 6 (Sunday)")
        if len(set(v)) != len(v):
            raise ValueError("Days must be unique")
        return sorted(v)

    def get_time(self) -> time:
        """Get the alarm time as a datetime.time object."""
        return time(hour=self.hour, minute=self.minute)

class AlarmCreate(AlarmBase):
    """Schema for creating a new alarm."""
    id: Optional[str] = Field(None, description="Optional ID for the alarm")

class AlarmResponse(AlarmBase):
    """Schema for alarm responses."""
    id: str = Field(..., description="Unique ID of the alarm")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "hour": 7,
                "minute": 30,
                "days": [0, 1, 2, 3, 4],
                "is_primary_schedule": True,
                "active": True
            }
        }

class Alarm:
    """
    Represents an alarm with validation and serialization capabilities.
    
    Attributes:
        id (str): Unique identifier for the alarm
        hour (int): Hour of the alarm (0-23)
        minute (int): Minute of the alarm (0-59)
        days (List[int]): Days of the week the alarm is active (0=Monday, 6=Sunday)
        is_primary_schedule (bool): Whether this alarm belongs to the primary schedule
        active (bool): Whether the alarm is currently active
    """

    def __init__(
        self,
        id: Optional[str],
        hour: int,
        minute: int,
        days: List[int],
        is_primary_schedule: bool,
        active: bool = True
    ):
        """
        Initialize a new Alarm instance with validation.
        
        Args:
            id: Optional unique identifier. If None, a new UUID will be generated.
            hour: Hour of the alarm (0-23)
            minute: Minute of the alarm (0-59)
            days: List of days the alarm should trigger (0=Monday, 6=Sunday)
            is_primary_schedule: Whether this alarm belongs to the primary schedule
            active: Whether the alarm is active (default: True)
            
        Raises:
            ValueError: If any of the input values are invalid
        """
        # Create Pydantic model for validation
        alarm_data = AlarmCreate(
            id=id,
            hour=hour,
            minute=minute,
            days=days,
            is_primary_schedule=is_primary_schedule,
            active=active
        )
        
        # Set validated values
        self.id = alarm_data.id if alarm_data.id else str(uuid.uuid4())
        self.hour = alarm_data.hour
        self.minute = alarm_data.minute
        self.days = alarm_data.days
        self.is_primary_schedule = alarm_data.is_primary_schedule
        self.active = alarm_data.active

    def to_dict(self) -> dict:
        """
        Convert the Alarm object to a dictionary for JSON serialization.
        
        Returns:
            dict: Dictionary representation of the alarm
        """
        return {
            "id": self.id,
            "hour": self.hour,
            "minute": self.minute,
            "days": self.days,
            "is_primary_schedule": self.is_primary_schedule,
            "active": self.active
        }

    @classmethod
    def from_dict(cls, alarm_dict: dict) -> 'Alarm':
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
        alarm_data = AlarmCreate(**alarm_dict)
        return cls(
            id=alarm_data.id,
            hour=alarm_data.hour,
            minute=alarm_data.minute,
            days=alarm_data.days,
            is_primary_schedule=alarm_data.is_primary_schedule,
            active=alarm_data.active
        )

    def to_response_model(self) -> AlarmResponse:
        """
        Convert to a Pydantic response model for API responses.
        
        Returns:
            AlarmResponse: Pydantic model for API responses
        """
        return AlarmResponse(**self.to_dict())

    def get_time(self) -> time:
        """
        Get the alarm time as a datetime.time object.
        
        Returns:
            time: Time object representing the alarm time
        """
        return time(hour=self.hour, minute=self.minute)

    def __repr__(self) -> str:
        """
        Return a string representation of the Alarm object.
        
        Returns:
            str: Human-readable representation of the alarm
        """
        time_str = f"{self.hour:02d}:{self.minute:02d}"
        days_str = ", ".join(
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d] 
            for d in self.days
        )
        schedule = "Primary" if self.is_primary_schedule else "Secondary"
        status = "Active" if self.active else "Inactive"
        return f"Alarm({self.id}) - {time_str} on {days_str} ({schedule}, {status})"
