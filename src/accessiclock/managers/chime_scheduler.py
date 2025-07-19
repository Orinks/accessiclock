"""
Chime Scheduler for AccessiClock application.

This module provides the ChimeScheduler class that handles chime timing logic
for hourly and quarter-hour intervals, with support for simultaneous ticking
and chime playback.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
from enum import Enum

from ..utils.logging_config import get_logger
from ..utils.error_handler import get_error_handler, ErrorCategory
from .audio_manager import AudioManager, AudioType


class ChimeInterval(Enum):
    """Enumeration for chime intervals."""
    QUARTER_HOUR = "quarter_hour"  # Every 15 minutes
    HALF_HOUR = "half_hour"        # Every 30 minutes
    HOUR = "hour"                  # Every hour


class ChimeScheduler:
    """
    Manages chime scheduling and playback for the AccessiClock application.
    
    Handles timing logic for hourly and quarter-hour chimes with support for
    simultaneous ticking and chime playback using the AudioManager.
    """
    
    def __init__(self, audio_manager: AudioManager, error_handler=None):
        """
        Initialize the ChimeScheduler.
        
        Args:
            audio_manager: AudioManager instance for playing chimes
            error_handler: Optional error handler instance
        """
        self.logger = get_logger("chime_scheduler")
        self.error_handler = error_handler or get_error_handler()
        self.audio_manager = audio_manager
        
        # Scheduling state
        self._enabled = True
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Chime configuration
        self._chime_intervals: Dict[ChimeInterval, bool] = {
            ChimeInterval.QUARTER_HOUR: True,
            ChimeInterval.HALF_HOUR: True,
            ChimeInterval.HOUR: True
        }
        
        # Callbacks for chime events
        self._chime_callbacks: Dict[ChimeInterval, Optional[Callable]] = {
            ChimeInterval.QUARTER_HOUR: None,
            ChimeInterval.HALF_HOUR: None,
            ChimeInterval.HOUR: None
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        self.logger.info("ChimeScheduler initialized")
    
    def start(self) -> bool:
        """
        Start the chime scheduler.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            with self._lock:
                if self._running:
                    self.logger.warning("ChimeScheduler is already running")
                    return True
                
                if not self._enabled:
                    self.logger.info("ChimeScheduler is disabled, not starting")
                    return False
                
                # Reset stop event
                self._stop_event.clear()
                
                # Create and start scheduler thread
                self._scheduler_thread = threading.Thread(
                    target=self._scheduler_loop,
                    name="ChimeScheduler",
                    daemon=True
                )
                self._scheduler_thread.start()
                
                self._running = True
                self.logger.info("ChimeScheduler started")
                return True
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                "starting chime scheduler",
                show_user_notification=False
            )
            return False
    
    def stop(self) -> bool:
        """
        Stop the chime scheduler.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            with self._lock:
                if not self._running:
                    self.logger.info("ChimeScheduler is not running")
                    return True
                
                # Signal stop
                self._stop_event.set()
                
                # Wait for thread to finish
                if self._scheduler_thread and self._scheduler_thread.is_alive():
                    self._scheduler_thread.join(timeout=2.0)
                    
                    if self._scheduler_thread.is_alive():
                        self.logger.warning("ChimeScheduler thread did not stop gracefully")
                
                self._running = False
                self._scheduler_thread = None
                self.logger.info("ChimeScheduler stopped")
                return True
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                "stopping chime scheduler",
                show_user_notification=False
            )
            return False
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the chime scheduler.
        
        Args:
            enabled: True to enable chimes, False to disable
        """
        with self._lock:
            was_running = self._running
            
            if not enabled and was_running:
                self.stop()
            
            self._enabled = enabled
            
            if enabled and not was_running and not self._running:
                self.start()
            
            self.logger.info(f"ChimeScheduler {'enabled' if enabled else 'disabled'}")
    
    def is_enabled(self) -> bool:
        """
        Check if the chime scheduler is enabled.
        
        Returns:
            bool: True if enabled, False otherwise
        """
        return self._enabled
    
    def is_running(self) -> bool:
        """
        Check if the chime scheduler is running.
        
        Returns:
            bool: True if running, False otherwise
        """
        return self._running
    
    def set_chime_interval_enabled(self, interval: ChimeInterval, enabled: bool) -> None:
        """
        Enable or disable a specific chime interval.
        
        Args:
            interval: The chime interval to configure
            enabled: True to enable, False to disable
        """
        with self._lock:
            self._chime_intervals[interval] = enabled
            self.logger.info(f"Chime interval {interval.value} {'enabled' if enabled else 'disabled'}")
    
    def is_chime_interval_enabled(self, interval: ChimeInterval) -> bool:
        """
        Check if a specific chime interval is enabled.
        
        Args:
            interval: The chime interval to check
            
        Returns:
            bool: True if enabled, False otherwise
        """
        return self._chime_intervals.get(interval, False)
    
    def set_chime_callback(self, interval: ChimeInterval, callback: Optional[Callable]) -> None:
        """
        Set a callback function to be called when a chime occurs.
        
        Args:
            interval: The chime interval for the callback
            callback: Function to call when chime occurs (or None to remove)
        """
        with self._lock:
            self._chime_callbacks[interval] = callback
            self.logger.debug(f"Chime callback {'set' if callback else 'removed'} for {interval.value}")
    
    def trigger_chime_now(self, interval: ChimeInterval) -> bool:
        """
        Manually trigger a chime immediately.
        
        Args:
            interval: The type of chime to trigger
            
        Returns:
            bool: True if chime was triggered successfully, False otherwise
        """
        try:
            if not self._enabled:
                self.logger.info("ChimeScheduler is disabled, not triggering chime")
                return False
            
            return self._play_chime(interval)
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                f"manually triggering {interval.value} chime",
                show_user_notification=False
            )
            return False
    
    def get_next_chime_time(self) -> Optional[datetime]:
        """
        Get the next scheduled chime time.
        
        Returns:
            datetime: Next chime time, or None if no chimes are enabled
        """
        if not self._enabled:
            return None
        
        now = datetime.now()
        next_times = []
        
        # Check each enabled interval
        for interval, enabled in self._chime_intervals.items():
            if not enabled:
                continue
            
            if interval == ChimeInterval.QUARTER_HOUR:
                # Next quarter hour (0, 15, 30, 45 minutes)
                minutes = now.minute
                next_quarter = ((minutes // 15) + 1) * 15
                if next_quarter >= 60:
                    next_time = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
                else:
                    next_time = now.replace(minute=next_quarter, second=0, microsecond=0)
                next_times.append(next_time)
            
            elif interval == ChimeInterval.HALF_HOUR:
                # Next half hour (0, 30 minutes)
                minutes = now.minute
                if minutes < 30:
                    next_time = now.replace(minute=30, second=0, microsecond=0)
                else:
                    next_time = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
                next_times.append(next_time)
            
            elif interval == ChimeInterval.HOUR:
                # Next hour (0 minutes)
                next_time = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
                next_times.append(next_time)
        
        return min(next_times) if next_times else None
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop that runs in a separate thread."""
        self.logger.info("ChimeScheduler loop started")
        
        try:
            while not self._stop_event.is_set():
                try:
                    # Calculate next chime time
                    next_chime_time = self.get_next_chime_time()
                    
                    if next_chime_time is None:
                        # No chimes enabled, wait a bit and check again
                        self._stop_event.wait(60)  # Check every minute
                        continue
                    
                    # Calculate time until next chime
                    now = datetime.now()
                    time_until_chime = (next_chime_time - now).total_seconds()
                    
                    if time_until_chime <= 0:
                        # Time has passed, determine which chime to play
                        self._check_and_play_chimes(now)
                        # Wait a bit to avoid rapid firing
                        self._stop_event.wait(1)
                    else:
                        # Wait until next chime time (or until stopped)
                        wait_time = min(time_until_chime, 60)  # Check at least every minute
                        self._stop_event.wait(wait_time)
                
                except Exception as e:
                    self.error_handler.handle_error(
                        e,
                        ErrorCategory.AUDIO,
                        "chime scheduler loop",
                        show_user_notification=False
                    )
                    # Wait a bit before continuing to avoid rapid error loops
                    self._stop_event.wait(5)
        
        finally:
            self.logger.info("ChimeScheduler loop ended")
    
    def _check_and_play_chimes(self, current_time: datetime) -> None:
        """
        Check current time and play appropriate chimes.
        
        Args:
            current_time: Current datetime to check against
        """
        minute = current_time.minute
        
        # Determine which chimes should play
        chimes_to_play = []
        
        if minute == 0:
            # Top of the hour - play hour chime
            if self._chime_intervals.get(ChimeInterval.HOUR, False):
                chimes_to_play.append(ChimeInterval.HOUR)
        
        if minute == 30:
            # Half hour - play half hour chime
            if self._chime_intervals.get(ChimeInterval.HALF_HOUR, False):
                chimes_to_play.append(ChimeInterval.HALF_HOUR)
        
        if minute in [15, 45]:
            # Quarter hours - play quarter hour chime
            if self._chime_intervals.get(ChimeInterval.QUARTER_HOUR, False):
                chimes_to_play.append(ChimeInterval.QUARTER_HOUR)
        
        # Play chimes
        for chime_interval in chimes_to_play:
            self._play_chime(chime_interval)
    
    def _play_chime(self, interval: ChimeInterval) -> bool:
        """
        Play a chime for the specified interval.
        
        Args:
            interval: The chime interval to play
            
        Returns:
            bool: True if chime was played successfully, False otherwise
        """
        try:
            # Map chime intervals to audio types
            audio_type_map = {
                ChimeInterval.QUARTER_HOUR: AudioType.QUARTER_CHIME,
                ChimeInterval.HALF_HOUR: AudioType.HALF_CHIME,
                ChimeInterval.HOUR: AudioType.HOUR_CHIME
            }
            
            audio_type = audio_type_map.get(interval)
            if audio_type is None:
                self.logger.error(f"Unknown chime interval: {interval}")
                return False
            
            # Play the chime (this will not interfere with ticking sounds due to separate channels)
            success = self.audio_manager.play_sound(audio_type)
            
            if success:
                self.logger.info(f"Played {interval.value} chime")
                
                # Call callback if set
                callback = self._chime_callbacks.get(interval)
                if callback:
                    try:
                        callback(interval, datetime.now())
                    except Exception as e:
                        self.logger.error(f"Error in chime callback for {interval.value}: {e}")
            else:
                self.logger.warning(f"Failed to play {interval.value} chime")
            
            return success
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                f"playing {interval.value} chime",
                show_user_notification=False
            )
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the chime scheduler.
        
        Returns:
            Dict[str, Any]: Status information
        """
        with self._lock:
            return {
                'enabled': self._enabled,
                'running': self._running,
                'chime_intervals': {
                    interval.value: enabled 
                    for interval, enabled in self._chime_intervals.items()
                },
                'next_chime_time': self.get_next_chime_time().isoformat() if self.get_next_chime_time() else None
            }
    
    def cleanup(self) -> None:
        """Clean up the chime scheduler."""
        try:
            self.logger.info("Cleaning up chime scheduler")
            
            # Stop the scheduler
            self.stop()
            
            # Clear callbacks
            with self._lock:
                self._chime_callbacks.clear()
            
            self.logger.info("Chime scheduler cleanup completed")
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.AUDIO,
                "chime scheduler cleanup",
                show_user_notification=False
            )
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during destruction