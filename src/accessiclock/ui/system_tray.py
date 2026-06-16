"""System tray integration for AccessiClock."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import wx
import wx.adv

if TYPE_CHECKING:
    from ..app import AccessiClockApp

logger = logging.getLogger(__name__)

TRAY_MENU_LABELS = [
    "Show AccessiClock",
    "Announce Time",
    "Test Chime",
    "Settings...",
    "Exit AccessiClock",
]


class TrayActionHandler:
    """Actions exposed by the system tray menu."""

    def __init__(self, app: AccessiClockApp):
        self.app = app

    def show_main_window(self) -> None:
        window = self.app.main_window
        if not window:
            return
        window.Show(True)
        if window.IsIconized():
            window.Iconize(False)
        window.Raise()
        window.SetFocus()

    def announce_time(self) -> None:
        self.app.announce_time(style=self.app.config.get("announcement_style", "simple"))
        if self.app.main_window:
            self.app.main_window.set_status_from_app("Announced current time")

    def test_chime(self) -> None:
        if self.app.play_test_sound() and self.app.main_window:
            self.app.main_window.set_status_from_app("Test chime played from tray")

    def open_settings(self) -> None:
        self.show_main_window()
        if self.app.main_window:
            self.app.main_window.open_settings_dialog()

    def exit_application(self) -> None:
        self.app.request_exit()


class SystemTrayIcon(wx.adv.TaskBarIcon):
    """Accessible text-menu system tray icon."""

    def __init__(self, app: AccessiClockApp):
        super().__init__()
        self.action_handler = TrayActionHandler(app)
        self._icon = self._create_icon()
        self.SetIcon(self._icon, "AccessiClock")

        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self._on_left_click)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self._on_left_click)
        self.Bind(wx.adv.EVT_TASKBAR_RIGHT_DOWN, self._on_right_click)

    def _create_icon(self) -> wx.Icon:
        icon = wx.Icon()
        bitmap = wx.Bitmap(16, 16)
        dc = wx.MemoryDC(bitmap)
        dc.SetBackground(wx.Brush(wx.Colour(35, 35, 35)))
        dc.Clear()
        dc.SetTextForeground(wx.WHITE)
        dc.DrawText("A", 3, 0)
        dc.SelectObject(wx.NullBitmap)
        icon.CopyFromBitmap(bitmap)
        return icon

    def CreatePopupMenu(self) -> wx.Menu:
        menu = wx.Menu()
        show_item = menu.Append(wx.ID_ANY, TRAY_MENU_LABELS[0])
        announce_item = menu.Append(wx.ID_ANY, TRAY_MENU_LABELS[1])
        test_item = menu.Append(wx.ID_ANY, TRAY_MENU_LABELS[2])
        settings_item = menu.Append(wx.ID_ANY, TRAY_MENU_LABELS[3])
        menu.AppendSeparator()
        exit_item = menu.Append(wx.ID_ANY, TRAY_MENU_LABELS[4])

        self.Bind(wx.EVT_MENU, lambda _event: self.action_handler.show_main_window(), show_item)
        self.Bind(wx.EVT_MENU, lambda _event: self.action_handler.announce_time(), announce_item)
        self.Bind(wx.EVT_MENU, lambda _event: self.action_handler.test_chime(), test_item)
        self.Bind(wx.EVT_MENU, lambda _event: self.action_handler.open_settings(), settings_item)
        self.Bind(wx.EVT_MENU, lambda _event: self.action_handler.exit_application(), exit_item)
        return menu

    def update_tooltip(self, text: str) -> None:
        self.SetIcon(self._icon, text[:127] or "AccessiClock")

    def _on_left_click(self, event: wx.adv.TaskBarIconEvent) -> None:
        self.action_handler.show_main_window()

    def _on_right_click(self, event: wx.adv.TaskBarIconEvent) -> None:
        self.PopupMenu(self.CreatePopupMenu())

    def cleanup(self) -> None:
        try:
            self.RemoveIcon()
        except Exception:
            logger.debug("Unable to remove tray icon", exc_info=True)
        self.Destroy()

