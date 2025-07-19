"""
Pygame audio backend implementation for AccessiClock application.

This module provides the PygameAudioBackend class that implements the AudioBackend
interface using pygame.mixer for actual audio playback.
"""

from pathlib import Path
from typing import Dict, Optional, Union, List
import threading

from ..interfaces.audio_interface import AudioBackend, AudioType
from ..utils.logging_config import get_logger
from ..utils.error_handler import get_error_handler, ErrorCategory

# Import pygame only when needed to avoid test hanging issues
try:
    import pygame
    import pygame.mixer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    # Create mock pygame for when it's not available
    class MockPygame:
        class error(Exception):
            pass
        
        class mixer:
            @staticmethod
            def pre_init(*args, **kwargs):
                pass
            
            @staticmethod
            def init():
                pass
            
            @staticmethod
            def get_init():
                return False  # Indicate not initialized when pygame unavailable
            
            @staticmethod
            def set_num_channels(num):
                pass
            
            @staticmethod
            def quit():
                pass
            
            class Sound:
                def __init__(self, file_path):
                    raise Exception("Pygame not available")
                
                def set_volume(self, volume):
                    pass
            
            class Channel:
                def __init__(self, channel_num):
                    self.channel_num = channel_num
                
                def get_busy(self):
                    return False
                
                def play(self, sound, loops=0):
                    pass
                
                def stop(self):
                    pass
        
        error = Exception
    
    pygame = MockPygame()


