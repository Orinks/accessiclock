"""
Unit tests for AccessiClock ChimeScheduler.

Tests chime scheduling, timing logic, and simultaneous audio playback functionality.
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.accessiclock.managers import ChimeScheduler, ChimeInterval, AudioType


class TestChimeScheduler:
    """Test cases for ChimeScheduler class."""
    
    @pytest.fixture
    def mock_audio_manager(self):
        """Create a mock AudioManager for testing."""
        mock_manager = Mock()
        mock_manager.play_sound.return_value = True
        return mock_manager
    
    @pytest.fixture
    def chime_scheduler(self, mock_audio_manager):
        """Create a ChimeScheduler instance for testing."""
        scheduler = ChimeScheduler(mock_audio_manager)
        yield scheduler
        scheduler.cleanup()
    
    def test_chime_scheduler_initialization(self, chime_scheduler, mock_audio_manager):
        """Test ChimeScheduler initialization."""
        assert chime_scheduler.audio_manager == mock_audio_manager
        assert chime_scheduler._enabled is True
        assert chime_scheduler._running is False
        assert len(chime_scheduler._chime_intervals) == len(ChimeInterval)
        
        # All intervals should be enabled by default
        for interval in ChimeInterval:
            assert chime_scheduler._chime_intervals[interval] is True
    
    def test_chime_interval_enum(self):
        """Test ChimeInterval enum values."""
        assert ChimeInterval.QUARTER_HOUR.value == "quarter_hour"
        assert ChimeInterval.HALF_HOUR.value == "half_hour"
        assert ChimeInterval.HOUR.value == "hour"
    
    def test_enable_disable_scheduler(self, chime_scheduler):
        """Test enabling and disabling the scheduler."""
        # Initially enabled
        assert chime_scheduler.is_enabled() is True
        
        # Disable
        chime_scheduler.set_enabled(False)
        assert chime_scheduler.is_enabled() is False
        
        # Enable
        chime_scheduler.set_enabled(True)
        assert chime_scheduler.is_enabled() is True
    
    def test_start_stop_scheduler(self, chime_scheduler):
        """Test starting and stopping the scheduler."""
        # Initially not running
        assert chime_scheduler.is_running() is False
        
        # Start
        result = chime_scheduler.start()
        assert result is True
        assert chime_scheduler.is_running() is True
        
        # Stop
        result = chime_scheduler.stop()
        assert result is True
        assert chime_scheduler.is_running() is False
    
    def test_start_when_disabled(self, chime_scheduler):
        """Test starting scheduler when disabled."""
        chime_scheduler.set_enabled(False)
        
        result = chime_scheduler.start()
        assert result is False
        assert chime_scheduler.is_running() is False
    
    def test_start_when_already_running(self, chime_scheduler):
        """Test starting scheduler when already running."""
        chime_scheduler.start()
        
        # Try to start again
        result = chime_scheduler.start()
        assert result is True  # Should succeed but not create new thread
        assert chime_scheduler.is_running() is True
    
    def test_stop_when_not_running(self, chime_scheduler):
        """Test stopping scheduler when not running."""
        result = chime_scheduler.stop()
        assert result is True
        assert chime_scheduler.is_running() is False
    
    def test_chime_interval_configuration(self, chime_scheduler):
        """Test configuring individual chime intervals."""
        # Test setting intervals
        chime_scheduler.set_chime_interval_enabled(ChimeInterval.QUARTER_HOUR, False)
        assert chime_scheduler.is_chime_interval_enabled(ChimeInterval.QUARTER_HOUR) is False
        assert chime_scheduler.is_chime_interval_enabled(ChimeInterval.HOUR) is True
        
        chime_scheduler.set_chime_interval_enabled(ChimeInterval.HOUR, False)
        assert chime_scheduler.is_chime_interval_enabled(ChimeInterval.HOUR) is False
        
        # Re-enable
        chime_scheduler.set_chime_interval_enabled(ChimeInterval.QUARTER_HOUR, True)
        assert chime_scheduler.is_chime_interval_enabled(ChimeInterval.QUARTER_HOUR) is True
    
    def test_chime_callbacks(self, chime_scheduler):
        """Test setting and calling chime callbacks."""
        callback_called = []
        
        def test_callback(interval, timestamp):
            callback_called.append((interval, timestamp))
        
        # Set callback
        chime_scheduler.set_chime_callback(ChimeInterval.HOUR, test_callback)
        
        # Trigger chime manually
        result = chime_scheduler.trigger_chime_now(ChimeInterval.HOUR)
        assert result is True
        
        # Check callback was called
        assert len(callback_called) == 1
        assert callback_called[0][0] == ChimeInterval.HOUR
        assert isinstance(callback_called[0][1], datetime)
        
        # Remove callback
        chime_scheduler.set_chime_callback(ChimeInterval.HOUR, None)
        
        # Trigger again - callback should not be called
        callback_called.clear()
        chime_scheduler.trigger_chime_now(ChimeInterval.HOUR)
        assert len(callback_called) == 0
    
    def test_trigger_chime_now(self, chime_scheduler, mock_audio_manager):
        """Test manually triggering chimes."""
        # Test each chime type
        result = chime_scheduler.trigger_chime_now(ChimeInterval.HOUR)
        assert result is True
        mock_audio_manager.play_sound.assert_called_with(AudioType.HOUR_CHIME)
        
        result = chime_scheduler.trigger_chime_now(ChimeInterval.HALF_HOUR)
        assert result is True
        mock_audio_manager.play_sound.assert_called_with(AudioType.HALF_CHIME)
        
        result = chime_scheduler.trigger_chime_now(ChimeInterval.QUARTER_HOUR)
        assert result is True
        mock_audio_manager.play_sound.assert_called_with(AudioType.QUARTER_CHIME)
    
    def test_trigger_chime_when_disabled(self, chime_scheduler):
        """Test triggering chime when scheduler is disabled."""
        chime_scheduler.set_enabled(False)
        
        result = chime_scheduler.trigger_chime_now(ChimeInterval.HOUR)
        assert result is False
    
    def test_trigger_chime_audio_failure(self, chime_scheduler, mock_audio_manager):
        """Test triggering chime when audio manager fails."""
        mock_audio_manager.play_sound.return_value = False
        
        result = chime_scheduler.trigger_chime_now(ChimeInterval.HOUR)
        assert result is False
    
    def test_get_next_chime_time_quarter_hour(self, chime_scheduler):
        """Test calculating next quarter-hour chime time."""
        # Mock current time to 10:07
        with patch('src.accessiclock.managers.chime_scheduler.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 10, 7, 30)
            mock_datetime.now.return_value = mock_now
            
            # Only enable quarter hour chimes
            chime_scheduler.set_chime_interval_enabled(ChimeInterval.HALF_HOUR, False)
            chime_scheduler.set_chime_interval_enabled(ChimeInterval.HOUR, False)
            
            next_time = chime_scheduler.get_next_chime_time()
            
            # Should be 10:15
            expected = datetime(2023, 1, 1, 10, 15, 0)
            assert next_time == expected
    
    def test_get_next_chime_time_half_hour(self, chime_scheduler):
        """Test calculating next half-hour chime time."""
        with patch('src.accessiclock.managers.chime_scheduler.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 10, 20, 0)
            mock_datetime.now.return_value = mock_now
            
            # Only enable half hour chimes
            chime_scheduler.set_chime_interval_enabled(ChimeInterval.QUARTER_HOUR, False)
            chime_scheduler.set_chime_interval_enabled(ChimeInterval.HOUR, False)
            
            next_time = chime_scheduler.get_next_chime_time()
            
            # Should be 10:30
            expected = datetime(2023, 1, 1, 10, 30, 0)
            assert next_time == expected
    
    def test_get_next_chime_time_hour(self, chime_scheduler):
        """Test calculating next hour chime time."""
        with patch('src.accessiclock.managers.chime_scheduler.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 10, 45, 0)
            mock_datetime.now.return_value = mock_now
            
            # Only enable hour chimes
            chime_scheduler.set_chime_interval_enabled(ChimeInterval.QUARTER_HOUR, False)
            chime_scheduler.set_chime_interval_enabled(ChimeInterval.HALF_HOUR, False)
            
            next_time = chime_scheduler.get_next_chime_time()
            
            # Should be 11:00
            expected = datetime(2023, 1, 1, 11, 0, 0)
            assert next_time == expected
    
    def test_get_next_chime_time_disabled(self, chime_scheduler):
        """Test getting next chime time when scheduler is disabled."""
        chime_scheduler.set_enabled(False)
        
        next_time = chime_scheduler.get_next_chime_time()
        assert next_time is None
    
    def test_get_next_chime_time_no_intervals_enabled(self, chime_scheduler):
        """Test getting next chime time when no intervals are enabled."""
        # Disable all intervals
        for interval in ChimeInterval:
            chime_scheduler.set_chime_interval_enabled(interval, False)
        
        next_time = chime_scheduler.get_next_chime_time()
        assert next_time is None
    
    def test_check_and_play_chimes_hour(self, chime_scheduler, mock_audio_manager):
        """Test playing chimes at the top of the hour."""
        # Mock time to exactly 10:00
        test_time = datetime(2023, 1, 1, 10, 0, 0)
        
        chime_scheduler._check_and_play_chimes(test_time)
        
        # Should play hour chime
        mock_audio_manager.play_sound.assert_called_with(AudioType.HOUR_CHIME)
    
    def test_check_and_play_chimes_half_hour(self, chime_scheduler, mock_audio_manager):
        """Test playing chimes at half past the hour."""
        # Mock time to exactly 10:30
        test_time = datetime(2023, 1, 1, 10, 30, 0)
        
        chime_scheduler._check_and_play_chimes(test_time)
        
        # Should play half hour chime
        mock_audio_manager.play_sound.assert_called_with(AudioType.HALF_CHIME)
    
    def test_check_and_play_chimes_quarter_hour(self, chime_scheduler, mock_audio_manager):
        """Test playing chimes at quarter past the hour."""
        # Mock time to exactly 10:15
        test_time = datetime(2023, 1, 1, 10, 15, 0)
        
        chime_scheduler._check_and_play_chimes(test_time)
        
        # Should play quarter hour chime
        mock_audio_manager.play_sound.assert_called_with(AudioType.QUARTER_CHIME)
        
        # Test 45 minutes past
        test_time = datetime(2023, 1, 1, 10, 45, 0)
        mock_audio_manager.reset_mock()
        
        chime_scheduler._check_and_play_chimes(test_time)
        mock_audio_manager.play_sound.assert_called_with(AudioType.QUARTER_CHIME)
    
    def test_check_and_play_chimes_no_chime_time(self, chime_scheduler, mock_audio_manager):
        """Test that no chimes play at non-chime times."""
        # Mock time to 10:07 (not a chime time)
        test_time = datetime(2023, 1, 1, 10, 7, 0)
        
        chime_scheduler._check_and_play_chimes(test_time)
        
        # Should not play any chimes
        mock_audio_manager.play_sound.assert_not_called()
    
    def test_check_and_play_chimes_disabled_intervals(self, chime_scheduler, mock_audio_manager):
        """Test that disabled intervals don't play chimes."""
        # Disable hour chimes
        chime_scheduler.set_chime_interval_enabled(ChimeInterval.HOUR, False)
        
        # Mock time to exactly 10:00
        test_time = datetime(2023, 1, 1, 10, 0, 0)
        
        chime_scheduler._check_and_play_chimes(test_time)
        
        # Should not play hour chime
        mock_audio_manager.play_sound.assert_not_called()
    
    def test_get_status(self, chime_scheduler):
        """Test getting scheduler status."""
        status = chime_scheduler.get_status()
        
        assert 'enabled' in status
        assert 'running' in status
        assert 'chime_intervals' in status
        assert 'next_chime_time' in status
        
        assert status['enabled'] is True
        assert status['running'] is False
        assert len(status['chime_intervals']) == len(ChimeInterval)
    
    def test_cleanup(self, chime_scheduler):
        """Test scheduler cleanup."""
        # Start scheduler first
        chime_scheduler.start()
        assert chime_scheduler.is_running() is True
        
        # Set a callback
        chime_scheduler.set_chime_callback(ChimeInterval.HOUR, lambda i, t: None)
        
        # Cleanup
        chime_scheduler.cleanup()
        
        # Should be stopped and callbacks cleared
        assert chime_scheduler.is_running() is False
        assert chime_scheduler._chime_callbacks[ChimeInterval.HOUR] is None
    
    def test_thread_safety(self, chime_scheduler):
        """Test thread safety of scheduler operations."""
        results = []
        
        def worker():
            for i in range(10):
                chime_scheduler.set_chime_interval_enabled(ChimeInterval.HOUR, i % 2 == 0)
                results.append(chime_scheduler.is_chime_interval_enabled(ChimeInterval.HOUR))
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All operations should complete without error
        assert len(results) == 30  # 3 threads * 10 operations each
    
    def test_scheduler_loop_integration(self, chime_scheduler, mock_audio_manager):
        """Test scheduler loop integration (short duration)."""
        # This test runs the actual scheduler loop for a very short time
        # to verify it doesn't crash
        
        with patch('src.accessiclock.managers.chime_scheduler.datetime') as mock_datetime:
            # Mock time to just before a chime
            mock_now = datetime(2023, 1, 1, 10, 59, 58)
            mock_datetime.now.return_value = mock_now
            
            # Start scheduler
            chime_scheduler.start()
            
            # Let it run briefly
            time.sleep(0.1)
            
            # Stop scheduler
            chime_scheduler.stop()
            
            # Should have stopped cleanly
            assert chime_scheduler.is_running() is False


class TestChimeInterval:
    """Test cases for ChimeInterval enum."""
    
    def test_chime_interval_values(self):
        """Test ChimeInterval enum values."""
        assert ChimeInterval.QUARTER_HOUR.value == "quarter_hour"
        assert ChimeInterval.HALF_HOUR.value == "half_hour"
        assert ChimeInterval.HOUR.value == "hour"
    
    def test_chime_interval_membership(self):
        """Test ChimeInterval membership checks."""
        intervals = [ci.value for ci in ChimeInterval]
        assert "quarter_hour" in intervals
        assert "half_hour" in intervals
        assert "hour" in intervals
        assert "invalid" not in intervals


if __name__ == "__main__":
    pytest.main([__file__, "-v"])