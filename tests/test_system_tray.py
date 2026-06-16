from unittest.mock import MagicMock


def test_tray_menu_labels_are_textual_and_accessible():
    from accessiclock.ui.system_tray import TRAY_MENU_LABELS

    assert TRAY_MENU_LABELS == [
        "Show AccessiClock",
        "Announce Time",
        "Test Chime",
        "Settings...",
        "Exit AccessiClock",
    ]
    assert all(label.strip() and "&" not in label for label in TRAY_MENU_LABELS)


def test_tray_action_methods_delegate_to_app_and_window():
    from accessiclock.ui.system_tray import TrayActionHandler

    app = MagicMock()
    window = MagicMock()
    app.main_window = window
    handler = TrayActionHandler(app)

    handler.show_main_window()
    window.Show.assert_called_once_with(True)
    window.Raise.assert_called_once()

    handler.announce_time()
    app.announce_time.assert_called_once()

    handler.test_chime()
    app.play_test_sound.assert_called_once()

    handler.open_settings()
    window.open_settings_dialog.assert_called_once()

    handler.exit_application()
    app.request_exit.assert_called_once()

