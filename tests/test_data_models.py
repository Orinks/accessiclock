"""
Unit tests for AccessiClock data models.

Tests validation, serialization, and functionality of all data model classes.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from src.accessiclock.models import (
    ClockPackage,
    VisualConfig,
    AudioConfig,
    UserPreferences,
    NotificationSettings,
    AnalogStyle,
    DigitalStyle,
    ClockType,
    ValidationError
)


class TestAnalogStyle:
    """Test cases for AnalogStyle dataclass."""
    
    def test_analog_style_defaults(self):
        """Test AnalogStyle with default values."""
        style = AnalogStyle()
        assert style.face_color == "#FFFFFF"
        assert style.hour_hand_color == "#000000"
        assert style.minute_hand_color == "#000000"
        assert style.second_hand_color == "#FF0000"
        assert style.number_color == "#000000"
        assert style.tick_color == "#000000"
        assert style.show_numbers is True
        assert style.show_ticks is True
    
    def test_analog_style_custom_values(self):
        """Test AnalogStyle with custom values."""
        style = AnalogStyle(
            face_color="#F0F0F0",
            hour_hand_color="#333333",
            show_numbers=False
        )
        assert style.face_color == "#F0F0F0"
        assert style.hour_hand_color == "#333333"
        assert style.show_numbers is False
    
    def test_analog_style_validation_valid(self):
        """Test AnalogStyle validation with valid colors."""
        style = AnalogStyle()
        style.validate()  # Should not raise
    
    def test_analog_style_validation_invalid_color(self):
        """Test AnalogStyle validation with invalid colors."""
        style = AnalogStyle(face_color="invalid_color")
        with pytest.raises(ValidationError, match="Invalid color format"):
            style.validate()
    
    def test_analog_style_validation_invalid_hex(self):
        """Test AnalogStyle validation with invalid hex format."""
        style = AnalogStyle(face_color="#GGGGGG")
        with pytest.raises(ValidationError, match="Invalid color format"):
            style.validate()


class TestDigitalStyle:
    """Test cases for DigitalStyle dataclass."""
    
    def test_digital_style_defaults(self):
        """Test DigitalStyle with default values."""
        style = DigitalStyle()
        assert style.font_weight == "normal"
        assert style.show_seconds is True
        assert style.time_format == "12"
        assert style.date_format == "%Y-%m-%d"
        assert style.show_date is False
    
    def test_digital_style_custom_values(self):
        """Test DigitalStyle with custom values."""
        style = DigitalStyle(
            font_weight="bold",
            time_format="24",
            show_date=True
        )
        assert style.font_weight == "bold"
        assert style.time_format == "24"
        assert style.show_date is True
    
    def test_digital_style_validation_valid(self):
        """Test DigitalStyle validation with valid values."""
        style = DigitalStyle()
        style.validate()  # Should not raise
    
    def test_digital_style_validation_invalid_font_weight(self):
        """Test DigitalStyle validation with invalid font weight."""
        style = DigitalStyle(font_weight="invalid")
        with pytest.raises(ValidationError, match="Invalid font weight"):
            style.validate()
    
    def test_digital_style_validation_invalid_time_format(self):
        """Test DigitalStyle validation with invalid time format."""
        style = DigitalStyle(time_format="invalid")
        with pytest.raises(ValidationError, match="Invalid time format"):
            style.validate()
    
    def test_digital_style_validation_invalid_date_format(self):
        """Test DigitalStyle validation with invalid date format."""
        style = DigitalStyle(date_format="%invalid")
        with pytest.raises(ValidationError, match="Invalid date format"):
            style.validate()


class TestVisualConfig:
    """Test cases for VisualConfig dataclass."""
    
    def test_visual_config_defaults(self):
        """Test VisualConfig with default values."""
        config = VisualConfig()
        assert config.background_color == "#FFFFFF"
        assert config.text_color == "#000000"
        assert config.font_family == "Arial"
        assert config.font_size == 48
        assert isinstance(config.analog_style, AnalogStyle)
        assert isinstance(config.digital_style, DigitalStyle)
    
    def test_visual_config_custom_values(self):
        """Test VisualConfig with custom values."""
        analog_style = AnalogStyle(face_color="#F0F0F0")
        digital_style = DigitalStyle(font_weight="bold")
        
        config = VisualConfig(
            background_color="#CCCCCC",
            font_size=36,
            analog_style=analog_style,
            digital_style=digital_style
        )
        
        assert config.background_color == "#CCCCCC"
        assert config.font_size == 36
        assert config.analog_style.face_color == "#F0F0F0"
        assert config.digital_style.font_weight == "bold"
    
    def test_visual_config_validation_valid(self):
        """Test VisualConfig validation with valid values."""
        config = VisualConfig()
        config.validate()  # Should not raise
    
    def test_visual_config_validation_invalid_background_color(self):
        """Test VisualConfig validation with invalid background color."""
        config = VisualConfig(background_color="invalid")
        with pytest.raises(ValidationError, match="Invalid background color"):
            config.validate()
    
    def test_visual_config_validation_invalid_text_color(self):
        """Test VisualConfig validation with invalid text color."""
        config = VisualConfig(text_color="invalid")
        with pytest.raises(ValidationError, match="Invalid text color"):
            config.validate()
    
    def test_visual_config_validation_invalid_font_size(self):
        """Test VisualConfig validation with invalid font size."""
        config = VisualConfig(font_size=-1)
        with pytest.raises(ValidationError, match="Font size must be a positive integer"):
            config.validate()
    
    def test_visual_config_validation_invalid_font_family(self):
        """Test VisualConfig validation with invalid font family."""
        config = VisualConfig(font_family="")
        with pytest.raises(ValidationError, match="Invalid font family"):
            config.validate()


class TestAudioConfig:
    """Test cases for AudioConfig dataclass."""
    
    def test_audio_config_defaults(self):
        """Test AudioConfig with default values."""
        config = AudioConfig()
        assert config.tick_sound is None
        assert config.hour_chime is None
        assert config.quarter_chime is None
        assert config.half_chime is None
    
    def test_audio_config_custom_values(self):
        """Test AudioConfig with custom values."""
        config = AudioConfig(
            tick_sound="tick.wav",
            hour_chime="hour.mp3",
            quarter_chime="quarter.ogg"
        )
        assert config.tick_sound == "tick.wav"
        assert config.hour_chime == "hour.mp3"
        assert config.quarter_chime == "quarter.ogg"
    
    def test_audio_config_validation_valid(self):
        """Test AudioConfig validation with valid values."""
        config = AudioConfig(
            tick_sound="tick.wav",
            hour_chime="hour.mp3",
            quarter_chime="quarter.ogg"
        )
        config.validate()  # Should not raise
    
    def test_audio_config_validation_invalid_extension(self):
        """Test AudioConfig validation with invalid file extension."""
        config = AudioConfig(tick_sound="tick.txt")
        with pytest.raises(ValidationError, match="Invalid audio file format"):
            config.validate()
    
    def test_audio_config_validation_non_string(self):
        """Test AudioConfig validation with non-string path."""
        config = AudioConfig(tick_sound=123)
        with pytest.raises(ValidationError, match="Sound file path must be a string"):
            config.validate()
    
    def test_audio_config_validation_with_temp_file(self):
        """Test AudioConfig validation with actual file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            config = AudioConfig(tick_sound=temp_path)
            config.validate()  # Should not raise
        finally:
            os.unlink(temp_path)


