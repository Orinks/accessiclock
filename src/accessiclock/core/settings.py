"""Settings I/O and simple validation for AccessiClock."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

VALID_CHIME_STYLES = {"classic", "grandfather"}
VALID_ANNOUNCEMENT_STYLES = {"simple", "natural", "precise"}


@dataclass
class AppSettings:
    """Persistent user settings used by the app."""

    volume: int = 50
    clock: str = "default"
    chime_hourly: bool = True
    chime_half_hour: bool = False
    chime_quarter_hour: bool = False
    chime_style: str = "classic"
    hour_count_chimes: bool = False
    minute_tick: bool = False
    quiet_hours_enabled: bool = False
    quiet_start: str = "22:00"
    quiet_end: str = "07:00"
    alarm_enabled: bool = False
    alarm_time: str = "07:00"
    alarm_sound_enabled: bool = True
    alarm_spoken_text: str = "Time to get up"
    time_format: str = "12h"
    start_minimized: bool = False
    start_with_windows: bool = False
    play_startup_sound: bool = True
    announce_on_focus: bool = False
    speech_rate: int = 150
    announcement_style: str = "simple"
    minimize_to_tray: bool = False
    global_hotkeys_enabled: bool = False
    speak_time_hotkey: str = "Ctrl+Alt+T"
    audio_device_name: str = ""
    debug_logging: bool = False

    @classmethod
    def from_dict(cls, raw: dict) -> AppSettings:
        """Build settings from plain dict with safe defaults."""
        settings = cls(
            volume=_clamp_volume(raw.get("volume", 50)),
            clock=str(raw.get("clock", "default") or "default"),
            chime_hourly=bool(raw.get("chime_hourly", True)),
            chime_half_hour=bool(raw.get("chime_half_hour", False)),
            chime_quarter_hour=bool(raw.get("chime_quarter_hour", False)),
            chime_style=_valid_choice(raw.get("chime_style"), VALID_CHIME_STYLES, "classic"),
            hour_count_chimes=bool(raw.get("hour_count_chimes", False)),
            minute_tick=bool(raw.get("minute_tick", False)),
            quiet_hours_enabled=bool(raw.get("quiet_hours_enabled", False)),
            quiet_start=_time_string(raw.get("quiet_start", "22:00"), "22:00"),
            quiet_end=_time_string(raw.get("quiet_end", "07:00"), "07:00"),
            alarm_enabled=bool(raw.get("alarm_enabled", False)),
            alarm_time=_time_string(raw.get("alarm_time", "07:00"), "07:00"),
            alarm_sound_enabled=bool(raw.get("alarm_sound_enabled", True)),
            alarm_spoken_text=str(raw.get("alarm_spoken_text", "Time to get up") or "Time to get up"),
            time_format=_valid_choice(raw.get("time_format"), {"12h", "24h"}, "12h"),
            start_minimized=bool(raw.get("start_minimized", False)),
            start_with_windows=bool(raw.get("start_with_windows", False)),
            play_startup_sound=bool(raw.get("play_startup_sound", True)),
            announce_on_focus=bool(raw.get("announce_on_focus", False)),
            speech_rate=_clamp_int(raw.get("speech_rate", 150), 50, 300, 150),
            announcement_style=_valid_choice(
                raw.get("announcement_style"), VALID_ANNOUNCEMENT_STYLES, "simple"
            ),
            minimize_to_tray=bool(raw.get("minimize_to_tray", False)),
            global_hotkeys_enabled=bool(raw.get("global_hotkeys_enabled", False)),
            speak_time_hotkey=_non_blank_string(raw.get("speak_time_hotkey"), "Ctrl+Alt+T"),
            audio_device_name=_optional_string(raw.get("audio_device_name", "")),
            debug_logging=bool(raw.get("debug_logging", False)),
        )
        return settings

    def to_dict(self) -> dict:
        """Serialize settings to plain dict."""
        return asdict(self)


def _clamp_volume(value: object) -> int:
    return _clamp_int(value, 0, 100, 50)


def _clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        return max(minimum, min(maximum, int(value)))
    except (TypeError, ValueError):
        return default


def _valid_choice(value: object, choices: set[str], default: str) -> str:
    choice = str(value or default)
    if choice in choices:
        return choice
    return default


def _non_blank_string(value: object, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def _optional_string(value: object) -> str:
    return str(value or "").strip()


def _time_string(value: object, default: str) -> str:
    text = str(value or default)
    parts = text.split(":")
    if len(parts) != 2:
        return default
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return default
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return f"{hour:02d}:{minute:02d}"
    return default


def load_settings(config_file: Path) -> AppSettings:
    """Load settings from config file. Returns defaults on errors."""
    if not config_file.exists():
        return AppSettings()

    try:
        with open(config_file, encoding="utf-8") as handle:
            return AppSettings.from_dict(json.load(handle))
    except (OSError, json.JSONDecodeError, TypeError):
        return AppSettings()


def save_settings(config_file: Path, settings: AppSettings) -> None:
    """Save settings to disk, creating parent directories as needed."""
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as handle:
        json.dump(settings.to_dict(), handle, indent=2)
