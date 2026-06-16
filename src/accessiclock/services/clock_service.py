"""Clock service for chime scheduling and time management."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import time
from typing import Literal

logger = logging.getLogger(__name__)

ChimeType = Literal["hour", "half_hour", "quarter_hour", "tick"]
ChimeStyle = Literal["classic", "grandfather"]


@dataclass(frozen=True)
class AlarmEvent:
    """A due alarm action with optional sound and spoken text."""

    sound_name: str | None
    spoken_text: str | None


class ClockService:
    """
    Service for managing clock chimes and time announcements.
    
    Handles:
    - Chime scheduling (hourly, half-hour, quarter-hour)
    - Quiet hours
    - Chime deduplication (don't repeat within same minute)
    """

    def __init__(self):
        """Initialize the clock service."""
        # Chime settings
        self.chime_hourly: bool = True
        self.chime_half_hour: bool = False
        self.chime_quarter_hour: bool = False
        self.chime_style: ChimeStyle = "classic"
        self.hour_count_chimes: bool = False
        self.minute_tick: bool = False

        # Quiet hours (None = disabled)
        self.quiet_start: time | None = None
        self.quiet_end: time | None = None

        # Alarm settings. Quiet hours intentionally do not suppress alarms.
        self.alarm_time: time | None = None
        self.alarm_spoken_text: str = "Time to get up"
        self.alarm_sound_enabled: bool = True

        # Track last chime to prevent repeats
        self._last_chime_minute: tuple[int, int] | None = None  # (hour, minute)
        self._last_alarm_minute: tuple[int, int] | None = None

    def should_chime_now(self, current_time: time) -> ChimeType | None:
        """
        Determine if a chime should play at the given time.
        
        Args:
            current_time: The current time to check.
            
        Returns:
            The type of chime to play, or None if no chime.
        """
        # Check quiet hours
        if self._is_quiet_time(current_time):
            return None

        # Check if we already chimed this minute
        current_minute = (current_time.hour, current_time.minute)
        if self._last_chime_minute == current_minute:
            return None

        return self._get_interval_chime_type(current_time)

    def get_chime_sequence(self, current_time: time) -> list[ChimeType]:
        """
        Build the scheduled sound sequence for the given time.

        This supports talking-clock behavior inspired by classic accessible
        clocks: optional minute ticks, quarter-position counts, and hour-count
        chimes. Manual commands such as "announce time now" bypass this schedule.
        """
        if self._is_quiet_time(current_time):
            return []

        current_minute = (current_time.hour, current_time.minute)
        if self._last_chime_minute == current_minute:
            return []

        sequence: list[ChimeType] = []
        if self.minute_tick:
            sequence.append("tick")

        chime_type = self._get_interval_chime_type(current_time)
        if chime_type:
            sequence.extend(self._expand_chime(chime_type, current_time))

        return sequence

    def _get_interval_chime_type(self, current_time: time) -> ChimeType | None:
        """Return the scheduled interval chime type, ignoring tick sounds."""
        minute = current_time.minute

        # Check intervals in priority order
        if minute == 0 and self.chime_hourly:
            return "hour"

        if minute == 30 and self.chime_half_hour:
            return "half_hour"

        if minute in (15, 45) and self.chime_quarter_hour:
            return "quarter_hour"

        # Also check 0 and 30 for quarter hour if half_hour not enabled
        if minute == 0 and self.chime_quarter_hour and not self.chime_hourly:
            return "quarter_hour"

        if minute == 30 and self.chime_quarter_hour and not self.chime_half_hour:
            return "quarter_hour"

        return None

    def _expand_chime(self, chime_type: ChimeType, current_time: time) -> list[ChimeType]:
        """Expand one logical chime into the configured audible sequence."""
        if chime_type == "hour" and self.hour_count_chimes:
            return ["hour"] * self.get_hour_12h(current_time)

        if chime_type == "quarter_hour" and self.chime_style == "grandfather":
            quarter_count = current_time.minute // 15
            if quarter_count == 0:
                quarter_count = 4
            return ["quarter_hour"] * quarter_count

        return [chime_type]

    def mark_chimed(self, current_time: time) -> None:
        """
        Mark that a chime was played at the given time.
        
        This prevents the same chime from playing multiple times
        within the same minute.
        
        Args:
            current_time: The time when the chime was played.
        """
        self._last_chime_minute = (current_time.hour, current_time.minute)

    def get_hour_12h(self, current_time: time) -> int:
        """
        Get the hour in 12-hour format.
        
        Args:
            current_time: The time to extract the hour from.
            
        Returns:
            Hour as 1-12 (never 0).
        """
        hour = current_time.hour % 12
        return 12 if hour == 0 else hour

    def _is_quiet_time(self, current_time: time) -> bool:
        """
        Check if the given time falls within quiet hours.
        
        Args:
            current_time: The time to check.
            
        Returns:
            True if within quiet hours, False otherwise.
        """
        if self.quiet_start is None or self.quiet_end is None:
            return False
        
        # Handle overnight quiet hours (e.g., 23:00 to 07:00)
        if self.quiet_start > self.quiet_end:
            # Quiet hours span midnight
            return current_time >= self.quiet_start or current_time < self.quiet_end
        else:
            # Quiet hours within same day
            return self.quiet_start <= current_time < self.quiet_end

    @property
    def quiet_hours_enabled(self) -> bool:
        """Return whether quiet hours are currently enabled."""
        return self.quiet_start is not None and self.quiet_end is not None

    @quiet_hours_enabled.setter
    def quiet_hours_enabled(self, value: bool) -> None:
        """Enable or disable quiet hours. Disabling clears start/end times."""
        if not value:
            self.quiet_start = None
            self.quiet_end = None

    def set_quiet_hours(self, start: time, end: time) -> None:
        """
        Set quiet hours range.

        Args:
            start: Start time for quiet hours.
            end: End time for quiet hours.
        """
        self.quiet_start = start
        self.quiet_end = end

    def reset_chime_tracking(self) -> None:
        """Reset the chime tracking (e.g., after settings change)."""
        self._last_chime_minute = None

    @property
    def alarm_enabled(self) -> bool:
        """Return whether an alarm time is configured."""
        return self.alarm_time is not None

    @alarm_enabled.setter
    def alarm_enabled(self, value: bool) -> None:
        """Disable the alarm when set to False."""
        if not value:
            self.alarm_time = None

    def set_alarm(
        self,
        alarm_time: time,
        *,
        spoken_text: str = "Time to get up",
        sound_enabled: bool = True,
    ) -> None:
        """Configure the daily alarm."""
        self.alarm_time = alarm_time
        self.alarm_spoken_text = spoken_text.strip() or "Time to get up"
        self.alarm_sound_enabled = sound_enabled

    def get_due_alarm(self, current_time: time) -> AlarmEvent | None:
        """Return the due alarm event for the current minute, if any."""
        if not self.alarm_time:
            return None

        current_minute = (current_time.hour, current_time.minute)
        if self._last_alarm_minute == current_minute:
            return None

        if (
            current_time.hour != self.alarm_time.hour
            or current_time.minute != self.alarm_time.minute
        ):
            return None

        return AlarmEvent(
            sound_name="alarm" if self.alarm_sound_enabled else None,
            spoken_text=self.alarm_spoken_text,
        )

    def mark_alarmed(self, current_time: time) -> None:
        """Mark the alarm handled for the current minute."""
        self._last_alarm_minute = (current_time.hour, current_time.minute)
