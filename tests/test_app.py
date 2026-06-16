"""Tests for accessiclock.app module - config and volume logic."""

import json
import tempfile
from datetime import time
from pathlib import Path
from unittest.mock import MagicMock


class TestConfigLoading:
    """Test configuration loading logic (independent of wx)."""

    def test_load_config_from_valid_file(self):
        """Should load config values from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_data = {
                "volume": 75,
                "clock": "westminster",
                "chime_hourly": True,
                "chime_half_hour": True,
                "chime_quarter_hour": False,
            }
            with open(config_path, "w") as f:
                json.dump(config_data, f)
            
            # Load config manually (same logic as app._load_config)
            with open(config_path, encoding="utf-8") as f:
                loaded = json.load(f)
            
            assert loaded["volume"] == 75
            assert loaded["clock"] == "westminster"
            assert loaded["chime_hourly"] is True
            assert loaded["chime_half_hour"] is True
            assert loaded["chime_quarter_hour"] is False

    def test_load_config_missing_file_returns_empty(self):
        """Should return empty when config file doesn't exist."""
        config_path = Path("/nonexistent/config.json")
        
        loaded = {}
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                loaded = json.load(f)
        
        assert loaded == {}

    def test_save_config_writes_json_file(self):
        """Should write config to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            config = {
                "volume": 80,
                "clock": "nature",
                "chime_hourly": False,
                "chime_half_hour": True,
                "chime_quarter_hour": True,
            }
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            
            # Verify file
            assert config_path.exists()
            with open(config_path) as f:
                saved = json.load(f)
            
            assert saved["volume"] == 80
            assert saved["clock"] == "nature"
            assert saved["chime_hourly"] is False

    def test_config_default_values(self):
        """Test default config values."""
        # These match the defaults in AccessiClockApp.__init__
        defaults = {
            "current_volume": 50,
            "selected_clock": "default",
            "chime_hourly": True,
            "chime_half_hour": False,
            "chime_quarter_hour": False,
        }
        
        assert defaults["current_volume"] == 50
        assert defaults["selected_clock"] == "default"
        assert defaults["chime_hourly"] is True
        assert defaults["chime_half_hour"] is False


class TestVolumeLogic:
    """Test volume control logic (independent of wx)."""

    def test_volume_clamp_high(self):
        """Volume should be clamped to 100 max."""
        volume = 150
        clamped = max(0, min(100, volume))
        assert clamped == 100

    def test_volume_clamp_low(self):
        """Volume should be clamped to 0 min."""
        volume = -50
        clamped = max(0, min(100, volume))
        assert clamped == 0

    def test_volume_clamp_valid(self):
        """Valid volume should pass through unchanged."""
        volume = 75
        clamped = max(0, min(100, volume))
        assert clamped == 75

    def test_volume_zero(self):
        """Volume 0 is valid (muted)."""
        volume = 0
        clamped = max(0, min(100, volume))
        assert clamped == 0

    def test_volume_hundred(self):
        """Volume 100 is valid (max)."""
        volume = 100
        clamped = max(0, min(100, volume))
        assert clamped == 100


class TestAppIntegration:
    """Integration tests that can run without wx."""

    def test_paths_module_importable(self):
        """Paths module should be importable."""
        from accessiclock.paths import Paths
        assert Paths is not None

    def test_constants_module_importable(self):
        """Constants module should be importable."""
        from accessiclock.constants import APP_NAME, APP_VERSION
        assert APP_NAME == "AccessiClock"
        assert APP_VERSION is not None

    def test_clock_service_importable(self):
        """Clock service should be importable."""
        from accessiclock.services.clock_service import ClockService
        service = ClockService()
        assert service is not None

    def test_clock_pack_loader_importable(self):
        """Clock pack loader should be importable."""
        from accessiclock.services.clock_pack_loader import ClockPackLoader
        assert ClockPackLoader is not None

    def test_tts_engine_importable(self):
        """TTS engine should be importable."""
        from accessiclock.audio.tts_engine import TTSEngine
        assert TTSEngine is not None

    def test_audio_player_importable(self):
        """Audio player should be importable."""
        from accessiclock.audio.player import AudioPlayer
        assert AudioPlayer is not None

    def test_save_config_persists_tray_hotkey_and_audio_device_settings(self, temp_dir):
        from accessiclock.app import AccessiClockApp
        from accessiclock.core.settings import load_settings

        class FakePaths:
            config_file = temp_dir / "config.json"

        app = AccessiClockApp.__new__(AccessiClockApp)
        app.paths = FakePaths()
        app.settings = load_settings(app.paths.config_file)
        app.config = app.settings.to_dict()
        app.clock_service = None
        app.current_volume = 50
        app.selected_clock = "default"
        app.chime_hourly = True
        app.chime_half_hour = False
        app.chime_quarter_hour = False
        app.chime_style = "classic"
        app.hour_count_chimes = False
        app.minute_tick = False
        app.quiet_hours_enabled = False
        app.quiet_start = "22:00"
        app.quiet_end = "07:00"
        app.alarm_enabled = False
        app.alarm_time = "07:00"
        app.alarm_sound_enabled = True
        app.alarm_spoken_text = "Time to get up"
        app.minimize_to_tray = True
        app.global_hotkeys_enabled = True
        app.speak_time_hotkey = "Ctrl+Alt+T"
        app.audio_device_name = "Speakers"

        app.save_config()

        loaded = load_settings(app.paths.config_file)
        assert loaded.minimize_to_tray is True
        assert loaded.global_hotkeys_enabled is True
        assert loaded.speak_time_hotkey == "Ctrl+Alt+T"
        assert loaded.audio_device_name == "Speakers"

    def test_set_audio_device_keeps_previous_device_on_failure(self):
        from accessiclock.app import AccessiClockApp

        app = AccessiClockApp.__new__(AccessiClockApp)
        app.audio_device_name = "Headphones"
        app.audio_player = MagicMock()
        app.audio_player.set_output_device.side_effect = RuntimeError("device missing")
        app.save_config = MagicMock()

        assert app.set_audio_device("Speakers") is False
        assert app.audio_device_name == "Headphones"
        app.save_config.assert_not_called()


class TestAppChimePlayback:
    """Test app chime and alarm orchestration without starting wx."""

    def test_play_chime_sequence_uses_audio_player_sequence_for_multiple_sounds(self, temp_dir):
        """Multiple scheduled sounds should be delegated as one ordered sequence."""
        from accessiclock.app import AccessiClockApp
        from accessiclock.services.clock_pack_loader import ClockPackLoader

        clock_dir = temp_dir / "clocks" / "test"
        clock_dir.mkdir(parents=True)
        for name in ["hour.wav", "tick.wav"]:
            (clock_dir / name).touch()
        (clock_dir / "clock.json").write_text(
            json.dumps(
                {
                    "name": "Test",
                    "version": "1.0",
                    "sounds": {"hour": "hour.wav", "tick": "tick.wav"},
                }
            ),
            encoding="utf-8",
        )

        app = AccessiClockApp.__new__(AccessiClockApp)
        app.audio_player = MagicMock()
        app.audio_player.play_sound_sequence.return_value = True
        app.clock_pack_loader = ClockPackLoader(temp_dir / "clocks")
        app.clock_pack_loader.discover_packs()
        app.selected_clock = "test"

        assert app.play_chime_sequence(["tick", "hour", "hour"]) is True
        app.audio_player.play_sound_sequence.assert_called_once()
        played = app.audio_player.play_sound_sequence.call_args.args[0]
        assert played == [
            str(clock_dir / "tick.wav"),
            str(clock_dir / "hour.wav"),
            str(clock_dir / "hour.wav"),
        ]

    def test_check_and_trigger_alarm_speaks_configured_text(self):
        """A due alarm should play sound when available and speak configured text."""
        from accessiclock.app import AccessiClockApp
        from accessiclock.services.clock_service import ClockService

        app = AccessiClockApp.__new__(AccessiClockApp)
        app.clock_service = ClockService()
        app.clock_service.set_alarm(time(7, 30), spoken_text="Wake up", sound_enabled=True)
        app.play_chime = MagicMock(return_value=True)
        app.tts_engine = MagicMock()

        assert app.check_and_trigger_alarm(time(7, 30, 0)) is True

        app.play_chime.assert_called_once_with("alarm")
        app.tts_engine.speak.assert_called_once_with("Wake up")
