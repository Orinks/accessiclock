"""
Data models for AccessiClock application.

This module contains all the dataclasses and data structures used throughout
the application for clock packages, preferences, and configuration.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
from enum import Enum


class ClockType(Enum):
    """Enumeration for clock display types."""
    DIGITAL = "digital"
    ANALOG = "analog"


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


@dataclass
class AnalogStyle:
    """Configuration for analog clock appearance."""
    face_color: str = "#FFFFFF"
    hour_hand_color: str = "#000000"
    minute_hand_color: str = "#000000"
    second_hand_color: str = "#FF0000"
    number_color: str = "#000000"
    tick_color: str = "#000000"
    show_numbers: bool = True
    show_ticks: bool = True
    
    def validate(self) -> None:
        """Validate analog style configuration."""
        # Validate color formats (basic hex color validation)
        colors = [
            self.face_color, self.hour_hand_color, self.minute_hand_color,
            self.second_hand_color, self.number_color, self.tick_color
        ]
        for color in colors:
            if not self._is_valid_color(color):
                raise ValidationError(f"Invalid color format: {color}")
    
    def _is_valid_color(self, color: str) -> bool:
        """Basic validation for hex color format."""
        if not color.startswith('#'):
            return False
        if len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False


@dataclass
class DigitalStyle:
    """Configuration for digital clock appearance."""
    font_weight: str = "normal"
    show_seconds: bool = True
    time_format: str = "12"  # "12" or "24"
    date_format: str = "%Y-%m-%d"
    show_date: bool = False
    
    def validate(self) -> None:
        """Validate digital style configuration."""
        if self.font_weight not in ["normal", "bold", "light"]:
            raise ValidationError(f"Invalid font weight: {self.font_weight}")
        
        if self.time_format not in ["12", "24"]:
            raise ValidationError(f"Invalid time format: {self.time_format}")
        
        # Basic date format validation
        try:
            datetime.now().strftime(self.date_format)
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {self.date_format} - {e}")


@dataclass
class VisualConfig:
    """Visual configuration for clock display."""
    background_color: str = "#FFFFFF"
    text_color: str = "#000000"
    font_family: str = "Arial"
    font_size: int = 48
    analog_style: Optional[AnalogStyle] = None
    digital_style: Optional[DigitalStyle] = None
    
    def __post_init__(self):
        """Initialize default styles if not provided."""
        if self.analog_style is None:
            self.analog_style = AnalogStyle()
        if self.digital_style is None:
            self.digital_style = DigitalStyle()
    
    def validate(self) -> None:
        """Validate visual configuration."""
        # Validate colors
        if not self._is_valid_color(self.background_color):
            raise ValidationError(f"Invalid background color: {self.background_color}")
        if not self._is_valid_color(self.text_color):
            raise ValidationError(f"Invalid text color: {self.text_color}")
        
        # Validate font size
        if not isinstance(self.font_size, int) or self.font_size <= 0:
            raise ValidationError(f"Font size must be a positive integer: {self.font_size}")
        
        # Validate font family (basic check)
        if not self.font_family or not isinstance(self.font_family, str):
            raise ValidationError(f"Invalid font family: {self.font_family}")
        
        # Validate sub-styles
        if self.analog_style:
            self.analog_style.validate()
        if self.digital_style:
            self.digital_style.validate()
    
    def _is_valid_color(self, color: str) -> bool:
        """Basic validation for hex color format."""
        if not color.startswith('#'):
            return False
        if len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False


@dataclass
class AudioConfig:
    """Audio configuration for clock sounds."""
    tick_sound: Optional[str] = None
    hour_chime: Optional[str] = None
    quarter_chime: Optional[str] = None
    half_chime: Optional[str] = None
    
    def validate(self) -> None:
        """Validate audio configuration."""
        sound_files = [
            self.tick_sound, self.hour_chime, 
            self.quarter_chime, self.half_chime
        ]
        
        for sound_file in sound_files:
            if sound_file is not None:
                if not isinstance(sound_file, str):
                    raise ValidationError(f"Sound file path must be a string: {sound_file}")
                
                # Check if file exists (if it's an absolute path)
                if Path(sound_file).is_absolute() and not Path(sound_file).exists():
                    raise ValidationError(f"Sound file not found: {sound_file}")
                
                # Validate file extension
                valid_extensions = ['.wav', '.mp3', '.ogg']
                if not any(sound_file.lower().endswith(ext) for ext in valid_extensions):
                    raise ValidationError(f"Invalid audio file format: {sound_file}")


@dataclass
class ClockPackage:
    """Complete clock package definition."""
    id: str
    name: str
    description: str
    author: str
    version: str
    clock_type: str
    visual_config: VisualConfig
    audio_config: AudioConfig
    created_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Ensure clock_type is valid
        if self.clock_type not in [ct.value for ct in ClockType]:
            raise ValidationError(f"Invalid clock type: {self.clock_type}")
        
        # Ensure visual_config and audio_config are proper instances
        if not isinstance(self.visual_config, VisualConfig):
            if isinstance(self.visual_config, dict):
                self.visual_config = VisualConfig(**self.visual_config)
            else:
                raise ValidationError("visual_config must be a VisualConfig instance or dict")
        
        if not isinstance(self.audio_config, AudioConfig):
            if isinstance(self.audio_config, dict):
                self.audio_config = AudioConfig(**self.audio_config)
            else:
                raise ValidationError("audio_config must be an AudioConfig instance or dict")
    
    def validate(self) -> None:
        """Validate the complete clock package."""
        # Validate required string fields
        required_fields = ['id', 'name', 'description', 'author', 'version']
        for field_name in required_fields:
            value = getattr(self, field_name)
            if not value or not isinstance(value, str):
                raise ValidationError(f"Field '{field_name}' is required and must be a non-empty string")
        
        # Validate clock type
        if self.clock_type not in [ct.value for ct in ClockType]:
            raise ValidationError(f"Invalid clock type: {self.clock_type}")
        
        # Validate sub-configurations
        self.visual_config.validate()
        self.audio_config.validate()
        
        # Validate created_date
        if not isinstance(self.created_date, datetime):
            raise ValidationError("created_date must be a datetime object")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert clock package to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime to ISO string
        data['created_date'] = self.created_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClockPackage':
        """Create clock package from dictionary."""
        # Convert ISO string back to datetime
        if 'created_date' in data and isinstance(data['created_date'], str):
            data['created_date'] = datetime.fromisoformat(data['created_date'])
        
        # Handle nested configurations
        if 'visual_config' in data and isinstance(data['visual_config'], dict):
            visual_data = data['visual_config']
            if 'analog_style' in visual_data and visual_data['analog_style']:
                visual_data['analog_style'] = AnalogStyle(**visual_data['analog_style'])
            if 'digital_style' in visual_data and visual_data['digital_style']:
                visual_data['digital_style'] = DigitalStyle(**visual_data['digital_style'])
            data['visual_config'] = VisualConfig(**visual_data)
        
        if 'audio_config' in data and isinstance(data['audio_config'], dict):
            data['audio_config'] = AudioConfig(**data['audio_config'])
        
        return cls(**data)


@dataclass
class NotificationSettings:
    """Settings for system notifications."""
    enabled: bool = True
    show_hourly_chimes: bool = True
    show_time_announcements: bool = False
    notification_duration: int = 5  # seconds
    
    def validate(self) -> None:
        """Validate notification settings."""
        if not isinstance(self.notification_duration, int) or self.notification_duration <= 0:
            raise ValidationError("notification_duration must be a positive integer")


@dataclass
class UserPreferences:
    """User preferences and application settings."""
    selected_clock_package: str = "default"
    chime_enabled: bool = True
    speech_enabled: bool = False
    elevenlabs_api_key: Optional[str] = None
    selected_voice: Optional[str] = None
    volume_settings: Dict[str, float] = field(default_factory=lambda: {
        "master": 1.0,
        "ticks": 0.8,
        "chimes": 1.0,
        "speech": 0.9
    })
    notification_settings: NotificationSettings = field(default_factory=NotificationSettings)
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Ensure notification_settings is proper instance
        if not isinstance(self.notification_settings, NotificationSettings):
            if isinstance(self.notification_settings, dict):
                self.notification_settings = NotificationSettings(**self.notification_settings)
            else:
                self.notification_settings = NotificationSettings()
    
    def validate(self) -> None:
        """Validate user preferences."""
        # Validate selected_clock_package
        if not self.selected_clock_package or not isinstance(self.selected_clock_package, str):
            raise ValidationError("selected_clock_package must be a non-empty string")
        
        # Validate volume settings
        if not isinstance(self.volume_settings, dict):
            raise ValidationError("volume_settings must be a dictionary")
        
        for key, value in self.volume_settings.items():
            if not isinstance(key, str):
                raise ValidationError(f"Volume setting key must be string: {key}")
            if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                raise ValidationError(f"Volume setting value must be between 0.0 and 1.0: {key}={value}")
        
        # Validate API key if provided
        if self.elevenlabs_api_key is not None:
            if not isinstance(self.elevenlabs_api_key, str) or len(self.elevenlabs_api_key.strip()) == 0:
                raise ValidationError("elevenlabs_api_key must be a non-empty string if provided")
        
        # Validate notification settings
        self.notification_settings.validate()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create preferences from dictionary."""
        # Handle nested notification settings
        if 'notification_settings' in data and isinstance(data['notification_settings'], dict):
            data['notification_settings'] = NotificationSettings(**data['notification_settings'])
        
        return cls(**data)