"""
Preferences Manager for AccessiClock application.

This module handles loading, saving, and managing user preferences with
JSON-based configuration storage and validation.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from ..models.data_models import UserPreferences, ValidationError
from ..utils.logging_config import get_logger
from ..utils.error_handler import get_error_handler, ErrorCategory


class PreferencesManager:
    """Manages user preferences with JSON-based storage."""
    
    def __init__(self, app_instance=None):
        """Initialize the preferences manager.
        
        Args:
            app_instance: Reference to the main application instance for error handling
        """
        self.logger = get_logger("preferences_manager")
        self.error_handler = get_error_handler(app_instance) if app_instance else None
        
        # Set up configuration directory and file paths
        self.config_dir = self._get_config_directory()
        self.preferences_file = self.config_dir / "preferences.json"
        self.backup_file = self.config_dir / "preferences_backup.json"
        
        # Current preferences instance
        self._preferences: Optional[UserPreferences] = None
        
        # Ensure config directory exists
        self._ensure_config_directory()
        
        self.logger.info(f"PreferencesManager initialized with config dir: {self.config_dir}")
    
    def _get_config_directory(self) -> Path:
        """Get the configuration directory path based on the operating system."""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', '')) / 'AccessiClock'
        elif os.name == 'posix':  # macOS and Linux
            if 'darwin' in os.sys.platform.lower():  # macOS
                config_dir = Path.home() / 'Library' / 'Application Support' / 'AccessiClock'
            else:  # Linux
                config_dir = Path.home() / '.config' / 'accessiclock'
        else:
            # Fallback to home directory
            config_dir = Path.home() / '.accessiclock'
        
        return config_dir
    
    def _ensure_config_directory(self) -> None:
        """Ensure the configuration directory exists."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Configuration directory ensured: {self.config_dir}")
        except Exception as e:
            error_msg = f"Failed to create configuration directory: {e}"
            self.logger.error(error_msg)
            if self.error_handler:
                self.error_handler.handle_error(
                    e, ErrorCategory.FILE_SYSTEM, "config directory creation"
                )
            raise ValidationError(error_msg)
    
    def load_preferences(self) -> UserPreferences:
        """Load preferences from storage.
        
        Returns:
            UserPreferences: Loaded preferences or defaults if loading fails
        """
        try:
            if self.preferences_file.exists():
                self.logger.info(f"Loading preferences from: {self.preferences_file}")
                
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Validate the loaded data structure
                if not isinstance(data, dict):
                    raise ValidationError("Preferences file contains invalid data structure")
                
                # Create preferences from loaded data
                preferences = UserPreferences.from_dict(data)
                
                # Validate the loaded preferences
                preferences.validate()
                
                self._preferences = preferences
                self.logger.info("Preferences loaded successfully")
                return preferences
                
            else:
                self.logger.info("No preferences file found, using defaults")
                return self._load_default_preferences()
                
        except (json.JSONDecodeError, ValidationError, FileNotFoundError) as e:
            error_msg = f"Failed to load preferences: {e}"
            self.logger.warning(error_msg)
            
            if self.error_handler:
                self.error_handler.handle_error(
                    e, ErrorCategory.CONFIGURATION, "preferences loading"
                )
            
            # Try to load from backup
            backup_preferences = self._try_load_backup()
            if backup_preferences:
                return backup_preferences
            
            # Fall back to defaults
            self.logger.info("Falling back to default preferences")
            return self._load_default_preferences()
        
        except Exception as e:
            error_msg = f"Unexpected error loading preferences: {e}"
            self.logger.error(error_msg)
            
            if self.error_handler:
                self.error_handler.handle_error(
                    e, ErrorCategory.CONFIGURATION, "preferences loading"
                )
            
            return self._load_default_preferences()
    
    def _try_load_backup(self) -> Optional[UserPreferences]:
        """Try to load preferences from backup file.
        
        Returns:
            UserPreferences or None if backup loading fails
        """
        try:
            if self.backup_file.exists():
                self.logger.info("Attempting to load from backup preferences")
                
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                preferences = UserPreferences.from_dict(data)
                preferences.validate()
                
                self._preferences = preferences
                self.logger.info("Backup preferences loaded successfully")
                return preferences
                
        except Exception as e:
            self.logger.warning(f"Failed to load backup preferences: {e}")
        
        return None
    
    def _load_default_preferences(self) -> UserPreferences:
        """Load default preferences.
        
        Returns:
            UserPreferences: Default preferences instance
        """
        try:
            preferences = UserPreferences()
            preferences.validate()
            self._preferences = preferences
            
            # Save defaults to file for future use
            self.save_preferences()
            
            self.logger.info("Default preferences loaded and saved")
            return preferences
            
        except Exception as e:
            error_msg = f"Failed to create default preferences: {e}"
            self.logger.error(error_msg)
            
            if self.error_handler:
                self.error_handler.handle_error(
                    e, ErrorCategory.CONFIGURATION, "default preferences creation"
                )
            
            raise ValidationError(error_msg)
    
    def save_preferences(self) -> bool:
        """Save current preferences to storage.
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        if self._preferences is None:
            self.logger.warning("No preferences to save")
            return False
        
        try:
            # Validate preferences before saving
            self._preferences.validate()
            
            # Create backup of existing preferences
            self._create_backup()
            
            # Convert to dictionary for JSON serialization
            data = self._preferences.to_dict()
            
            # Write to temporary file first, then rename for atomic operation
            temp_file = self.preferences_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self.preferences_file)
            
            self.logger.info(f"Preferences saved successfully to: {self.preferences_file}")
            return True
            
        except ValidationError as e:
            error_msg = f"Preferences validation failed during save: {e}"
            self.logger.error(error_msg)
            
            if self.error_handler:
                self.error_handler.handle_error(
                    e, ErrorCategory.CONFIGURATION, "preferences validation"
                )
            
            return False
            
        except Exception as e:
            error_msg = f"Failed to save preferences: {e}"
            self.logger.error(error_msg)
            
            if self.error_handler:
                self.error_handler.handle_error(
                    e, ErrorCategory.FILE_SYSTEM, "preferences saving"
                )
            
            return False
    
    def _create_backup(self) -> None:
        """Create a backup of the current preferences file."""
        try:
            if self.preferences_file.exists():
                import shutil
                shutil.copy2(self.preferences_file, self.backup_file)
                self.logger.debug("Preferences backup created")
        except Exception as e:
            self.logger.warning(f"Failed to create preferences backup: {e}")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a specific preference value.
        
        Args:
            key: The preference key (supports dot notation for nested values)
            default: Default value if key is not found
            
        Returns:
            The preference value or default
        """
        if self._preferences is None:
            self.load_preferences()
        
        try:
            # Handle dot notation for nested keys
            keys = key.split('.')
            value = self._preferences
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                elif isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.warning(f"Error getting preference '{key}': {e}")
            return default
    
    def set_preference(self, key: str, value: Any) -> bool:
        """Set a specific preference value.
        
        Args:
            key: The preference key (supports dot notation for nested values)
            value: The value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self._preferences is None:
            self.load_preferences()
        
        try:
            # Handle dot notation for nested keys
            keys = key.split('.')
            target = self._preferences
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if hasattr(target, k):
                    target = getattr(target, k)
                elif isinstance(target, dict):
                    if k not in target:
                        target[k] = {}
                    target = target[k]
                else:
                    self.logger.error(f"Cannot set nested preference: {key}")
                    return False
            
            # Set the final value
            final_key = keys[-1]
            if hasattr(target, final_key):
                setattr(target, final_key, value)
            elif isinstance(target, dict):
                target[final_key] = value
            else:
                self.logger.error(f"Cannot set preference: {key}")
                return False
            
            # Validate and save
            self._preferences.validate()
            return self.save_preferences()
            
        except ValidationError as e:
            self.logger.error(f"Validation error setting preference '{key}': {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error setting preference '{key}': {e}")
            return False
    
    def get_preferences(self) -> UserPreferences:
        """Get the current preferences instance.
        
        Returns:
            UserPreferences: Current preferences
        """
        if self._preferences is None:
            self.load_preferences()
        return self._preferences
    
    def set_preferences(self, preferences: UserPreferences) -> bool:
        """Set the entire preferences instance.
        
        Args:
            preferences: New preferences instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            preferences.validate()
            self._preferences = preferences
            return self.save_preferences()
        except ValidationError as e:
            self.logger.error(f"Invalid preferences provided: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset preferences to default values.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info("Resetting preferences to defaults")
            self._preferences = UserPreferences()
            return self.save_preferences()
        except Exception as e:
            self.logger.error(f"Failed to reset preferences: {e}")
            return False
    
    def export_preferences(self, file_path: Path) -> bool:
        """Export preferences to a specified file.
        
        Args:
            file_path: Path to export the preferences to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self._preferences is None:
            self.load_preferences()
        
        try:
            data = self._preferences.to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Preferences exported to: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export preferences: {e}")
            return False
    
    def import_preferences(self, file_path: Path) -> bool:
        """Import preferences from a specified file.
        
        Args:
            file_path: Path to import the preferences from
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            preferences = UserPreferences.from_dict(data)
            preferences.validate()
            
            self._preferences = preferences
            success = self.save_preferences()
            
            if success:
                self.logger.info(f"Preferences imported from: {file_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to import preferences: {e}")
            return False