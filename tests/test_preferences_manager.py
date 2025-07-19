"""
Unit tests for PreferencesManager.

Tests cover loading, saving, validation, and error handling scenarios
for the preferences management system.
"""

import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.accessiclock.managers.preferences_manager import PreferencesManager
from src.accessiclock.models.data_models import UserPreferences, ValidationError, NotificationSettings


class TestPreferencesManager:
    """Test suite for PreferencesManager class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Mock the config directory to use our temp directory
        self.patcher = patch.object(PreferencesManager, '_get_config_directory')
        self.mock_get_config_dir = self.patcher.start()
        self.mock_get_config_dir.return_value = self.temp_path
        
        # Create preferences manager instance
        self.preferences_manager = PreferencesManager()
    
    def teardown_method(self):
        """Clean up after each test method."""
        self.patcher.stop()
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test PreferencesManager initialization."""
        assert self.preferences_manager.config_dir == self.temp_path
        assert self.preferences_manager.preferences_file == self.temp_path / "preferences.json"
        assert self.preferences_manager.backup_file == self.temp_path / "preferences_backup.json"
        assert self.preferences_manager._preferences is None
        assert self.temp_path.exists()
    
    def test_load_default_preferences(self):
        """Test loading default preferences when no file exists."""
        preferences = self.preferences_manager.load_preferences()
        
        assert isinstance(preferences, UserPreferences)
        assert preferences.selected_clock_package == "default"
        assert preferences.chime_enabled is True
        assert preferences.speech_enabled is False
        assert preferences.elevenlabs_api_key is None
        assert preferences.selected_voice is None
        assert isinstance(preferences.volume_settings, dict)
        assert isinstance(preferences.notification_settings, NotificationSettings)
        
        # Check that preferences file was created
        assert self.preferences_manager.preferences_file.exists()
    
    def test_save_preferences(self):
        """Test saving preferences to file."""
        # Load default preferences first
        preferences = self.preferences_manager.load_preferences()
        
        # Modify some settings
        preferences.chime_enabled = False
        preferences.speech_enabled = True
        preferences.selected_clock_package = "custom"
        
        # Save preferences
        success = self.preferences_manager.save_preferences()
        assert success is True
        
        # Verify file exists and contains correct data
        assert self.preferences_manager.preferences_file.exists()
        
        with open(self.preferences_manager.preferences_file, 'r') as f:
            data = json.load(f)
        
        assert data['chime_enabled'] is False
        assert data['speech_enabled'] is True
        assert data['selected_clock_package'] == "custom"
    
    def test_load_existing_preferences(self):
        """Test loading preferences from existing file."""
        # Create test preferences data
        test_data = {
            "selected_clock_package": "test_clock",
            "chime_enabled": False,
            "speech_enabled": True,
            "elevenlabs_api_key": "test_key",
            "selected_voice": "test_voice",
            "volume_settings": {
                "master": 0.8,
                "ticks": 0.6,
                "chimes": 0.9,
                "speech": 0.7
            },
            "notification_settings": {
                "enabled": True,
                "show_hourly_chimes": False,
                "show_time_announcements": True,
                "notification_duration": 10
            }
        }
        
        # Write test data to preferences file
        with open(self.preferences_manager.preferences_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load preferences
        preferences = self.preferences_manager.load_preferences()
        
        # Verify loaded data
        assert preferences.selected_clock_package == "test_clock"
        assert preferences.chime_enabled is False
        assert preferences.speech_enabled is True
        assert preferences.elevenlabs_api_key == "test_key"
        assert preferences.selected_voice == "test_voice"
        assert preferences.volume_settings["master"] == 0.8
        assert preferences.notification_settings.enabled is True
        assert preferences.notification_settings.show_hourly_chimes is False
        assert preferences.notification_settings.notification_duration == 10
    
    def test_load_corrupted_preferences_fallback_to_defaults(self):
        """Test fallback to defaults when preferences file is corrupted."""
        # Write invalid JSON to preferences file
        with open(self.preferences_manager.preferences_file, 'w') as f:
            f.write("invalid json content")
        
        # Load preferences should fall back to defaults
        preferences = self.preferences_manager.load_preferences()
        
        assert isinstance(preferences, UserPreferences)
        assert preferences.selected_clock_package == "default"
        assert preferences.chime_enabled is True
    
    def test_load_invalid_preferences_fallback_to_defaults(self):
        """Test fallback to defaults when preferences data is invalid."""
        # Write invalid preferences data
        invalid_data = {
            "selected_clock_package": "",  # Invalid empty string
            "volume_settings": {
                "master": 2.0  # Invalid volume > 1.0
            }
        }
        
        with open(self.preferences_manager.preferences_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Load preferences should fall back to defaults
        preferences = self.preferences_manager.load_preferences()
        
        assert isinstance(preferences, UserPreferences)
        assert preferences.selected_clock_package == "default"
        assert preferences.volume_settings["master"] == 1.0
    
    def test_backup_and_restore(self):
        """Test backup creation and restoration."""
        # Load and modify preferences
        preferences = self.preferences_manager.load_preferences()
        preferences.chime_enabled = False
        self.preferences_manager.save_preferences()
        
        # Verify backup was created
        assert self.preferences_manager.backup_file.exists()
        
        # Corrupt the main preferences file
        with open(self.preferences_manager.preferences_file, 'w') as f:
            f.write("corrupted data")
        
        # Create new preferences manager to test backup loading
        # Need to use the same temp directory setup
        with patch.object(PreferencesManager, '_get_config_directory', return_value=self.temp_path):
            new_manager = PreferencesManager()
            preferences = new_manager.load_preferences()
        
        # Should have loaded from backup
        assert preferences.chime_enabled is False
    
    def test_get_preference(self):
        """Test getting individual preference values."""
        preferences = self.preferences_manager.load_preferences()
        
        # Test simple key
        assert self.preferences_manager.get_preference("chime_enabled") is True
        assert self.preferences_manager.get_preference("selected_clock_package") == "default"
        
        # Test nested key with dot notation
        assert self.preferences_manager.get_preference("volume_settings.master") == 1.0
        assert self.preferences_manager.get_preference("notification_settings.enabled") is True
        
        # Test non-existent key with default
        assert self.preferences_manager.get_preference("non_existent", "default_value") == "default_value"
        assert self.preferences_manager.get_preference("volume_settings.non_existent", 0.5) == 0.5
    
    def test_set_preference(self):
        """Test setting individual preference values."""
        self.preferences_manager.load_preferences()
        
        # Test simple key
        success = self.preferences_manager.set_preference("chime_enabled", False)
        assert success is True
        assert self.preferences_manager.get_preference("chime_enabled") is False
        
        # Test nested key with dot notation
        success = self.preferences_manager.set_preference("volume_settings.master", 0.8)
        assert success is True
        assert self.preferences_manager.get_preference("volume_settings.master") == 0.8
        
        # Test setting invalid value
        success = self.preferences_manager.set_preference("volume_settings.master", 2.0)
        assert success is False  # Should fail validation
    
    def test_set_preferences(self):
        """Test setting entire preferences instance."""
        # Create custom preferences
        custom_preferences = UserPreferences(
            selected_clock_package="custom",
            chime_enabled=False,
            speech_enabled=True
        )
        
        success = self.preferences_manager.set_preferences(custom_preferences)
        assert success is True
        
        # Verify preferences were set
        loaded_preferences = self.preferences_manager.get_preferences()
        assert loaded_preferences.selected_clock_package == "custom"
        assert loaded_preferences.chime_enabled is False
        assert loaded_preferences.speech_enabled is True
    
    def test_reset_to_defaults(self):
        """Test resetting preferences to defaults."""
        # Load and modify preferences
        preferences = self.preferences_manager.load_preferences()
        preferences.chime_enabled = False
        preferences.selected_clock_package = "custom"
        self.preferences_manager.save_preferences()
        
        # Reset to defaults
        success = self.preferences_manager.reset_to_defaults()
        assert success is True
        
        # Verify reset
        preferences = self.preferences_manager.get_preferences()
        assert preferences.chime_enabled is True
        assert preferences.selected_clock_package == "default"
    
    def test_export_preferences(self):
        """Test exporting preferences to file."""
        # Load and modify preferences
        preferences = self.preferences_manager.load_preferences()
        preferences.chime_enabled = False
        
        # Export to file
        export_file = self.temp_path / "exported_preferences.json"
        success = self.preferences_manager.export_preferences(export_file)
        assert success is True
        assert export_file.exists()
        
        # Verify exported content
        with open(export_file, 'r') as f:
            data = json.load(f)
        assert data['chime_enabled'] is False
    
    def test_import_preferences(self):
        """Test importing preferences from file."""
        # Create import data
        import_data = {
            "selected_clock_package": "imported",
            "chime_enabled": False,
            "speech_enabled": True,
            "volume_settings": {
                "master": 0.7,
                "ticks": 0.5,
                "chimes": 0.8,
                "speech": 0.6
            },
            "notification_settings": {
                "enabled": False,
                "show_hourly_chimes": True,
                "show_time_announcements": False,
                "notification_duration": 3
            }
        }
        
        # Write import file
        import_file = self.temp_path / "import_preferences.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)
        
        # Import preferences
        success = self.preferences_manager.import_preferences(import_file)
        assert success is True
        
        # Verify imported preferences
        preferences = self.preferences_manager.get_preferences()
        assert preferences.selected_clock_package == "imported"
        assert preferences.chime_enabled is False
        assert preferences.speech_enabled is True
        assert preferences.volume_settings["master"] == 0.7
        assert preferences.notification_settings.enabled is False
    
    def test_import_invalid_preferences(self):
        """Test importing invalid preferences file."""
        # Create invalid import file
        import_file = self.temp_path / "invalid_preferences.json"
        with open(import_file, 'w') as f:
            f.write("invalid json")
        
        # Import should fail
        success = self.preferences_manager.import_preferences(import_file)
        assert success is False
    
    def test_config_directory_creation_failure(self):
        """Test handling of config directory creation failure."""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")):
            with pytest.raises(ValidationError, match="Failed to create configuration directory"):
                PreferencesManager()
    
    def test_save_without_loaded_preferences(self):
        """Test saving when no preferences are loaded."""
        manager = PreferencesManager()
        success = manager.save_preferences()
        assert success is False
    
    def test_validation_error_during_save(self):
        """Test handling validation errors during save."""
        preferences = self.preferences_manager.load_preferences()
        
        # Manually corrupt preferences to cause validation error
        preferences.volume_settings["master"] = 2.0  # Invalid volume
        
        success = self.preferences_manager.save_preferences()
        assert success is False
    
    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    def test_file_permission_error_during_save(self, mock_file):
        """Test handling file permission errors during save."""
        self.preferences_manager.load_preferences()
        success = self.preferences_manager.save_preferences()
        assert success is False
    
    def test_config_directory_exists(self):
        """Test that config directory is created and accessible."""
        # Test that the preferences manager creates a valid config directory
        assert self.preferences_manager.config_dir.exists()
        assert self.preferences_manager.config_dir.is_dir()


class TestPreferencesManagerIntegration:
    """Integration tests for PreferencesManager with real file system."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Use real file system but in temp directory
        self.patcher = patch.object(PreferencesManager, '_get_config_directory')
        self.mock_get_config_dir = self.patcher.start()
        self.mock_get_config_dir.return_value = self.temp_path
    
    def teardown_method(self):
        """Clean up integration test fixtures."""
        self.patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_preferences_lifecycle(self):
        """Test complete preferences lifecycle: create, modify, save, load."""
        # Create manager and load defaults
        manager1 = PreferencesManager()
        preferences1 = manager1.load_preferences()
        
        # Modify preferences
        preferences1.chime_enabled = False
        preferences1.selected_clock_package = "test_clock"
        preferences1.volume_settings["master"] = 0.8
        preferences1.notification_settings.enabled = False
        
        # Save preferences
        success = manager1.save_preferences()
        assert success is True
        
        # Create new manager instance and load
        manager2 = PreferencesManager()
        preferences2 = manager2.load_preferences()
        
        # Verify persistence
        assert preferences2.chime_enabled is False
        assert preferences2.selected_clock_package == "test_clock"
        assert preferences2.volume_settings["master"] == 0.8
        assert preferences2.notification_settings.enabled is False
    
    def test_concurrent_access_safety(self):
        """Test that concurrent access doesn't corrupt preferences."""
        # Create initial preferences
        manager1 = PreferencesManager()
        preferences1 = manager1.load_preferences()
        preferences1.chime_enabled = False
        manager1.save_preferences()
        
        # Simulate concurrent access
        manager2 = PreferencesManager()
        preferences2 = manager2.load_preferences()
        
        # Both should have the same data
        assert preferences1.chime_enabled == preferences2.chime_enabled
        assert preferences1.selected_clock_package == preferences2.selected_clock_package