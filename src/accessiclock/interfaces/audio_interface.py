"""
Audio interface abstractions for AccessiClock application.

This module provides abstract interfaces for audio functionality,
allowing for easy testing and potential backend swapping.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Union, List
from pathlib import Path
from enum import Enum


class AudioType(Enum):
    """Enumeration for different audio types."""
    TICK = "tick"
    HOUR_CHIME = "hour_chime"
    QUARTER_CHIME = "quarter_chime"
    HALF_CHIME = "half_chime"
    SPEECH = "speech"


class AudioBackend(ABC):
    """Abstract interface for audio backend implementations."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the audio backend."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up audio resources."""
        pass
    
    @abstractmethod
    def load_sound_file(self, audio_type: AudioType, file_path: Union[str, Path]) -> bool:
        """Load a sound file for the specified audio type."""
        pass
    
    @abstractmethod
    def play_sound(self, audio_type: AudioType, loops: int = 0) -> bool:
        """Play a sound of the specified type."""
        pass
    
    @abstractmethod
    def stop_sound(self, audio_type: AudioType) -> bool:
        """Stop playing a specific type of sound."""
        pass
    
    @abstractmethod
    def set_volume(self, audio_type: AudioType, volume: float) -> bool:
        """Set the volume for a specific audio type."""
        pass
    
    @abstractmethod
    def set_master_volume(self, volume: float) -> bool:
        """Set the master volume that affects all audio types."""
        pass
    
    @abstractmethod
    def get_volume(self, audio_type: AudioType) -> float:
        """Get the current volume for a specific audio type."""
        pass
    
    @abstractmethod
    def get_master_volume(self) -> float:
        """Get the current master volume."""
        pass
    
    @abstractmethod
    def is_playing(self, audio_type: AudioType) -> bool:
        """Check if a specific audio type is currently playing."""
        pass
    
    @abstractmethod
    def validate_audio_file(self, file_path: Union[str, Path]) -> bool:
        """Validate an audio file for compatibility."""
        pass


class MockAudioBackend(AudioBackend):
    """Mock audio backend for testing."""
    
    def __init__(self):
        self._initialized = False
        self._sounds = {}
        self._volumes = {audio_type: 1.0 for audio_type in AudioType}
        self._master_volume = 1.0
        self._playing = {audio_type: False for audio_type in AudioType}
        self.play_calls = []  # Track play calls for testing
        self.load_calls = []  # Track load calls for testing
    
    def initialize(self) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> None:
        self._initialized = False
        self._sounds.clear()
        self._playing = {audio_type: False for audio_type in AudioType}
    
    def load_sound_file(self, audio_type: AudioType, file_path: Union[str, Path]) -> bool:
        self.load_calls.append((audio_type, str(file_path)))
        if Path(file_path).exists() and self.validate_audio_file(file_path):
            self._sounds[audio_type] = str(file_path)
            return True
        return False
    
    def play_sound(self, audio_type: AudioType, loops: int = 0) -> bool:
        self.play_calls.append((audio_type, loops))
        if audio_type in self._sounds:
            self._playing[audio_type] = True
            return True
        return False
    
    def stop_sound(self, audio_type: AudioType) -> bool:
        self._playing[audio_type] = False
        return True
    
    def set_volume(self, audio_type: AudioType, volume: float) -> bool:
        if 0.0 <= volume <= 1.0:
            self._volumes[audio_type] = volume
            return True
        return False
    
    def set_master_volume(self, volume: float) -> bool:
        if 0.0 <= volume <= 1.0:
            self._master_volume = volume
            return True
        return False
    
    def get_volume(self, audio_type: AudioType) -> float:
        return self._volumes.get(audio_type, 1.0)
    
    def get_master_volume(self) -> float:
        return self._master_volume
    
    def is_playing(self, audio_type: AudioType) -> bool:
        return self._playing.get(audio_type, False)
    
    def validate_audio_file(self, file_path: Union[str, Path]) -> bool:
        # Simple validation for testing
        path = Path(file_path)
        return path.suffix.lower() in ['.wav', '.ogg', '.mp3']