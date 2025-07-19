"""
Unit tests for AccessiClock AudioManager.

Tests audio loading, channel management, volume control, and playback functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading
import time

from src.accessiclock.managers import AudioManager, AudioType
from src.accessiclock.utils.error_handler import ErrorCategory


class TestAudioManager:
    """Test cases for AudioManager class."""
    
    @pytest.fixture
    def audio_manager(self):
        """Create an AudioManager instance for testing."""
        # Force pygame unavailable for testing
        with patch('src.accessiclock.managers.audio_manager.PYGAME_AVAILABLE', False):
            manager = AudioManager()
            yield manager
            manager.cleanup()
    
    @pytest.fixture
    def mock_sound_file(self):
        """Create a temporary mock sound file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            # Write minimal WAV header to make it a valid file
            temp_file.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
            temp_path = temp_file.name
        
        yield temp_path
        
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
    
    def test_audio_manager_initialization(self, audio_manager):
        """Test AudioManager initialization."""
        assert audio_manager._initialized is True
        assert len(audio_manager._volume_settings) == len(AudioType)
        assert audio_manager._master_volume == 1.0
        assert len(audio_manager._channels) == len(AudioType)
    
    def test_audio_manager_initialization_failure(self):
        """Test AudioManager initialization failure handling."""
        # Test with pygame available but failing to initialize
        with patch('src.accessiclock.managers.audio_manager.PYGAME_AVAILABLE', True), \
             patch('src.accessiclock.managers.audio_manager.pygame.mixer.get_init', return_value=False), \
             patch('src.accessiclock.managers.audio_manager.pygame.mixer.init', side_effect=Exception("Test error")):
            manager = AudioManager()
            assert manager._initialized is False
    
    def test_channel_assignments(self, audio_manager):
        """Test that each audio type has a unique channel assignment."""
        assignments = AudioManager.CHANNEL_ASSIGNMENTS
        
        # Check all audio types have assignments
        for audio_type in AudioType:
            assert audio_type in assignments
        
        # Check all assignments are unique
        channel_numbers = list(assignments.values())
        assert len(channel_numbers) == len(set(channel_numbers))
    
    def test_supported_formats(self):
        """Test supported audio formats."""
        formats = AudioManager.SUPPORTED_FORMATS
        assert '.wav' in formats
        assert '.ogg' in formats
        assert '.mp3' in formats
    
    @patch('src.accessiclock.managers.audio_manager.pygame.mixer.Sound')
    def test_load_sound_file_success(self, mock_sound_class, audio_manager, mock_sound_file):
        """Test successful sound file loading."""
        mock_sound = Mock()
        mock_sound_class.return_value = mock_sound
        
        result = audio_manager.load_sound_file(AudioType.TICK, mock_sound_file)
        
        assert result is True
        mock_sound_class.assert_called_once_with(mock_sound_file)
        mock_sound.set_volume.assert_called_once()
        assert AudioType.TICK in audio_manager._sound_files
    
    def test_load_sound_file_nonexistent(self, audio_manager):
        """Test loading non-existent sound file."""
        result = audio_manager.load_sound_file(AudioType.TICK, "nonexistent.wav")
        assert result is False
    
    def test_load_sound_file_unsupported_format(self, audio_manager):
        """Test loading unsupported audio format."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = audio_manager.load_sound_file(AudioType.TICK, temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)
    
    @patch('src.accessiclock.managers.audio_manager.pygame.mixer.Sound')
    def test_load_sound_file_pygame_error(self, mock_sound_class, audio_manager, mock_sound_file):
        """Test sound file loading with pygame error."""
        mock_sound_class.side_effect = Exception("Test error")
        
        result = audio_manager.load_sound_file(AudioType.TICK, mock_sound_file)
        assert result is False
    
    @patch('src.accessiclock.managers.audio_manager.pygame.mixer.Sound')
    def test_load_sound_pack(self, mock_sound_class, audio_manager, mock_sound_file):
        """Test loading multiple sound files from a sound pack."""
        mock_sound = Mock()
        mock_sound_class.return_value = mock_sound
        
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
    
    def test_load_sound_pack_empty(self, audio_manager):
        """Test loading empty sound pack."""
        results = audio_manager.load_sound_pack({})
        assert len(results) == 0
    
    def test_play_sound_success(self, audio_manager):
        """Test successful sound playback."""
        # Mock loaded sound and channel
        mock_sound = Mock()
        mock_channel = Mock()
        mock_channel.get_busy.return_value = False
        
        audio_manager._sound_files[AudioType.TICK] = mock_sound
        audio_manager._channels[AudioType.TICK] = mock_channel
        
        result = audio_manager.play_sound(AudioType.TICK)
        
        assert result is True
        mock_channel.play.assert_called_once_with(mock_sound, loops=0)
    
    def test_play_sound_with_loops(self, audio_manager):
        """Test sound playback with loops."""
        mock_sound = Mock()
        mock_channel = Mock()
        mock_channel.get_busy.return_value = False
        
        audio_manager._sound_files[AudioType.TICK] = mock_sound
        audio_manager._channels[AudioType.TICK] = mock_channel
        
        result = audio_manager.play_sound(AudioType.TICK, loops=5)
        
        assert result is True
        mock_channel.play.assert_called_once_with(mock_sound, loops=5)
    
    def test_play_sound_stop_existing(self, audio_manager):
        """Test that existing sound is stopped before playing new one."""
        mock_sound = Mock()
        mock_channel = Mock()
        mock_channel.get_busy.return_value = True  # Channel is busy
        
        audio_manager._sound_files[AudioType.TICK] = mock_sound
        audio_manager._channels[AudioType.TICK] = mock_channel
        
        result = audio_manager.play_sound(AudioType.TICK)
        
        assert result is True
        mock_channel.stop.assert_called_once()
        mock_channel.play.assert_called_once_with(mock_sound, loops=0)
    
    def test_play_sound_no_sound_loaded(self, audio_manager):
        """Test playing sound when no sound is loaded."""
        result = audio_manager.play_sound(AudioType.TICK)
        assert result is False
    
    def test_play_sound_no_channel(self, audio_manager):
        """Test playing sound when no channel is available."""
        mock_sound = Mock()
        audio_manager._sound_files[AudioType.TICK] = mock_sound
        # Don't set up channel
        
        result = audio_manager.play_sound(AudioType.TICK)
        assert result is False
    
    def test_play_sound_pygame_error(self, audio_manager):
        """Test sound playback with pygame error."""
        mock_sound = Mock()
        mock_channel = Mock()
        mock_channel.get_busy.return_value = False
        mock_channel.play.side_effect = Exception("Test error")
        
        audio_manager._sound_files[AudioType.TICK] = mock_sound
        audio_manager._channels[AudioType.TICK] = mock_channel
        
        result = audio_manager.play_sound(AudioType.TICK)
        assert result is False
    
    def test_stop_sound_success(self, audio_manager):
        """Test successful sound stopping."""
        mock_channel = Mock()
        mock_channel.get_busy.return_value = True
        
        audio_manager._channels[AudioType.TICK] = mock_channel
        
        result = audio_manager.stop_sound(AudioType.TICK)
        
        assert result is True
        mock_channel.stop.assert_called_once()
    
    def test_stop_sound_not_playing(self, audio_manager):
        """Test stopping sound when not playing."""
        mock_channel = Mock()
        mock_channel.get_busy.return_value = False
        
        audio_manager._channels[AudioType.TICK] = mock_channel
        
        result = audio_manager.stop_sound(AudioType.TICK)
        
        assert result is True
        mock_channel.stop.assert_not_called()
    
    def test_stop_sound_no_channel(self, audio_manager):
        """Test stopping sound when no channel exists."""
        result = audio_manager.stop_sound(AudioType.TICK)
        assert result is True  # Should not fail
    
    def test_stop_all_sounds(self, audio_manager):
        """Test stopping all sounds."""
        # Set up mock channels
        for audio_type in AudioType:
            mock_channel = Mock()
            mock_channel.get_busy.return_value = True
            audio_manager._channels[audio_type] = mock_channel
        
        audio_manager.stop_all_sounds()
        
        # Verify all channels were stopped
        for audio_type in AudioType:
            audio_manager._channels[audio_type].stop.assert_called_once()
    
    def test_set_volume_success(self, audio_manager):
        """Test successful volume setting."""
        mock_sound = Mock()
        audio_manager._sound_files[AudioType.TICK] = mock_sound
        
        result = audio_manager.set_volume(AudioType.TICK, 0.5)
        
        assert result is True
        assert audio_manager._volume_settings[AudioType.TICK] == 0.5
        mock_sound.set_volume.assert_called_once_with(0.5)  # 0.5 * 1.0 master volume
    
    def test_set_volume_invalid_range(self, audio_manager):
        """Test setting volume with invalid range."""
        result_low = audio_manager.set_volume(AudioType.TICK, -0.1)
        result_high = audio_manager.set_volume(AudioType.TICK, 1.1)
        
        assert result_low is False
        assert result_high is False
    
    def test_set_volume_no_sound_loaded(self, audio_manager):
        """Test setting volume when no sound is loaded."""
        result = audio_manager.set_volume(AudioType.TICK, 0.5)
        
        assert result is True
        assert audio_manager._volume_settings[AudioType.TICK] == 0.5
    
    def test_set_master_volume_success(self, audio_manager):
        """Test successful master volume setting."""
        # Set up mock sounds
        mock_sound1 = Mock()
        mock_sound2 = Mock()
        audio_manager._sound_files[AudioType.TICK] = mock_sound1
        audio_manager._sound_files[AudioType.HOUR_CHIME] = mock_sound2
        
        result = audio_manager.set_master_volume(0.8)
        
        assert result is True
        assert audio_manager._master_volume == 0.8
        
        # Check that all sounds had their volume updated
        mock_sound1.set_volume.assert_called()
        mock_sound2.set_volume.assert_called()
    
    def test_set_master_volume_invalid_range(self, audio_manager):
        """Test setting master volume with invalid range."""
        result_low = audio_manager.set_master_volume(-0.1)
        result_high = audio_manager.set_master_volume(1.1)
        
        assert result_low is False
        assert result_high is False
    
    def test_get_volume(self, audio_manager):
        """Test getting volume for audio type."""
        audio_manager._volume_settings[AudioType.TICK] = 0.7
        
        volume = audio_manager.get_volume(AudioType.TICK)
        assert volume == 0.7
    
    def test_get_volume_default(self, audio_manager):
        """Test getting volume for audio type with default value."""
        # Clear the volume setting
        del audio_manager._volume_settings[AudioType.TICK]
        
        volume = audio_manager.get_volume(AudioType.TICK)
        assert volume == 1.0  # Default value
    
    def test_get_master_volume(self, audio_manager):
        """Test getting master volume."""
        audio_manager._master_volume = 0.6
        
        volume = audio_manager.get_master_volume()
        assert volume == 0.6
    
    def test_is_playing_true(self, audio_manager):
        """Test is_playing when sound is playing."""
        mock_channel = Mock()
        mock_channel.get_busy.return_value = True
        
        audio_manager._channels[AudioType.TICK] = mock_channel
        
        result = audio_manager.is_playing(AudioType.TICK)
        assert result is True
    
    def test_is_playing_false(self, audio_manager):
        """Test is_playing when sound is not playing."""
        mock_channel = Mock()
        mock_channel.get_busy.return_value = False
        
        audio_manager._channels[AudioType.TICK] = mock_channel
        
        result = audio_manager.is_playing(AudioType.TICK)
        assert result is False
    
    def test_is_playing_no_channel(self, audio_manager):
        """Test is_playing when no channel exists."""
        result = audio_manager.is_playing(AudioType.TICK)
        assert result is False
    
    def test_get_loaded_sounds(self, audio_manager):
        """Test getting list of loaded sounds."""
        mock_sound1 = Mock()
        mock_sound2 = Mock()
        
        audio_manager._sound_files[AudioType.TICK] = mock_sound1
        audio_manager._sound_files[AudioType.HOUR_CHIME] = mock_sound2
        audio_manager._sound_files[AudioType.QUARTER_CHIME] = None
        
        loaded_sounds = audio_manager.get_loaded_sounds()
        
        assert AudioType.TICK in loaded_sounds
        assert AudioType.HOUR_CHIME in loaded_sounds
        assert AudioType.QUARTER_CHIME not in loaded_sounds
        assert len(loaded_sounds) == 2
    
    def test_validate_audio_file_success(self, audio_manager, mock_sound_file):
        """Test successful audio file validation."""
        with patch('src.accessiclock.managers.audio_manager.pygame.mixer.Sound') as mock_sound_class:
            mock_sound_class.return_value = Mock()
            
            result = audio_manager.validate_audio_file(mock_sound_file)
            assert result is True
    
    def test_validate_audio_file_nonexistent(self, audio_manager):
        """Test validation of non-existent audio file."""
        result = audio_manager.validate_audio_file("nonexistent.wav")
        assert result is False
    
    def test_validate_audio_file_unsupported_format(self, audio_manager):
        """Test validation of unsupported audio format."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = audio_manager.validate_audio_file(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)
    
    def test_validate_audio_file_pygame_error(self, audio_manager, mock_sound_file):
        """Test audio file validation with pygame error."""
        with patch('src.accessiclock.managers.audio_manager.pygame.mixer.Sound', side_effect=Exception("Test error")):
            result = audio_manager.validate_audio_file(mock_sound_file)
            assert result is False
    
    def test_thread_safety(self, audio_manager):
        """Test thread safety of audio manager operations."""
        mock_sound = Mock()
        audio_manager._sound_files[AudioType.TICK] = mock_sound
        
        results = []
        
        def set_volume_worker():
            for i in range(10):
                result = audio_manager.set_volume(AudioType.TICK, 0.5)
                results.append(result)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=set_volume_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert all(results)
        assert len(results) == 50  # 5 threads * 10 operations each
    
    def test_cleanup(self, audio_manager):
        """Test audio manager cleanup."""
        # Set up some state
        mock_sound = Mock()
        mock_channel = Mock()
        audio_manager._sound_files[AudioType.TICK] = mock_sound
        audio_manager._channels[AudioType.TICK] = mock_channel
        
        with patch('src.accessiclock.managers.audio_manager.pygame.mixer.quit') as mock_quit:
            audio_manager.cleanup()
        
        # Verify cleanup
        assert len(audio_manager._sound_files) == 0
        assert len(audio_manager._channels) == 0
        assert audio_manager._initialized is False
        mock_quit.assert_called_once()
    
    def test_cleanup_error_handling(self, audio_manager):
        """Test cleanup error handling."""
        with patch('src.accessiclock.managers.audio_manager.pygame.mixer.quit', side_effect=Exception("Test error")):
            # Should not raise exception
            audio_manager.cleanup()
    
    def test_destructor(self):
        """Test AudioManager destructor."""
        with patch('src.accessiclock.managers.audio_manager.pygame.mixer.pre_init'), \
             patch('src.accessiclock.managers.audio_manager.pygame.mixer.init'), \
             patch('src.accessiclock.managers.audio_manager.pygame.mixer.get_init', return_value=True), \
             patch('src.accessiclock.managers.audio_manager.pygame.mixer.set_num_channels'), \
             patch('src.accessiclock.managers.audio_manager.pygame.mixer.Channel'), \
             patch('src.accessiclock.managers.audio_manager.pygame.mixer.quit'):
            
            manager = AudioManager()
            cleanup_called = False
            
            original_cleanup = manager.cleanup
            def mock_cleanup():
                nonlocal cleanup_called
                cleanup_called = True
                original_cleanup()
            
            manager.cleanup = mock_cleanup
            
            # Delete the manager
            del manager
            
            # Cleanup should have been called
            assert cleanup_called


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