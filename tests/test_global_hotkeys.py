from unittest.mock import MagicMock


class FakeWx:
    MOD_CONTROL = 0x0002
    MOD_ALT = 0x0001
    WXK_F8 = 344
    EVT_HOTKEY = object()


def test_parse_hotkey_supports_ctrl_alt_letter():
    from accessiclock.ui.global_hotkeys import parse_hotkey

    parsed = parse_hotkey("Ctrl+Alt+T", wx_module=FakeWx)

    assert parsed is not None
    assert parsed.modifiers == FakeWx.MOD_CONTROL | FakeWx.MOD_ALT
    assert parsed.keycode == ord("T")


def test_parse_hotkey_supports_function_key():
    from accessiclock.ui.global_hotkeys import parse_hotkey

    parsed = parse_hotkey("Ctrl+Alt+F8", wx_module=FakeWx)

    assert parsed is not None
    assert parsed.keycode == FakeWx.WXK_F8


def test_parse_hotkey_rejects_blank_text():
    from accessiclock.ui.global_hotkeys import parse_hotkey

    assert parse_hotkey("", wx_module=FakeWx) is None


def test_global_hotkey_manager_registers_and_dispatches():
    from accessiclock.ui.global_hotkeys import GlobalHotkeyManager

    frame = MagicMock()
    frame.RegisterHotKey.return_value = True
    callback = MagicMock()
    manager = GlobalHotkeyManager(frame, wx_module=FakeWx)

    assert manager.register("Ctrl+Alt+T", callback) is True
    frame.RegisterHotKey.assert_called_once()
    frame.Bind.assert_called_once_with(FakeWx.EVT_HOTKEY, manager._on_hotkey)

    event = MagicMock()
    event.GetId.return_value = manager._hotkey_id
    manager._on_hotkey(event)

    callback.assert_called_once()


def test_global_hotkey_manager_cleans_up_registered_hotkey():
    from accessiclock.ui.global_hotkeys import GlobalHotkeyManager

    frame = MagicMock()
    frame.RegisterHotKey.return_value = True
    manager = GlobalHotkeyManager(frame, wx_module=FakeWx)
    manager.register("Ctrl+Alt+T", MagicMock())

    manager.unregister()

    frame.UnregisterHotKey.assert_called_once_with(manager._hotkey_id)