class PygameAudioBackend(AudioBackend):
    """
    Pygame implementation of the AudioBackend interface.
    
    Uses pygame.mixer for simultaneous audio playback with individual channel
    management for different audio types.
    """
    
    # Audio channel assignments
    CHANNEL_ASSIGNMENTS = {
        AudioType.TICK: 0,
        AudioType.HOUR_CHIME: 1,
        AudioType.QUARTER_CHIME: 2,
        AudioType.HALF_CHIME: 3,
        AudioType.SPEECH: 4
    }
    
    # Supported audio formats
    SUPPORTED_FORMATS = ['.wav', '.ogg', '.mp3']
    
    def __init__(self, error_handler=None):
        """
        Initialize the PygameAudioBackend.
        
        Args:
            error_handler: Optional error handler instance
        """
        self.logger = get_logger("pygame_audio_backend")
        self.error_handler = error_handler or get_error_handler()
        
        # Audio state
        self._initialized = False
        self._sound_files: Dict[AudioType, Optional[pygame.mixer.Sound]] = {}
        self._volume_settings: Dict[AudioType, float] = {
            AudioType.TICK: 0.8,
            AudioType.HOUR_CHIME: 1.0,
            AudioType.QUARTER_CHIME: 1.0,
            AudioType.HALF_CHIME: 1.0,
            AudioType.SPEECH: 0.9
        }
        self._master_volume: float = 1.0
        self._channels: Dict[AudioType, pygame.mixer.Channel] = {}
        
        # Thread safety
        self._lock = threading.Lock()
    
    def initialize(self) -> bool:
        """Initialize the pygame audio backend."""
        try:
            # Check if pygame is available
            if not PYGAME_AVAILABLE:
                self.logger.warning("Pygame not available, backend initialization failed")
                return False
            
            # Initialize pygame mixer if not already initialized
            if not pygame.mixer.get_init():
                # Initialize with high quality settings
                pygame.mixer.pre_init(
                    frequency=44100,  # High quality sample rate
                    size=-16,         # 16-bit signed samples
                    channels=2,       # Stereo
                    buffer=1024       # Small buffer for low latency
                )
                pygame.mixer.init()
            
            # Reserve channels for our audio types
            num_channels = len(self.CHANNEL_ASSIGNMENTS)
            pygame.mixer.set_num_channels(max(num_channels, 8))  # Ensure we have enough channels
            
            # Get channel objects
            for audio_type, channel_num in self.CHANNEL_ASSIGNMENTS.items():
                try:
                    self._channels[audio_type] = pygame.mixer.Channel(channel_num)
                except (pygame.error, AttributeError):
                    # Create a mock channel for testing or when pygame is not available
                    self._channels[audio_type] = None
            
            self._initialized = True
            self.logger.info("Pygame audio backend initialized successfully")
            return True
            
        except pygame.error as e:
            self.logger.warning(f"Pygame mixer initialization failed: {e}")
            self._initialized = False
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    "pygame backend initialization",
                    show_user_notification=False
                )
            return False
        except Exception as e:
            self.logger.warning(f"Pygame audio backend initialization failed: {e}")
            self._initialized = False
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    "pygame backend initialization",
                    show_user_notification=False
                )
            return False
    
    def cleanup(self) -> None:
        """Clean up pygame audio resources."""
        try:
            self.logger.info("Cleaning up pygame audio backend")
            
            # Stop all sounds
            with self._lock:
                for audio_type in AudioType:
                    self.stop_sound(audio_type)
                
                # Clear sound files and channels
                self._sound_files.clear()
                self._channels.clear()
            
            # Quit pygame mixer
            if PYGAME_AVAILABLE and pygame.mixer.get_init():
                pygame.mixer.quit()
            
            self._initialized = False
            self.logger.info("Pygame audio backend cleanup completed")
            
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    "pygame backend cleanup",
                    show_user_notification=False
                )
    
    def load_sound_file(self, audio_type: AudioType, file_path: Union[str, Path]) -> bool:
        """Load a sound file for the specified audio type."""
        if not self._initialized:
            self.logger.error("Pygame backend not initialized")
            return False
        
        try:
            file_path = Path(file_path)
            
            # Validate file exists
            if not file_path.exists():
                raise FileNotFoundError(f"Audio file not found: {file_path}")
            
            # Validate file format
            if not self._is_supported_format(file_path):
                raise ValueError(f"Unsupported audio format: {file_path.suffix}")
            
            with self._lock:
                # Load the sound
                sound = pygame.mixer.Sound(str(file_path))
                
                # Set initial volume
                volume = self._volume_settings.get(audio_type, 1.0) * self._master_volume
                sound.set_volume(volume)
                
                # Store the sound
                self._sound_files[audio_type] = sound
                
                self.logger.info(f"Loaded sound file for {audio_type.value}: {file_path}")
                return True
                
        except (pygame.error, FileNotFoundError, ValueError) as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    f"loading sound file for {audio_type.value}",
                    show_user_notification=False
                )
            return False
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    f"loading sound file for {audio_type.value}",
                    show_user_notification=False
                )
            return False
    
    def play_sound(self, audio_type: AudioType, loops: int = 0) -> bool:
        """Play a sound of the specified type."""
        if not self._initialized:
            self.logger.error("Pygame backend not initialized")
            return False
        
        try:
            with self._lock:
                # Check if sound is loaded
                sound = self._sound_files.get(audio_type)
                if sound is None:
                    self.logger.warning(f"No sound loaded for {audio_type.value}")
                    return False
                
                # Get the channel for this audio type
                channel = self._channels.get(audio_type)
                if channel is None:
                    self.logger.error(f"No channel assigned for {audio_type.value}")
                    return False
                
                # Stop any currently playing sound on this channel
                if channel.get_busy():
                    channel.stop()
                
                # Play the sound
                channel.play(sound, loops=loops)
                
                self.logger.debug(f"Playing sound: {audio_type.value}")
                return True
                
        except pygame.error as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    f"playing {audio_type.value} sound",
                    show_user_notification=False
                )
            return False
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    f"playing {audio_type.value} sound",
                    show_user_notification=False
                )
            return False
    
    def stop_sound(self, audio_type: AudioType) -> bool:
        """Stop playing a specific type of sound."""
        if not self._initialized:
            return False
        
        try:
            with self._lock:
                channel = self._channels.get(audio_type)
                if channel and channel.get_busy():
                    channel.stop()
                    self.logger.debug(f"Stopped sound: {audio_type.value}")
                return True
                
        except pygame.error as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    f"stopping {audio_type.value} sound",
                    show_user_notification=False
                )
            return False
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    f"stopping {audio_type.value} sound",
                    show_user_notification=False
                )
            return False
    
    def set_volume(self, audio_type: AudioType, volume: float) -> bool:
        """Set the volume for a specific audio type."""
        if not (0.0 <= volume <= 1.0):
            self.logger.error(f"Invalid volume level: {volume}. Must be between 0.0 and 1.0")
            return False
        
        try:
            with self._lock:
                # Update volume setting
                self._volume_settings[audio_type] = volume
                
                # Apply to loaded sound if available
                sound = self._sound_files.get(audio_type)
                if sound:
                    effective_volume = volume * self._master_volume
                    sound.set_volume(effective_volume)
                
                self.logger.debug(f"Set volume for {audio_type.value}: {volume}")
                return True
                
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    f"setting volume for {audio_type.value}",
                    show_user_notification=False
                )
            return False
    
    def set_master_volume(self, volume: float) -> bool:
        """Set the master volume that affects all audio types."""
        if not (0.0 <= volume <= 1.0):
            self.logger.error(f"Invalid master volume level: {volume}. Must be between 0.0 and 1.0")
            return False
        
        try:
            with self._lock:
                self._master_volume = volume
                
                # Update all loaded sounds with new master volume
                for audio_type, sound in self._sound_files.items():
                    if sound:
                        type_volume = self._volume_settings.get(audio_type, 1.0)
                        effective_volume = type_volume * self._master_volume
                        sound.set_volume(effective_volume)
                
                self.logger.debug(f"Set master volume: {volume}")
                return True
                
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.AUDIO,
                    "setting master volume",
                    show_user_notification=False
                )
            return False
    
    def get_volume(self, audio_type: AudioType) -> float:
        """Get the current volume for a specific audio type."""
        return self._volume_settings.get(audio_type, 1.0)
    
    def get_master_volume(self) -> float:
        """Get the current master volume."""
        return self._master_volume
    
    def is_playing(self, audio_type: AudioType) -> bool:
        """Check if a specific audio type is currently playing."""
        if not self._initialized:
            return False
        
        try:
            channel = self._channels.get(audio_type)
            return channel.get_busy() if channel else False
        except Exception:
            return False
    
    def validate_audio_file(self, file_path: Union[str, Path]) -> bool:
        """Validate an audio file for compatibility."""
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                self.logger.error(f"Audio file not found: {file_path}")
                return False
            
            # Check file format
            if not self._is_supported_format(file_path):
                self.logger.error(f"Unsupported audio format: {file_path.suffix}")
                return False
            
            # Try to load the file to verify it's valid (only if pygame is available)
            if PYGAME_AVAILABLE:
                try:
                    test_sound = pygame.mixer.Sound(str(file_path))
                    # If we get here, the file is valid
                    del test_sound  # Clean up
                    return True
                except pygame.error as e:
                    self.logger.error(f"Invalid audio file {file_path}: {e}")
                    return False
            else:
                # If pygame not available, just check format
                return True
                
        except Exception as e:
            self.logger.error(f"Error validating audio file {file_path}: {e}")
            return False
    
    def _is_supported_format(self, file_path: Path) -> bool:
        """Check if the audio file format is supported."""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS