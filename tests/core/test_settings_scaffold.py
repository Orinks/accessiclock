from pathlib import Path

from accessiclock.core.settings import AppSettings, load_settings, save_settings


def test_load_settings_defaults_for_missing_file(tmp_path: Path):
    settings = load_settings(tmp_path / "missing.json")
    assert settings == AppSettings()


def test_load_settings_clamps_volume(tmp_path: Path):
    config_file = tmp_path / "config.json"
    config_file.write_text('{"volume": 999, "clock": "digital"}', encoding="utf-8")

    settings = load_settings(config_file)
    assert settings.volume == 100
    assert settings.clock == "digital"


def test_load_settings_reads_clock_chime_options(tmp_path: Path):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        (
            '{"chime_style": "grandfather", "hour_count_chimes": true, '
            '"minute_tick": true, "alarm_enabled": true, "alarm_time": "07:30", '
            '"alarm_sound_enabled": false, "alarm_spoken_text": "Wake up"}'
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_file)

    assert settings.chime_style == "grandfather"
    assert settings.hour_count_chimes is True
    assert settings.minute_tick is True
    assert settings.alarm_enabled is True
    assert settings.alarm_time == "07:30"
    assert settings.alarm_sound_enabled is False
    assert settings.alarm_spoken_text == "Wake up"


def test_load_settings_reads_tray_hotkey_and_audio_device_options(tmp_path: Path):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        (
            '{"minimize_to_tray": true, "global_hotkeys_enabled": true, '
            '"speak_time_hotkey": "Ctrl+Alt+T", "audio_device_name": "Speakers"}'
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_file)

    assert settings.minimize_to_tray is True
    assert settings.global_hotkeys_enabled is True
    assert settings.speak_time_hotkey == "Ctrl+Alt+T"
    assert settings.audio_device_name == "Speakers"


def test_load_settings_rejects_blank_hotkey_and_normalizes_audio_device(tmp_path: Path):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"speak_time_hotkey": " ", "audio_device_name": ""}',
        encoding="utf-8",
    )

    settings = load_settings(config_file)

    assert settings.speak_time_hotkey == "Ctrl+Alt+T"
    assert settings.audio_device_name == ""


def test_load_settings_rejects_unknown_chime_style(tmp_path: Path):
    config_file = tmp_path / "config.json"
    config_file.write_text('{"chime_style": "mystery"}', encoding="utf-8")

    settings = load_settings(config_file)

    assert settings.chime_style == "classic"


def test_save_and_load_round_trip(tmp_path: Path):
    config_file = tmp_path / "nested" / "config.json"
    expected = AppSettings(
        volume=25,
        clock="westminster",
        chime_half_hour=True,
        chime_style="grandfather",
        hour_count_chimes=True,
        minute_tick=True,
        alarm_enabled=True,
        alarm_time="06:45",
        alarm_spoken_text="Coffee is ready",
        minimize_to_tray=True,
        global_hotkeys_enabled=True,
        speak_time_hotkey="Ctrl+Alt+T",
        audio_device_name="Headphones",
    )

    save_settings(config_file, expected)
    loaded = load_settings(config_file)

    assert loaded == expected
