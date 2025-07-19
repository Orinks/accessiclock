"""
Unit tests for AccessiClock AudioManager.

Tests audio functionality using the MockAudioBackend for clean, fast testing.
"""

import pytest
import tempfile
import os
from pathlib import Path
import threading

from src.accessiclock.managers import AudioManager, AudioType
from src.accessiclock.interfaces import MockAudioBackend


class TestAudioManager:
    """Test cases for AudioManager class using MockAudioBackend."""
    
    @pytest.fixture
    def mock_backend(self):
        """Create a MockAudioBackend for testing."""
        return MockAudioBackend()
    
    @pytest.fixture
    def audio_manager(self, mock_backend):
        """Create an AudioManager instance with mock backend."""
        manager = AudioManager(audio_backend=mock_backend)
        yield manager
        manager.cleanup()
    
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
    
    def test_audio_manager_initialization(self, audio_manager, mock_backend):
        """Test AudioManager initialization."""
        assert audio_manager._initialized is True
        assert audio_manager.audio_backend == mock_backend
        assert mock_backend._initialized is True
    
    def test_load_sound_file_success(self, audio_manager, mock_backend, mock_sound_file):
        """Test successful sound file loading."""
        result = audio_manager.load_sound_file(AudioType.TICK, mock_sound_file)
        
        assert result is True
        assert (AudioType.TICK, mock_sound_file) in mock_backend.load_calls
        assert AudioType.TICK in mock_backend._sounds
    
    def test_load_sound_file_nonexistent(self, audio_manager, mock_backend):
        """Test loading non-existent sound file."""
        result = audio_manager.load_sound_file(AudioType.TICK, "nonexistent.wav")
        
        assert result is False
        assert AudioType.TICK not in mock_backend._sounds
    
    def test_load_sound_pack(self, audio_manager, mock_backend, mock_sound_file):
        """Test loading multiple sound files from a sound pack."""
        sound_pack = {
            'tick_sound': mock_sound_file,
            'hour_chime': mock_sound_file,
            'quarter_chime': mock_sound_file,
            'invalid_key': mock_sound_file  # Should be ignored
        }
        
        results = audio_manager.load_sound_pack(sound_pack)
        
        assert len(results) == 3  # Only valid keys should be processed
        assert AudioType.TICK in results
        assert AudioType.HOUR_CHIME in results
        assert AudioType.QUARTER_CHIME in results
        assert all(results.values())  # All should be True
    
    def test_play_sound_success(self, audio_manager, mock_backend, mock_sound_file):
        """Test successful sound playback."""
        # Load sound first
        audio_manager.load_sound_file(AudioType.TICK, mock_sound_file)
        
        result = audio_manager.play_sound(AudioType.TICK)
        
        assert result is True
        assert (AudioType.TICK, 0) in mock_backend.play_calls
        assert mock_backend.is_playing(AudioType.TICK) is True
    
    def test_play_sound_with_loops(self, audio_manager, mock_backend, mock_sound_file):
        """Test sound playback with loops."""
        audio_manager.load_sound_file(AudioType.TICK, mock_sound_file)
        
        result = audio_manager.play_sound(AudioType.TICK, loops=5)
        
        assert result is True
        assert (AudioType.TICK, 5) in mock_backend.play_calls
    
    def test_stop_sound(self, audio_manager, mock_backend, mock_sound_file):
        """Test stopping sound."""
        # Load and play sound first
        audio_manager.load_sound_file(AudioType.TICK, mock_sound_file)
        audio_manager.play_sound(AudioType.TICK)
        
        result = audio_manager.stop_sound(AudioType.TICK)
        
        assert result is True
        assert mock_backend.is_playing(AudioType.TICK) is False
    
    def test_stop_all_sounds(self, audio_manager, mock_backend, mock_sound_file):
        """Test stopping all sounds."""
        # Load and play multiple sounds
        audio_manager.load_sound_file(AudioType.TICK, mock_sound_file)
        audio_manager.load_sound_file(AudioType.HOUR_CHIME, mock_sound_file)
        audio_manager.play_sound(AudioType.TICK)
        audio_manager.play_sound(AudioType.HOUR_CHIME)
        
        audio_manager.stop_all_sounds()
        
        # All sounds should be stopped
        for audio_type in AudioType:
            assert mock_backend.is_playing(audio_type) is False
    
    def test_volume_control(self, audio_manager, mock_backend):
        """Test volume control functionality."""
        # Test individual volume
        result = audio_manager.set_volume(AudioType.TICK, 0.5)
        assert result is True
        assert audio_manager.get_volume(AudioType.TICK) == 0.5
        
        # Test master volume
        result = audio_manager.set_master_volume(0.8)
        assert result is True
        assert audio_manager.get_master_volume() == 0.8
    
    def test_volume_validation(self, audio_manager):
        """Test volume validation."""
        # Invalid volumes should fail
        assert audio_manager.set_volume(AudioType.TICK, -0.1) is False
        assert audio_manager.set_volume(AudioType.TICK, 1.1) is False
        assert audio_manager.set_master_volume(-0.1) is False
        assert audio_manager.set_master_volume(1.1) is False
    
    def test_is_playing(self, audio_manager, mock_backend, mock_sound_file):
        """Test checking if sound is playing."""
        # Initially not playing
        assert audio_manager.is_playing(AudioType.TICK) is False
        
        # Load and play sound
        audio_manager.load_sound_file(AudioType.TICK, mock_sound_file)
        audio_manager.play_sound(AudioType.TICK)
        
        # Should be playing
        assert audio_manager.is_playing(AudioType.TICK) is True
        
        # Stop sound
        audio_manager.stop_sound(AudioType.TICK)
        
        # Should not be playing
        assert audio_manager.is_playing(AudioType.TICK) is False
    
    def test_validate_audio_file(self, audio_manager, mock_sound_file):
        """Test audio file validation."""
        # Valid file
        result = audio_manager.validate_audio_file(mock_sound_file)
        assert result is True
        
        # Invalid format
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = audio_manager.validate_audio_file(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)
    
    def test_thread_safety(self, audio_manager):
        """Test thread safety of audio manager operations."""
        results = []
        
        def volume_worker():
            for i in range(10):
                result = audio_manager.set_volume(AudioType.TICK, 0.5)
                results.append(result)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=volume_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert all(results)
        assert len(results) == 50  # 5 threads * 10 operations each
    
    def test_cleanup(self, audio_manager, mock_backend):
        """Test audio manager cleanup."""
        # Load some sounds
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b'mock audio data')
            temp_path = temp_file.name
        
        try:
            audio_manager.load_sound_file(AudioType.TICK, temp_path)
            audio_manager.play_sound(AudioType.TICK)
            
            # Cleanup
            audio_manager.cleanup()
            
            # Should be cleaned up
            assert audio_manager._initialized is False
            assert mock_backend._initialized is False
        finally:
            os.unlink(temp_path)


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])