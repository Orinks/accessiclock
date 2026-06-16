"""AccessiClock wxPython application."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import time as dt_time
from typing import TYPE_CHECKING, cast

import wx

from .audio.tts_engine import TimeStyle, TTSEngine
from .core.settings import AppSettings, load_settings, save_settings
from .paths import Paths
from .services.clock_pack_loader import ClockPackLoader
from .services.clock_service import ChimeStyle, ClockService

if TYPE_CHECKING:
    from .audio.player import AudioPlayer
    from .ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class AccessiClockApp(wx.App):
    """AccessiClock application using wxPython."""

    def __init__(self, portable_mode: bool = False):
        self._portable_mode = portable_mode
        self.paths = Paths(portable_mode=portable_mode)

        self.main_window: MainWindow | None = None
        self.audio_player: AudioPlayer | None = None
        self.tts_engine: TTSEngine | None = None
        self.clock_service: ClockService | None = None
        self.clock_pack_loader: ClockPackLoader | None = None

        self.settings = AppSettings()
        self.config = self.settings.to_dict()
        self.current_volume = self.settings.volume
        self.selected_clock = self.settings.clock
        self.chime_hourly = self.settings.chime_hourly
        self.chime_half_hour = self.settings.chime_half_hour
        self.chime_quarter_hour = self.settings.chime_quarter_hour
        self.chime_style: ChimeStyle = cast(ChimeStyle, self.settings.chime_style)
        self.hour_count_chimes = self.settings.hour_count_chimes
        self.minute_tick = self.settings.minute_tick
        self.alarm_enabled = self.settings.alarm_enabled
        self.alarm_time = self.settings.alarm_time
        self.alarm_sound_enabled = self.settings.alarm_sound_enabled
        self.alarm_spoken_text = self.settings.alarm_spoken_text
        self.quiet_hours_enabled = self.settings.quiet_hours_enabled
        self.quiet_start = self.settings.quiet_start
        self.quiet_end = self.settings.quiet_end

        super().__init__()

    def OnInit(self) -> bool:
        """Initialize the app and create the main window."""
        logger.info("Starting AccessiClock wxPython app")
        try:
            self._startup()
            return True
        except Exception:
            logger.exception("Startup failed")
            wx.MessageBox("AccessiClock could not start. See log file for details.", "Startup Error")
            return False

    def _startup(self) -> None:
        self._init_services()
        self._init_audio()
        self._init_tts()
        self._load_config()
        self._sync_service_settings()

        from .ui.main_window import MainWindow

        self.main_window = MainWindow(self)
        self.main_window.Show()
        self.SetTopWindow(self.main_window)

    def _init_services(self) -> None:
        self.clock_service = ClockService()
        self.clock_pack_loader = ClockPackLoader(self.paths.clocks_dir)
        self.clock_pack_loader.discover_packs()

    def _init_audio(self) -> None:
        try:
            from .audio.player import AudioPlayer

            self.audio_player = AudioPlayer(volume_percent=self.current_volume)
        except Exception:
            logger.warning("Audio player unavailable", exc_info=True)
            self.audio_player = None

    def _init_tts(self) -> None:
        try:
            self.tts_engine = TTSEngine()
        except Exception:
            logger.warning("TTS unavailable", exc_info=True)
            self.tts_engine = None

    def _sync_service_settings(self) -> None:
        if not self.clock_service:
            return
        self.clock_service.chime_hourly = self.chime_hourly
        self.clock_service.chime_half_hour = self.chime_half_hour
        self.clock_service.chime_quarter_hour = self.chime_quarter_hour
        self.clock_service.chime_style = cast(ChimeStyle, self.chime_style)
        self.clock_service.hour_count_chimes = self.hour_count_chimes
        self.clock_service.minute_tick = self.minute_tick
        if self.alarm_enabled:
            try:
                alarm_hour, alarm_minute = map(int, self.alarm_time.split(":"))
                self.clock_service.set_alarm(
                    dt_time(alarm_hour, alarm_minute),
                    spoken_text=self.alarm_spoken_text,
                    sound_enabled=self.alarm_sound_enabled,
                )
            except (TypeError, ValueError):
                logger.warning("Invalid alarm time in config; disabling alarm")
                self.clock_service.alarm_enabled = False
        else:
            self.clock_service.alarm_enabled = False

    def _load_config(self) -> None:
        self.settings = load_settings(self.paths.config_file)
        self.config = self.settings.to_dict()

        self.current_volume = self.settings.volume
        self.selected_clock = self.settings.clock
        self.chime_hourly = self.settings.chime_hourly
        self.chime_half_hour = self.settings.chime_half_hour
        self.chime_quarter_hour = self.settings.chime_quarter_hour
        self.chime_style = cast(ChimeStyle, self.settings.chime_style)
        self.hour_count_chimes = self.settings.hour_count_chimes
        self.minute_tick = self.settings.minute_tick
        self.alarm_enabled = self.settings.alarm_enabled
        self.alarm_time = self.settings.alarm_time
        self.alarm_sound_enabled = self.settings.alarm_sound_enabled
        self.alarm_spoken_text = self.settings.alarm_spoken_text
        self.quiet_hours_enabled = self.settings.quiet_hours_enabled
        self.quiet_start = self.settings.quiet_start
        self.quiet_end = self.settings.quiet_end

        if self.clock_service and self.settings.quiet_hours_enabled:
            try:
                sh, sm = map(int, self.settings.quiet_start.split(":"))
                eh, em = map(int, self.settings.quiet_end.split(":"))
                self.clock_service.set_quiet_hours(dt_time(sh, sm), dt_time(eh, em))
            except (TypeError, ValueError):
                logger.warning("Invalid quiet hours in config; disabling")
                self.clock_service.quiet_hours_enabled = False
                self.quiet_hours_enabled = False

    def save_config(self) -> None:
        if (
            self.clock_service
            and self.clock_service.quiet_hours_enabled
            and self.clock_service.quiet_start
            and self.clock_service.quiet_end
        ):
            quiet_enabled = True
            quiet_start = self.clock_service.quiet_start.strftime("%H:%M")
            quiet_end = self.clock_service.quiet_end.strftime("%H:%M")
        else:
            quiet_enabled = False
            quiet_start = self.quiet_start
            quiet_end = self.quiet_end
        self.quiet_hours_enabled = quiet_enabled
        self.quiet_start = quiet_start
        self.quiet_end = quiet_end

        self.config.update(
            {
                "volume": self.current_volume,
                "clock": self.selected_clock,
                "chime_hourly": self.chime_hourly,
                "chime_half_hour": self.chime_half_hour,
                "chime_quarter_hour": self.chime_quarter_hour,
                "chime_style": self.chime_style,
                "hour_count_chimes": self.hour_count_chimes,
                "minute_tick": self.minute_tick,
                "quiet_hours_enabled": quiet_enabled,
                "quiet_start": quiet_start,
                "quiet_end": quiet_end,
                "alarm_enabled": self.alarm_enabled,
                "alarm_time": self.alarm_time,
                "alarm_sound_enabled": self.alarm_sound_enabled,
                "alarm_spoken_text": self.alarm_spoken_text,
            }
        )
        self.settings = AppSettings(
            **self.config,
        )
        self._sync_service_settings()
        save_settings(self.paths.config_file, self.settings)

    def set_volume(self, volume: int) -> None:
        self.current_volume = max(0, min(100, volume))
        if self.audio_player:
            self.audio_player.set_volume(self.current_volume)
        self.save_config()

    def play_chime(self, chime_type: str) -> bool:
        if not self.audio_player or not self.clock_pack_loader:
            return False
        try:
            pack_info = self.clock_pack_loader.get_pack(self.selected_clock)
            if not pack_info:
                return False
            sound_path = pack_info.get_sound_path(chime_type)
            if not sound_path or not sound_path.exists():
                return False
            self.audio_player.play_sound(str(sound_path))
            return True
        except Exception:
            logger.warning("Unable to play %s chime", chime_type, exc_info=True)
            return False

    def play_chime_sequence(self, chime_types: Sequence[str]) -> bool:
        """Play an ordered chime sequence from the selected clock pack."""
        if not self.audio_player or not self.clock_pack_loader or not chime_types:
            return False
        try:
            pack_info = self.clock_pack_loader.get_pack(self.selected_clock)
            if not pack_info:
                return False
            sound_paths = []
            for chime_type in chime_types:
                sound_path = pack_info.get_sound_path(chime_type)
                if not sound_path or not sound_path.exists():
                    logger.info("Skipping missing %s sound in %s", chime_type, pack_info.name)
                    continue
                sound_paths.append(str(sound_path))
            if not sound_paths:
                return False
            if len(sound_paths) == 1:
                self.audio_player.play_sound(sound_paths[0])
                return True
            if hasattr(self.audio_player, "play_sound_sequence"):
                return bool(self.audio_player.play_sound_sequence(sound_paths))
            for sound_path_text in sound_paths:
                self.audio_player.play_sound(sound_path_text)
            return True
        except Exception:
            logger.warning("Unable to play chime sequence: %s", chime_types, exc_info=True)
            return False

    def play_test_sound(self) -> bool:
        return self.play_chime("preview") or self.play_chime("hour")

    def announce_time(self, style: str = "simple") -> bool:
        if not self.tts_engine:
            return False
        from datetime import datetime

        self.tts_engine.speak_time(datetime.now().time(), style=cast(TimeStyle, style))
        return True

    def check_and_play_chime(self, current_time: dt_time | None = None) -> str | None:
        if not self.clock_service:
            return None

        if current_time is None:
            from datetime import datetime

            current_time = datetime.now().time()
        chime_sequence = self.clock_service.get_chime_sequence(current_time)
        if chime_sequence and self.play_chime_sequence(chime_sequence):
            self.clock_service.mark_chimed(current_time)
            return ", ".join(chime_sequence)
        return None

    def check_and_trigger_alarm(self, current_time: dt_time | None = None) -> bool:
        """Trigger the configured alarm when it is due."""
        if not self.clock_service:
            return False

        if current_time is None:
            from datetime import datetime

            current_time = datetime.now().time()
        alarm = self.clock_service.get_due_alarm(current_time)
        if not alarm:
            return False
        did_anything = False
        if alarm.sound_name:
            did_anything = self.play_chime(alarm.sound_name) or did_anything
        if alarm.spoken_text and self.tts_engine:
            self.tts_engine.speak(alarm.spoken_text)
            did_anything = True
        self.clock_service.mark_alarmed(current_time)
        return did_anything

    def get_available_clocks(self) -> list[str]:
        if not self.clock_pack_loader or not self.clock_pack_loader._cache:
            return ["Default"]
        return [info.name for info in self.clock_pack_loader._cache.values()]

    def OnExit(self) -> int:
        logger.info("Shutting down AccessiClock")
        self.save_config()

        if self.audio_player:
            try:
                self.audio_player.cleanup()
            except Exception:
                logger.warning("Audio cleanup failed", exc_info=True)
        if self.tts_engine:
            try:
                self.tts_engine.cleanup()
            except Exception:
                logger.warning("TTS cleanup failed", exc_info=True)
        return 0
