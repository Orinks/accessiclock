"""
Unit tests for AccessiClock audio interfaces.

Tests the audio interface abstractions without any pygame dependencies.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.accessiclock.interfaces import MockAudioBackend, AudioType


class TestAudioType:
    """Test cases for AudioType enum."""
    
    def test_audio_type_values(self):
        """Test AudioType enum values."""
        assert AudioType.TICK.value == "tick"
        assert AudioType.HOUR_CHIME.value == "hour_chime"
        assert AudioType.QUARTER_CHIME.value == "quarter_chime"
        assert AudioType.HALF_CHIME.value == "half_chime"
        assert AudioType.SPEECH.value == "speech"
    
    def test_audio_type_membership(self):
        """Test AudioType membership checks."""
        audio_types = [at.value for at in AudioType]
        assert "tick" in audio_types
        assert "hour_chime" in audio_types
        assert "quarter_chime" in audio_types
        assert "half_chime" in audio_types
        assert "speech" in audio_types
        assert "invalid" not in audio_types


class TestMockAudioBackend:
    """Test cases for MockAudioBackend class."""
    
    @pytest.fixture
    def mock_backend(self):
        """Create a MockAudioBackend for testing."""
        backend = MockAudioBackend()
        backend.initialize()
        yield backend
        backend.cleanup()
    
    @pytest.fixture
    def mock_sound_file(self):
        """Create a temporary mock sound file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b'mock audio data')
            temp_path = temp_file.name
        
        yield temp_path
        
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
    
    def test_mock_backend_initialization(self, mock_backend):
        """Test MockAudioBackend initialization."""
        assert mock_backend._initialized is True
        assert len(mock_backend._volumes) == len(AudioType)
        assert mock_backend._master_volume == 1.0
        assert len(mock_backend._playing) == len(AudioType)
        assert all(not playing for playing in mock_backend._playing.values())
    
    def test_mock_backend_load_sound_file(self, mock_backend, mock_sound_file):
        """Test loading sound files with mock backend."""
        result = mock_backend.load_sound_file(AudioType.TICK, mock_sound_file)
        
        assert result is True
        assert (AudioType.TICK, mock_sound_file) in mock_backend.load_calls
        assert AudioType.TICK in mock_backend._sounds
        assert mock_backend._sounds[AudioType.TICK] == mock_sound_file
    
    def test_mock_backend_load_nonexistent_file(self, mock_backend):
        """Test loading non-existent sound file."""
        result = mock_backend.load_sound_file(AudioType.TICK, "nonexistent.wav")
        
        assert result is False
        assert AudioType.TICK not in mock_backend._sounds
    
    def test_mock_backend_load_unsupported_format(self, mock_backend):
        """Test loading unsupported audio format."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = mock_backend.load_sound_file(AudioType.TICK, temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)
    
    def test_mock_backend_play_sound(self, mock_backend, mock_sound_file):
        """Test playing sounds with mock backend."""
        # Load sound first
        mock_backend.load_sound_file(AudioType.TICK, mock_sound_file)
        
        # Play sound
        result = mock_backend.play_sound(AudioType.TICK)
        
        assert result is True
        assert (AudioType.TICK, 0) in mock_backend.play_calls
        assert mock_backend.is_playing(AudioType.TICK) is True
    
    def test_mock_backend_play_sound_with_loops(self, mock_backend, mock_sound_file):
        """Test playing sounds with loops."""
        mock_backend.load_sound_file(AudioType.TICK, mock_sound_file)
        
        result = mock_backend.play_sound(AudioType.TICK, loops=5)
        
        assert result is True
        assert (AudioType.TICK, 5) in mock_backend.play_calls
    
    def test_mock_backend_play_unloaded_sound(self, mock_backend):
        """Test playing sound that hasn't been loaded."""
        result = mock_backend.play_sound(AudioType.TICK)
        
        assert result is False
        assert mock_backend.is_playing(AudioType.TICK) is False
    
    def test_mock_backend_stop_sound(self, mock_backend, mock_sound_file):
        """Test stopping sounds."""
        # Load and play sound
        mock_backend.load_sound_file(AudioType.TICK, mock_sound_file)
        mock_backend.play_sound(AudioType.TICK)
        
        # Stop sound
        result = mock_backend.stop_sound(AudioType.TICK)
        
        assert result is True
        assert mock_backend.is_playing(AudioType.TICK) is False
    
    def test_mock_backend_volume_control(self, mock_backend):
        """Test volume control with mock backend."""
        # Set individual volume
        result = mock_backend.set_volume(AudioType.TICK, 0.5)
        assert result is True
        assert mock_backend.get_volume(AudioType.TICK) == 0.5
        
        # Set master volume
        result = mock_backend.set_master_volume(0.8)
        assert result is True
        assert mock_backend.get_master_volume() == 0.8
    
    def test_mock_backend_volume_validation(self, mock_backend):
        """Test volume validation."""
        # Invalid volumes should fail
        assert mock_backend.set_volume(AudioType.TICK, -0.1) is False
        assert mock_backend.set_volume(AudioType.TICK, 1.1) is False
        assert mock_backend.set_master_volume(-0.1) is False
        assert mock_backend.set_master_volume(1.1) is False
        
        # Valid volumes should succeed
        assert mock_backend.set_volume(AudioType.TICK, 0.0) is True
        assert mock_backend.set_volume(AudioType.TICK, 1.0) is True
        assert mock_backend.set_master_volume(0.0) is True
        assert mock_backend.set_master_volume(1.0) is True
    
    def test_mock_backend_file_validation(self, mock_backend):
        """Test file validation with mock backend."""
        # Supported formats
        assert mock_backend.validate_audio_file("test.wav") is True
        assert mock_backend.validate_audio_file("test.ogg") is True
        assert mock_backend.validate_audio_file("test.mp3") is True
        assert mock_backend.validate_audio_file("test.WAV") is True  # Case insensitive
        
        # Unsupported formats
        assert mock_backend.validate_audio_file("test.txt") is False
        assert mock_backend.validate_audio_file("test.doc") is False
        assert mock_backend.validate_audio_file("test") is False
    
    def test_mock_backend_cleanup(self, mock_backend):
        """Test mock backend cleanup."""
        # Load some sounds
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b'mock audio data')
            temp_path = temp_file.name
        
        try:
            mock_backend.load_sound_file(AudioType.TICK, temp_path)
            mock_backend.play_sound(AudioType.TICK)
            
            # Cleanup
            mock_backend.cleanup()
            
            # Should be cleaned up
            assert mock_backend._initialized is False
            assert len(mock_backend._sounds) == 0
            assert all(not playing for playing in mock_backend._playing.values())
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])