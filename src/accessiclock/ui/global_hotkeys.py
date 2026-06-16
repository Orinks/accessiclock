"""Global hotkey registration for AccessiClock."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import wx

HotkeyCallback = Callable[[], None]


@dataclass(frozen=True)
class ParsedHotkey:
    modifiers: int
    keycode: int


def parse_hotkey(hotkey_text: str, *, wx_module: Any = wx) -> ParsedHotkey | None:
    """Parse a compact hotkey string such as Ctrl+Alt+T."""
    parts = [part.strip() for part in hotkey_text.split("+") if part.strip()]
    if not parts:
        return None

    modifiers = 0
    key_text = parts[-1].upper()
    for part in parts[:-1]:
        token = part.lower()
        if token == "ctrl":
            modifiers |= int(wx_module.MOD_CONTROL)
        elif token == "alt":
            modifiers |= int(wx_module.MOD_ALT)
        elif token == "shift":
            modifiers |= int(wx_module.MOD_SHIFT)
        else:
            return None

    if len(key_text) == 1:
        keycode = ord(key_text)
    elif key_text.startswith("F") and key_text[1:].isdigit():
        keycode = int(getattr(wx_module, f"WXK_{key_text}", 0))
        if not keycode:
            return None
    else:
        return None
    return ParsedHotkey(modifiers=modifiers, keycode=keycode)


class GlobalHotkeyManager:
    """Small wrapper around wx.RegisterHotKey with a testable parser."""

    def __init__(self, frame: wx.Frame, *, wx_module: Any = wx):
        self._frame = frame
        self._wx = wx_module
        self._hotkey_id = self._make_hotkey_id()
        self._callback: HotkeyCallback | None = None
        self._registered = False

    def _make_hotkey_id(self) -> int:
        if hasattr(self._wx, "NewIdRef"):
            return int(self._wx.NewIdRef())
        return 9001

    def register(self, hotkey_text: str, callback: HotkeyCallback) -> bool:
        """Register a single announce-time global hotkey."""
        parsed = parse_hotkey(hotkey_text, wx_module=self._wx)
        if parsed is None:
            return False
        self.unregister()
        if not self._frame.RegisterHotKey(self._hotkey_id, parsed.modifiers, parsed.keycode):
            return False
        self._callback = callback
        self._registered = True
        self._frame.Bind(self._wx.EVT_HOTKEY, self._on_hotkey)
        return True

    def unregister(self) -> None:
        """Unregister the active hotkey if there is one."""
        if not self._registered:
            return
        try:
            self._frame.UnregisterHotKey(self._hotkey_id)
        finally:
            self._registered = False
            self._callback = None

    def _on_hotkey(self, event: wx.KeyEvent) -> None:
        if event.GetId() != self._hotkey_id:
            event.Skip()
            return
        if self._callback:
            self._callback()
