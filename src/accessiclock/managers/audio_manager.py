"""
Audio Manager for AccessiClock application.

This module provides the AudioManager class that handles all audio playback
using an AudioBackend interface for better testability and separation of concerns.
"""

import threading
from typing import Dict, Optional, Union, List
from pathlib import Path

from ..utils.logging_config import get_logger
from ..utils.error_handler import get_error_handler, ErrorCategory
from ..interfaces.audio_interface import AudioBackend, AudioType


class AudioManager:
    """
    Manages all audio playback for the AccessiClock application.
    
    Uses an AudioBackend interface for audio operations, allowing for
    easy testing and potential backend swapping.
    """
    
    def __init__(self, audio_backend: Optional[AudioBackend] = None, error_handler=None):
        """
        Initialize the AudioManager.
        
        Args:
            audio_backend: AudioBackend implementation to use (defaults to PygameAudioBackend)
            error_handler: Optional error handler instance
        """
        self.logger = get_logger("audio_manager")
        self.error_handler = error_handler or get_error_handler()
        
        # Use provided backend or default to pygame backend
        if audio_backend is None:
            # Lazy import to avoid pygame import at module level
            from ..backends import PygameAudioBackend
            audio_backend = PygameAudioBackend(error_handler)
        
        self.audio_backend = audio_backend
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize the backend
        self._initialized = self.audio_backend.initialize()
        
        if self._initialized:
            self.logger.info("AudioManager initialized successfully")
        else:
            self.logger.warning("AudioManager initialization failed")
    
    def load_sound_file(self, audio_type: AudioType, file_path: Union[str, Path]) -> bool:
        """
        Load a sound file for the specified audio type.
        
        Args:
            audio_type: The type of audio (tick, chime, etc.)
            file_path: Path to the audio file
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not self._initialized:
            self.logger.error("Audio manager not initialized")
            return False
        
        try:
            with self._lock:
                success = self.audio_backend.load_sound_file(audio_type, file_path)
                
                if success:
                    self.logger.info(f"Loaded sound file for {audio_type.value}: {file_path}")
                else:
                    self.logger.warning(f"Failed to load sound file for {audio_type.value}: {file_path}")
                
                return success
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                f"loading sound file for {audio_type.value}",
                show_user_notification=False
            )
            return False
    
    def load_sound_pack(self, sound_pack: Dict[str, str]) -> Dict[AudioType, bool]:
        """
        Load multiple sound files from a sound pack configuration.
        
        Args:
            sound_pack: Dictionary mapping audio type names to file paths
            
        Returns:
            Dict[AudioType, bool]: Results of loading each sound file
        """
        results = {}
        
        # Map string keys to AudioType enums
        type_mapping = {
            'tick_sound': AudioType.TICK,
            'hour_chime': AudioType.HOUR_CHIME,
            'quarter_chime': AudioType.QUARTER_CHIME,
            'half_chime': AudioType.HALF_CHIME
        }
        
        for key, file_path in sound_pack.items():
            if key in type_mapping and file_path:
                audio_type = type_mapping[key]
                results[audio_type] = self.load_sound_file(audio_type, file_path)
        
        return results
    
    def play_sound(self, audio_type: AudioType, loops: int = 0) -> bool:
        """
        Play a sound of the specified type.
        
        Args:
            audio_type: The type of audio to play
            loops: Number of times to loop (-1 for infinite, 0 for once)
            
        Returns:
            bool: True if playback started successfully, False otherwise
        """
        if not self._initialized:
            self.logger.error("Audio manager not initialized")
            return False
        
        try:
            with self._lock:
                success = self.audio_backend.play_sound(audio_type, loops)
                
                if success:
                    self.logger.debug(f"Playing sound: {audio_type.value}")
                else:
                    self.logger.warning(f"Failed to play sound: {audio_type.value}")
                
                return success
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                f"playing {audio_type.value} sound",
                show_user_notification=False
            )
            return False
    
    def stop_sound(self, audio_type: AudioType) -> bool:
        """
        Stop playing a specific type of sound.
        
        Args:
            audio_type: The type of audio to stop
            
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self._initialized:
            return False
        
        try:
            with self._lock:
                return self._stop_sound_unlocked(audio_type)
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                f"stopping {audio_type.value} sound",
                show_user_notification=False
            )
            return False
    
    def _stop_sound_unlocked(self, audio_type: AudioType) -> bool:
        """
        Stop playing a specific type of sound without acquiring lock.
        
        Args:
            audio_type: The type of audio to stop
            
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        success = self.audio_backend.stop_sound(audio_type)
        
        if success:
            self.logger.debug(f"Stopped sound: {audio_type.value}")
        
        return success
    
    def stop_all_sounds(self) -> None:
        """Stop all currently playing sounds."""
        if not self._initialized:
            return
        
        try:
            with self._lock:
                for audio_type in AudioType:
                    self._stop_sound_unlocked(audio_type)
                self.logger.debug("Stopped all sounds")
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                "stopping all sounds",
                show_user_notification=False
            )
    
    def set_volume(self, audio_type: AudioType, volume: float) -> bool:
        """
        Set the volume for a specific audio type.
        
        Args:
            audio_type: The type of audio to adjust
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if volume was set successfully, False otherwise
        """
        if not (0.0 <= volume <= 1.0):
            self.logger.error(f"Invalid volume level: {volume}. Must be between 0.0 and 1.0")
            return False
        
        try:
            with self._lock:
                success = self.audio_backend.set_volume(audio_type, volume)
                
                if success:
                    self.logger.debug(f"Set volume for {audio_type.value}: {volume}")
                
                return success
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                f"setting volume for {audio_type.value}",
                show_user_notification=False
            )
            return False
    
    def set_master_volume(self, volume: float) -> bool:
        """
        Set the master volume that affects all audio types.
        
        Args:
            volume: Master volume level (0.0 to 1.0)
            
        Returns:
            bool: True if master volume was set successfully, False otherwise
        """
        if not (0.0 <= volume <= 1.0):
            self.logger.error(f"Invalid master volume level: {volume}. Must be between 0.0 and 1.0")
            return False
        
        try:
            with self._lock:
                success = self.audio_backend.set_master_volume(volume)
                
                if success:
                    self.logger.debug(f"Set master volume: {volume}")
                
                return success
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                "setting master volume",
                show_user_notification=False
            )
            return False
    
    def get_volume(self, audio_type: AudioType) -> float:
        """
        Get the current volume for a specific audio type.
        
        Args:
            audio_type: The type of audio to query
            
        Returns:
            float: Current volume level (0.0 to 1.0)
        """
        return self.audio_backend.get_volume(audio_type)
    
    def get_master_volume(self) -> float:
        """
        Get the current master volume.
        
        Returns:
            float: Current master volume level (0.0 to 1.0)
        """
        return self.audio_backend.get_master_volume()
    
    def is_playing(self, audio_type: AudioType) -> bool:
        """
        Check if a specific audio type is currently playing.
        
        Args:
            audio_type: The type of audio to check
            
        Returns:
            bool: True if the audio type is currently playing, False otherwise
        """
        if not self._initialized:
            return False
        
        try:
            return self.audio_backend.is_playing(audio_type)
        except Exception:
            return False
    
    def validate_audio_file(self, file_path: Union[str, Path]) -> bool:
        """
        Validate an audio file for compatibility.
        
        Args:
            file_path: Path to the audio file to validate
            
        Returns:
            bool: True if file is valid and compatible, False otherwise
        """
        try:
            return self.audio_backend.validate_audio_file(file_path)
        except Exception as e:
            self.logger.error(f"Error validating audio file {file_path}: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        try:
            self.logger.info("Cleaning up audio manager")
            
            # Stop all sounds
            self.stop_all_sounds()
            
            # Cleanup backend
            self.audio_backend.cleanup()
            
            self._initialized = False
            self.logger.info("Audio manager cleanup completed")
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                "audio manager cleanup",
                show_user_notification=False
            )
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during destruction