class TestNotificationSettings:
    """Test cases for NotificationSettings dataclass."""
    
    def test_notification_settings_defaults(self):
        """Test NotificationSettings with default values."""
        settings = NotificationSettings()
        assert settings.enabled is True
        assert settings.show_hourly_chimes is True
        assert settings.show_time_announcements is False
        assert settings.notification_duration == 5
    
    def test_notification_settings_custom_values(self):
        """Test NotificationSettings with custom values."""
        settings = NotificationSettings(
            enabled=False,
            notification_duration=10
        )
        assert settings.enabled is False
        assert settings.notification_duration == 10
    
    def test_notification_settings_validation_valid(self):
        """Test NotificationSettings validation with valid values."""
        settings = NotificationSettings()
        settings.validate()  # Should not raise
    
    def test_notification_settings_validation_invalid_duration(self):
        """Test NotificationSettings validation with invalid duration."""
        settings = NotificationSettings(notification_duration=-1)
        with pytest.raises(ValidationError, match="notification_duration must be a positive integer"):
            settings.validate()


class TestUserPreferences:
    """Test cases for UserPreferences dataclass."""
    
    def test_user_preferences_defaults(self):
        """Test UserPreferences with default values."""
        prefs = UserPreferences()
        assert prefs.selected_clock_package == "default"
        assert prefs.chime_enabled is True
        assert prefs.speech_enabled is False
        assert prefs.elevenlabs_api_key is None
        assert prefs.selected_voice is None
        assert isinstance(prefs.volume_settings, dict)
        assert isinstance(prefs.notification_settings, NotificationSettings)
    
    def test_user_preferences_custom_values(self):
        """Test UserPreferences with custom values."""
        volume_settings = {"master": 0.8, "ticks": 0.5}
        notification_settings = NotificationSettings(enabled=False)
        
        prefs = UserPreferences(
            selected_clock_package="custom",
            chime_enabled=False,
            elevenlabs_api_key="test_key",
            volume_settings=volume_settings,
            notification_settings=notification_settings
        )
        
        assert prefs.selected_clock_package == "custom"
        assert prefs.chime_enabled is False
        assert prefs.elevenlabs_api_key == "test_key"
        assert prefs.volume_settings["master"] == 0.8
        assert prefs.notification_settings.enabled is False
    
    def test_user_preferences_validation_valid(self):
        """Test UserPreferences validation with valid values."""
        prefs = UserPreferences()
        prefs.validate()  # Should not raise
    
    def test_user_preferences_validation_empty_clock_package(self):
        """Test UserPreferences validation with empty clock package."""
        prefs = UserPreferences(selected_clock_package="")
        with pytest.raises(ValidationError, match="selected_clock_package must be a non-empty string"):
            prefs.validate()
    
    def test_user_preferences_validation_invalid_volume_settings(self):
        """Test UserPreferences validation with invalid volume settings."""
        prefs = UserPreferences(volume_settings={"master": 2.0})  # > 1.0
        with pytest.raises(ValidationError, match="Volume setting value must be between 0.0 and 1.0"):
            prefs.validate()
    
    def test_user_preferences_validation_empty_api_key(self):
        """Test UserPreferences validation with empty API key."""
        prefs = UserPreferences(elevenlabs_api_key="   ")
        with pytest.raises(ValidationError, match="elevenlabs_api_key must be a non-empty string"):
            prefs.validate()
    
    def test_user_preferences_serialization(self):
        """Test UserPreferences to_dict and from_dict methods."""
        original = UserPreferences(
            selected_clock_package="test",
            chime_enabled=False,
            elevenlabs_api_key="test_key"
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = UserPreferences.from_dict(data)
        
        assert restored.selected_clock_package == original.selected_clock_package
        assert restored.chime_enabled == original.chime_enabled
        assert restored.elevenlabs_api_key == original.elevenlabs_api_key


class TestClockPackage:
    """Test cases for ClockPackage dataclass."""
    
    def test_clock_package_creation(self):
        """Test ClockPackage creation with valid data."""
        visual_config = VisualConfig()
        audio_config = AudioConfig()
        
        package = ClockPackage(
            id="test_clock",
            name="Test Clock",
            description="A test clock package",
            author="Test Author",
            version="1.0.0",
            clock_type="digital",
            visual_config=visual_config,
            audio_config=audio_config
        )
        
        assert package.id == "test_clock"
        assert package.name == "Test Clock"
        assert package.clock_type == "digital"
        assert isinstance(package.created_date, datetime)
    
    def test_clock_package_validation_valid(self):
        """Test ClockPackage validation with valid data."""
        visual_config = VisualConfig()
        audio_config = AudioConfig()
        
        package = ClockPackage(
            id="test_clock",
            name="Test Clock",
            description="A test clock package",
            author="Test Author",
            version="1.0.0",
            clock_type="digital",
            visual_config=visual_config,
            audio_config=audio_config
        )
        
        package.validate()  # Should not raise
    
    def test_clock_package_validation_empty_required_field(self):
        """Test ClockPackage validation with empty required field."""
        visual_config = VisualConfig()
        audio_config = AudioConfig()
        
        package = ClockPackage(
            id="",  # Empty ID
            name="Test Clock",
            description="A test clock package",
            author="Test Author",
            version="1.0.0",
            clock_type="digital",
            visual_config=visual_config,
            audio_config=audio_config
        )
        
        with pytest.raises(ValidationError, match="Field 'id' is required"):
            package.validate()
    
    def test_clock_package_validation_invalid_clock_type(self):
        """Test ClockPackage validation with invalid clock type."""
        visual_config = VisualConfig()
        audio_config = AudioConfig()
        
        with pytest.raises(ValidationError, match="Invalid clock type"):
            ClockPackage(
                id="test_clock",
                name="Test Clock",
                description="A test clock package",
                author="Test Author",
                version="1.0.0",
                clock_type="invalid_type",
                visual_config=visual_config,
                audio_config=audio_config
            )
    
    def test_clock_package_serialization(self):
        """Test ClockPackage to_dict and from_dict methods."""
        visual_config = VisualConfig(font_size=36)
        audio_config = AudioConfig(tick_sound="tick.wav")
        
        original = ClockPackage(
            id="test_clock",
            name="Test Clock",
            description="A test clock package",
            author="Test Author",
            version="1.0.0",
            clock_type="digital",
            visual_config=visual_config,
            audio_config=audio_config
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = ClockPackage.from_dict(data)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.clock_type == original.clock_type
        assert restored.visual_config.font_size == original.visual_config.font_size
        assert restored.audio_config.tick_sound == original.audio_config.tick_sound
        assert restored.created_date == original.created_date
    
    def test_clock_package_from_dict_with_nested_dicts(self):
        """Test ClockPackage.from_dict with nested dictionary configurations."""
        data = {
            "id": "test_clock",
            "name": "Test Clock",
            "description": "A test clock package",
            "author": "Test Author",
            "version": "1.0.0",
            "clock_type": "analog",
            "visual_config": {
                "font_size": 36,
                "analog_style": {
                    "face_color": "#F0F0F0"
                },
                "digital_style": {
                    "font_weight": "bold"
                }
            },
            "audio_config": {
                "tick_sound": "tick.wav",
                "hour_chime": "hour.mp3"
            },
            "created_date": "2023-01-01T12:00:00"
        }
        
        package = ClockPackage.from_dict(data)
        
        assert package.id == "test_clock"
        assert package.clock_type == "analog"
        assert package.visual_config.font_size == 36
        assert package.visual_config.analog_style.face_color == "#F0F0F0"
        assert package.visual_config.digital_style.font_weight == "bold"
        assert package.audio_config.tick_sound == "tick.wav"
        assert package.audio_config.hour_chime == "hour.mp3"


class TestClockType:
    """Test cases for ClockType enum."""
    
    def test_clock_type_values(self):
        """Test ClockType enum values."""
        assert ClockType.DIGITAL.value == "digital"
        assert ClockType.ANALOG.value == "analog"
    
    def test_clock_type_membership(self):
        """Test ClockType membership checks."""
        assert "digital" in [ct.value for ct in ClockType]
        assert "analog" in [ct.value for ct in ClockType]
        assert "invalid" not in [ct.value for ct in ClockType]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])