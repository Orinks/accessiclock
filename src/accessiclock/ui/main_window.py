"""
Main window for AccessiClock using wxPython.

Provides the primary UI with clock display, controls, and full
keyboard/screen reader accessibility.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import wx
import wx.adv

from ..constants import TIME_FORMAT_12H, TIME_FORMAT_24H, VOLUME_LEVELS
from ..core.shortcuts import build_shortcut_help

if TYPE_CHECKING:
    from ..app import AccessiClockApp

logger = logging.getLogger(__name__)


class MainWindow(wx.Frame):
    """
    Main application window for AccessiClock.

    Features:
    - Large clock display (screen reader accessible)
    - Clock pack selection
    - Volume control
    - Chime interval configuration
    - Test and settings buttons
    """

    def __init__(self, app: AccessiClockApp):
        """
        Initialize the main window.

        Args:
            app: The AccessiClock application instance.
        """
        super().__init__(
            parent=None,
            title="AccessiClock",
            size=(720, 820),
            style=wx.DEFAULT_FRAME_STYLE,
        )
        self.app = app

        # Timer for clock updates
        self._clock_timer: wx.Timer | None = None

        # Create UI
        self._create_widgets()
        self._create_menu_bar()
        self._bind_events()
        self._setup_keyboard_shortcuts()

        # Start clock timer
        self._start_clock_timer()

        # Center window and set predictable focus once shown.
        self.Centre()
        wx.CallAfter(self._set_initial_focus)

        logger.info("Main window created")

    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        panel = wx.ScrolledWindow(self)
        panel.SetScrollRate(0, 20)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Clock display - large, readable, screen reader accessible
        clock_label = wx.StaticText(panel, label="Current Time:")
        main_sizer.Add(clock_label, 0, wx.LEFT | wx.TOP, 10)

        self.clock_display = wx.TextCtrl(
            panel,
            value=self._get_current_time(),
            style=wx.TE_READONLY | wx.TE_CENTER,
            name="Current time display",
        )
        # Make it large and readable
        font = self.clock_display.GetFont()
        font.SetPointSize(28)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.clock_display.SetFont(font)
        main_sizer.Add(self.clock_display, 0, wx.EXPAND | wx.ALL, 10)

        # Status label for screen reader feedback
        self.status_label = wx.StaticText(
            panel,
            label="Ready. Use Tab to navigate controls.",
            name="Status",
        )
        main_sizer.Add(self.status_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Clock pack selection
        clock_sizer = wx.BoxSizer(wx.HORIZONTAL)
        clock_label = wx.StaticText(panel, label="Clock:")
        clock_sizer.Add(clock_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        # Get available clocks from app
        clock_choices = self.app.get_available_clocks()
        current_clock = self._get_clock_display_name(self.app.selected_clock)

        self.clock_selection = wx.ComboBox(
            panel,
            choices=clock_choices,
            value=current_clock if current_clock in clock_choices else clock_choices[0],
            style=wx.CB_READONLY,
            name="Clock pack selection",
        )
        clock_sizer.Add(self.clock_selection, 1, wx.EXPAND)
        main_sizer.Add(clock_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        main_sizer.AddSpacer(10)

        # Volume control
        volume_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.volume_label = wx.StaticText(
            panel,
            label=f"Volume: {self.app.current_volume}%",
        )
        volume_sizer.Add(self.volume_label, 1, wx.ALIGN_CENTER_VERTICAL)

        self.volume_button = wx.Button(panel, label="Change &Volume")
        volume_sizer.Add(self.volume_button, 0)
        main_sizer.Add(volume_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        main_sizer.AddSpacer(10)

        # Audio backend status
        backend_text = self._get_audio_backend_text()
        self.backend_label = wx.StaticText(panel, label=f"Audio backend: {backend_text}")
        main_sizer.Add(self.backend_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        audio_device_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.audio_device_label = wx.StaticText(
            panel,
            label=f"Audio output: {self._get_audio_device_text()}",
        )
        audio_device_sizer.Add(self.audio_device_label, 1, wx.ALIGN_CENTER_VERTICAL)
        self.audio_device_button = wx.Button(panel, label="Audio &Device...")
        audio_device_sizer.Add(self.audio_device_button, 0)
        main_sizer.Add(audio_device_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Chime intervals
        intervals_label = wx.StaticText(panel, label="Chime Intervals:")
        intervals_label.SetFont(
            intervals_label.GetFont().Bold()
        )
        main_sizer.Add(intervals_label, 0, wx.LEFT, 10)

        self.hourly_checkbox = wx.CheckBox(panel, label="&Hourly chimes")
        self.hourly_checkbox.SetValue(self.app.chime_hourly)
        main_sizer.Add(self.hourly_checkbox, 0, wx.LEFT | wx.TOP, 15)

        self.half_hour_checkbox = wx.CheckBox(panel, label="Ha&lf-hour chimes")
        self.half_hour_checkbox.SetValue(self.app.chime_half_hour)
        main_sizer.Add(self.half_hour_checkbox, 0, wx.LEFT | wx.TOP, 15)

        self.quarter_hour_checkbox = wx.CheckBox(panel, label="&Quarter-hour chimes")
        self.quarter_hour_checkbox.SetValue(self.app.chime_quarter_hour)
        main_sizer.Add(self.quarter_hour_checkbox, 0, wx.LEFT | wx.TOP, 15)

        main_sizer.AddSpacer(10)

        # Chime style and extra scheduled sounds
        style_sizer = wx.BoxSizer(wx.HORIZONTAL)
        style_label = wx.StaticText(panel, label="Chime style:")
        style_sizer.Add(style_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        self.chime_style_choice = wx.Choice(
            panel,
            choices=["Classic single chime", "Grandfather counted chimes"],
        )
        self.chime_style_choice.SetSelection(1 if self.app.chime_style == "grandfather" else 0)
        style_sizer.Add(self.chime_style_choice, 1, wx.EXPAND)
        main_sizer.Add(style_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.hour_count_checkbox = wx.CheckBox(panel, label="Count the hour on hourly chimes")
        self.hour_count_checkbox.SetValue(self.app.hour_count_chimes)
        main_sizer.Add(self.hour_count_checkbox, 0, wx.LEFT | wx.TOP, 15)

        self.minute_tick_checkbox = wx.CheckBox(panel, label="Play a minute tick")
        self.minute_tick_checkbox.SetValue(self.app.minute_tick)
        main_sizer.Add(self.minute_tick_checkbox, 0, wx.LEFT | wx.TOP, 15)

        main_sizer.AddSpacer(12)

        # Quiet hours controls
        quiet_label = wx.StaticText(panel, label="Quiet Hours:")
        quiet_label.SetFont(quiet_label.GetFont().Bold())
        main_sizer.Add(quiet_label, 0, wx.LEFT, 10)

        self.quiet_enabled_checkbox = wx.CheckBox(panel, label="Enable quiet hours")
        self.quiet_enabled_checkbox.SetValue(self.app.quiet_hours_enabled)
        main_sizer.Add(self.quiet_enabled_checkbox, 0, wx.LEFT | wx.TOP, 15)

        quiet_start_hour, quiet_start_minute = self._parse_hhmm(self.app.quiet_start, "22:00")
        quiet_end_hour, quiet_end_minute = self._parse_hhmm(self.app.quiet_end, "07:00")

        quiet_start_sizer = wx.BoxSizer(wx.HORIZONTAL)
        quiet_start_hour_label = wx.StaticText(panel, label="Quiet start hour:")
        quiet_start_sizer.Add(quiet_start_hour_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.quiet_start_hour_spin = wx.SpinCtrl(
            panel, min=0, max=23, initial=quiet_start_hour, size=(70, -1)
        )
        quiet_start_sizer.Add(self.quiet_start_hour_spin, 0, wx.RIGHT, 12)
        quiet_start_minute_label = wx.StaticText(panel, label="Quiet start minute:")
        quiet_start_sizer.Add(quiet_start_minute_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.quiet_start_minute_spin = wx.SpinCtrl(
            panel, min=0, max=59, initial=quiet_start_minute, size=(70, -1)
        )
        quiet_start_sizer.Add(self.quiet_start_minute_spin, 0)
        main_sizer.Add(quiet_start_sizer, 0, wx.LEFT | wx.RIGHT | wx.TOP, 15)

        quiet_end_sizer = wx.BoxSizer(wx.HORIZONTAL)
        quiet_end_hour_label = wx.StaticText(panel, label="Quiet end hour:")
        quiet_end_sizer.Add(quiet_end_hour_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.quiet_end_hour_spin = wx.SpinCtrl(
            panel, min=0, max=23, initial=quiet_end_hour, size=(70, -1)
        )
        quiet_end_sizer.Add(self.quiet_end_hour_spin, 0, wx.RIGHT, 12)
        quiet_end_minute_label = wx.StaticText(panel, label="Quiet end minute:")
        quiet_end_sizer.Add(quiet_end_minute_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.quiet_end_minute_spin = wx.SpinCtrl(
            panel, min=0, max=59, initial=quiet_end_minute, size=(70, -1)
        )
        quiet_end_sizer.Add(self.quiet_end_minute_spin, 0)
        main_sizer.Add(quiet_end_sizer, 0, wx.LEFT | wx.RIGHT | wx.TOP, 15)

        main_sizer.AddSpacer(12)

        # Alarm controls
        alarm_label = wx.StaticText(panel, label="Alarm:")
        alarm_label.SetFont(alarm_label.GetFont().Bold())
        main_sizer.Add(alarm_label, 0, wx.LEFT, 10)

        self.alarm_enabled_checkbox = wx.CheckBox(panel, label="Enable alarm")
        self.alarm_enabled_checkbox.SetValue(self.app.alarm_enabled)
        main_sizer.Add(self.alarm_enabled_checkbox, 0, wx.LEFT | wx.TOP, 15)

        alarm_time_sizer = wx.BoxSizer(wx.HORIZONTAL)
        alarm_hour_label = wx.StaticText(panel, label="Alarm hour:")
        alarm_time_sizer.Add(alarm_hour_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        alarm_hour, alarm_minute = self._parse_hhmm(self.app.alarm_time, "07:00")
        self.alarm_hour_spin = wx.SpinCtrl(panel, min=0, max=23, initial=alarm_hour, size=(70, -1))
        alarm_time_sizer.Add(self.alarm_hour_spin, 0, wx.RIGHT, 12)

        alarm_minute_label = wx.StaticText(panel, label="Alarm minute:")
        alarm_time_sizer.Add(alarm_minute_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        self.alarm_minute_spin = wx.SpinCtrl(
            panel, min=0, max=59, initial=alarm_minute, size=(70, -1)
        )
        alarm_time_sizer.Add(self.alarm_minute_spin, 0)
        main_sizer.Add(alarm_time_sizer, 0, wx.LEFT | wx.RIGHT | wx.TOP, 15)

        self.alarm_sound_checkbox = wx.CheckBox(panel, label="Play alarm sound")
        self.alarm_sound_checkbox.SetValue(self.app.alarm_sound_enabled)
        main_sizer.Add(self.alarm_sound_checkbox, 0, wx.LEFT | wx.TOP, 15)

        alarm_text_label = wx.StaticText(panel, label="Alarm spoken text:")
        main_sizer.Add(alarm_text_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        self.alarm_text_ctrl = wx.TextCtrl(panel, value=self.app.alarm_spoken_text)
        main_sizer.Add(self.alarm_text_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        main_sizer.AddSpacer(15)

        # Action buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.test_button = wx.Button(panel, label="&Test Chime")
        button_sizer.Add(self.test_button, 0, wx.RIGHT, 10)

        self.announce_button = wx.Button(panel, label="&Announce Time")
        button_sizer.Add(self.announce_button, 0, wx.RIGHT, 10)

        self.test_alarm_button = wx.Button(panel, label="Test &Alarm")
        button_sizer.Add(self.test_alarm_button, 0, wx.RIGHT, 10)

        self.settings_button = wx.Button(panel, label="&Settings")
        button_sizer.Add(self.settings_button, 0)

        main_sizer.Add(button_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(main_sizer)

    def _create_menu_bar(self) -> None:
        """Create the menu bar."""
        menubar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        settings_item = file_menu.Append(wx.ID_PREFERENCES, "&Settings\tCtrl+,")
        audio_device_item = file_menu.Append(wx.ID_ANY, "Audio &Device...\tCtrl+D")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tAlt+F4")
        menubar.Append(file_menu, "&File")

        # Clock menu
        clock_menu = wx.Menu()
        test_item = clock_menu.Append(wx.ID_ANY, "&Test Chime\tF5")
        announce_item = clock_menu.Append(wx.ID_ANY, "&Announce Time\tSpace")
        clock_menu.AppendSeparator()
        manage_item = clock_menu.Append(wx.ID_ANY, "&Manage Clocks...")
        menubar.Append(clock_menu, "&Clock")

        # Help menu
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "&About AccessiClock")
        menubar.Append(help_menu, "&Help")

        self.SetMenuBar(menubar)

        # Bind menu events
        self.Bind(wx.EVT_MENU, self._on_settings, settings_item)
        self.Bind(wx.EVT_MENU, self._on_audio_device, audio_device_item)
        self.Bind(wx.EVT_MENU, self._on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self._on_test_chime, test_item)
        self.Bind(wx.EVT_MENU, self._on_announce_time, announce_item)
        self.Bind(wx.EVT_MENU, self._on_manage_clocks, manage_item)
        self.Bind(wx.EVT_MENU, self._on_about, about_item)

    def _bind_events(self) -> None:
        """Bind event handlers."""
        # Window events
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_ICONIZE, self._on_iconize)

        # Control events
        self.clock_selection.Bind(wx.EVT_COMBOBOX, self._on_clock_changed)
        self.volume_button.Bind(wx.EVT_BUTTON, self._on_change_volume)
        self.audio_device_button.Bind(wx.EVT_BUTTON, self._on_audio_device)
        self.hourly_checkbox.Bind(wx.EVT_CHECKBOX, self._on_interval_changed)
        self.half_hour_checkbox.Bind(wx.EVT_CHECKBOX, self._on_interval_changed)
        self.quarter_hour_checkbox.Bind(wx.EVT_CHECKBOX, self._on_interval_changed)
        self.chime_style_choice.Bind(wx.EVT_CHOICE, self._on_chime_options_changed)
        self.hour_count_checkbox.Bind(wx.EVT_CHECKBOX, self._on_chime_options_changed)
        self.minute_tick_checkbox.Bind(wx.EVT_CHECKBOX, self._on_chime_options_changed)
        self.quiet_enabled_checkbox.Bind(wx.EVT_CHECKBOX, self._on_quiet_hours_changed)
        self.quiet_start_hour_spin.Bind(wx.EVT_SPINCTRL, self._on_quiet_hours_changed)
        self.quiet_start_minute_spin.Bind(wx.EVT_SPINCTRL, self._on_quiet_hours_changed)
        self.quiet_end_hour_spin.Bind(wx.EVT_SPINCTRL, self._on_quiet_hours_changed)
        self.quiet_end_minute_spin.Bind(wx.EVT_SPINCTRL, self._on_quiet_hours_changed)
        self.alarm_enabled_checkbox.Bind(wx.EVT_CHECKBOX, self._on_alarm_changed)
        self.alarm_hour_spin.Bind(wx.EVT_SPINCTRL, self._on_alarm_changed)
        self.alarm_minute_spin.Bind(wx.EVT_SPINCTRL, self._on_alarm_changed)
        self.alarm_sound_checkbox.Bind(wx.EVT_CHECKBOX, self._on_alarm_changed)
        self.alarm_text_ctrl.Bind(wx.EVT_TEXT, self._on_alarm_changed)
        self.test_button.Bind(wx.EVT_BUTTON, self._on_test_chime)
        self.announce_button.Bind(wx.EVT_BUTTON, self._on_announce_time)
        self.test_alarm_button.Bind(wx.EVT_BUTTON, self._on_test_alarm)
        self.settings_button.Bind(wx.EVT_BUTTON, self._on_settings)

    def _setup_keyboard_shortcuts(self) -> None:
        """Set up keyboard shortcuts and announce map in logs/status."""
        logger.info("Shortcut map: %s", build_shortcut_help())
        entries = []
        for keycode, handler in [
            (wx.WXK_F5, self._on_test_chime),
            (ord(" "), self._on_announce_time),
        ]:
            item_id = wx.NewIdRef()
            self.Bind(wx.EVT_MENU, handler, id=item_id)
            entries.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, keycode, item_id))

        audio_id = wx.NewIdRef()
        self.Bind(wx.EVT_MENU, self._on_audio_device, id=audio_id)
        entries.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D"), audio_id))

        settings_id = wx.NewIdRef()
        self.Bind(wx.EVT_MENU, self._on_settings, id=settings_id)
        entries.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord(","), settings_id))
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def _set_initial_focus(self) -> None:
        """Move focus to a stable control to help screen reader users on startup."""
        if self.clock_selection and self.clock_selection.IsShownOnScreen():
            self.clock_selection.SetFocus()
            self._set_status("Ready. Focus is on clock selection. Use Tab to navigate.")

    def _start_clock_timer(self) -> None:
        """Start the clock update timer."""
        self._clock_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_clock_tick, self._clock_timer)
        self._clock_timer.Start(1000)  # Update every second
        logger.info("Clock timer started")

    def _get_current_time(self) -> str:
        """Get the current time as a formatted string."""
        fmt = TIME_FORMAT_24H if self.app.config.get("time_format") == "24h" else TIME_FORMAT_12H
        return datetime.now().strftime(fmt)

    def _get_audio_backend_text(self) -> str:
        """Return current audio backend status for the UI."""
        if not self.app.audio_player:
            return "unavailable"
        return getattr(self.app.audio_player, "backend_name", "available")

    def _get_audio_device_text(self) -> str:
        """Return the configured audio device display text."""
        return self.app.audio_device_name or "Default system device"

    def _parse_hhmm(self, value: str, default: str) -> tuple[int, int]:
        """Parse HH:MM text for spin controls."""
        try:
            hour_text, minute_text = (value or default).split(":")
            hour = max(0, min(23, int(hour_text)))
            minute = max(0, min(59, int(minute_text)))
        except (TypeError, ValueError):
            hour_text, minute_text = default.split(":")
            hour = int(hour_text)
            minute = int(minute_text)
        return hour, minute

    def _get_clock_display_name(self, pack_id: str) -> str:
        """Get the display name for a clock pack ID."""
        if self.app.clock_pack_loader:
            pack_info = self.app.clock_pack_loader.get_pack(pack_id)
            if pack_info:
                return pack_info.name
        return pack_id.title()

    def _get_clock_pack_id(self, display_name: str) -> str:
        """Get the pack ID for a clock display name."""
        if self.app.clock_pack_loader:
            for pack_id, pack_info in self.app.clock_pack_loader._cache.items():
                if pack_info.name == display_name:
                    return pack_id
        return display_name.lower()

    # --- Event Handlers ---

    def _on_clock_tick(self, event: wx.TimerEvent) -> None:
        """Handle clock timer tick."""
        self.clock_display.SetValue(self._get_current_time())
        if self.app.system_tray_icon:
            self.app.system_tray_icon.update_tooltip(f"AccessiClock {self._get_current_time()}")

        if self.app.check_and_trigger_alarm():
            self._set_status("Alarm triggered")
            return

        # Check for chime intervals and play sounds
        chime_played = self.app.check_and_play_chime()
        if chime_played:
            self._set_status(f"Playing {chime_played.replace('_', ' ')}")

    def _on_clock_changed(self, event: wx.CommandEvent) -> None:
        """Handle clock pack selection change."""
        display_name = self.clock_selection.GetValue()
        pack_id = self._get_clock_pack_id(display_name)
        self.app.selected_clock = pack_id
        self._set_status(f"Clock changed to: {display_name}")
        self.app.save_config()
        logger.info(f"Clock pack changed to: {pack_id} ({display_name})")

    def _on_change_volume(self, event: wx.CommandEvent) -> None:
        """Handle volume button press - cycle through volume levels."""
        try:
            current_index = VOLUME_LEVELS.index(self.app.current_volume)
        except ValueError:
            current_index = 2  # Default to 50%

        next_index = (current_index + 1) % len(VOLUME_LEVELS)
        new_volume = VOLUME_LEVELS[next_index]

        self.app.set_volume(new_volume)
        self.volume_label.SetLabel(f"Volume: {new_volume}%")
        self._set_status(f"Volume set to {new_volume}%")
        logger.info(f"Volume changed to: {new_volume}%")

    def _on_audio_device(self, event: wx.CommandEvent) -> None:
        self.open_audio_device_dialog()

    def _on_interval_changed(self, event: wx.CommandEvent) -> None:
        """Handle chime interval checkbox changes."""
        self.app.chime_hourly = self.hourly_checkbox.GetValue()
        self.app.chime_half_hour = self.half_hour_checkbox.GetValue()
        self.app.chime_quarter_hour = self.quarter_hour_checkbox.GetValue()

        intervals = []
        if self.app.chime_hourly:
            intervals.append("hourly")
        if self.app.chime_half_hour:
            intervals.append("half-hour")
        if self.app.chime_quarter_hour:
            intervals.append("quarter-hour")

        interval_text = ", ".join(intervals) if intervals else "none"
        self._set_status(f"Chime intervals: {interval_text}")
        self.app.save_config()
        logger.info(f"Chime intervals updated: {interval_text}")

    def _on_chime_options_changed(self, event: wx.CommandEvent) -> None:
        """Handle chime style, hour count, and minute tick changes."""
        self.app.chime_style = (
            "grandfather" if self.chime_style_choice.GetSelection() == 1 else "classic"
        )
        self.app.hour_count_chimes = self.hour_count_checkbox.GetValue()
        self.app.minute_tick = self.minute_tick_checkbox.GetValue()
        if self.app.clock_service:
            self.app.clock_service.reset_chime_tracking()

        style_text = "grandfather counted chimes" if self.app.chime_style == "grandfather" else "classic single chime"
        tick_text = "minute tick on" if self.app.minute_tick else "minute tick off"
        hour_count_text = "hour count on" if self.app.hour_count_chimes else "hour count off"
        self._set_status(f"Chime style: {style_text}; {hour_count_text}; {tick_text}")
        self.app.save_config()
        logger.info("Chime options updated: %s, %s, %s", style_text, hour_count_text, tick_text)

    def _on_quiet_hours_changed(self, event: wx.CommandEvent) -> None:
        """Handle quiet hours changes."""
        if self.quiet_enabled_checkbox.GetValue() and self.app.clock_service:
            from datetime import time

            start = time(
                self.quiet_start_hour_spin.GetValue(),
                self.quiet_start_minute_spin.GetValue(),
            )
            end = time(
                self.quiet_end_hour_spin.GetValue(),
                self.quiet_end_minute_spin.GetValue(),
            )
            self.app.clock_service.set_quiet_hours(start, end)
            self.app.quiet_hours_enabled = True
            self.app.quiet_start = f"{start.hour:02d}:{start.minute:02d}"
            self.app.quiet_end = f"{end.hour:02d}:{end.minute:02d}"
        elif self.app.clock_service:
            self.app.clock_service.quiet_hours_enabled = False
            self.app.quiet_hours_enabled = False
            self.app.quiet_start = (
                f"{self.quiet_start_hour_spin.GetValue():02d}:"
                f"{self.quiet_start_minute_spin.GetValue():02d}"
            )
            self.app.quiet_end = (
                f"{self.quiet_end_hour_spin.GetValue():02d}:"
                f"{self.quiet_end_minute_spin.GetValue():02d}"
            )
        self.app.save_config()
        state = "enabled" if self.app.quiet_hours_enabled else "disabled"
        self._set_status(
            f"Quiet hours {state}: {self.app.quiet_start} to {self.app.quiet_end}"
        )

    def _on_alarm_changed(self, event: wx.CommandEvent) -> None:
        """Handle alarm option changes."""
        self._sync_alarm_from_controls(save=True)
        state = "enabled" if self.app.alarm_enabled else "disabled"
        self._set_status(f"Alarm {state} for {self.app.alarm_time}")

    def _sync_alarm_from_controls(self, *, save: bool) -> None:
        """Copy alarm UI state into the app and clock service."""
        self.app.alarm_enabled = self.alarm_enabled_checkbox.GetValue()
        self.app.alarm_time = (
            f"{self.alarm_hour_spin.GetValue():02d}:{self.alarm_minute_spin.GetValue():02d}"
        )
        self.app.alarm_sound_enabled = self.alarm_sound_checkbox.GetValue()
        self.app.alarm_spoken_text = self.alarm_text_ctrl.GetValue().strip() or "Time to get up"
        if save:
            self.app.save_config()

    def _on_test_chime(self, event: wx.CommandEvent) -> None:
        """Handle test chime button/menu."""
        self._set_status("Playing test chime...")
        if self.app.play_test_sound():
            self._set_status(f"Test chime played at {self.app.current_volume}% volume")
        else:
            self._set_status("Could not play test chime - audio not available")

    def _on_announce_time(self, event: wx.CommandEvent) -> None:
        """Handle announce time button/menu."""
        current_time = self._get_current_time()
        
        if self.app.announce_time(style=self.app.config.get("announcement_style", "simple")):
            self._set_status(f"Announced: {current_time}")
        else:
            # TTS not available, just show status
            self._set_status(f"The time is {current_time}")
        
        logger.info(f"Time announced: {current_time}")

    def _on_test_alarm(self, event: wx.CommandEvent) -> None:
        """Play the configured alarm sound/message immediately."""
        self._sync_alarm_from_controls(save=True)
        did_anything = False
        if self.app.alarm_sound_enabled:
            did_anything = self.app.play_chime("alarm") or did_anything
        if self.app.alarm_spoken_text and self.app.tts_engine:
            self.app.tts_engine.speak(self.app.alarm_spoken_text)
            did_anything = True
        if did_anything:
            self._set_status("Test alarm played")
        else:
            self._set_status("Could not test alarm - audio and speech unavailable")

    def _on_settings(self, event: wx.CommandEvent) -> None:
        """Handle settings button/menu."""
        self.open_settings_dialog()

    def open_settings_dialog(self) -> None:
        """Open settings from buttons, menu items, or the tray menu."""
        from .dialogs import SettingsDialog
        
        dlg = SettingsDialog(self, self.app)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()
        self._refresh_runtime_labels()
        
        self._set_status("Settings updated")
        logger.info("Settings dialog closed")

    def open_audio_device_dialog(self) -> None:
        """Open the audio-device picker and apply the selected output."""
        from .dialogs import AudioDeviceDialog

        dlg = AudioDeviceDialog(self, self.app)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                selected = dlg.get_selected_device_name()
                if self.app.set_audio_device(selected):
                    self._refresh_runtime_labels()
                    self._set_status(f"Audio output: {self._get_audio_device_text()}")
                else:
                    self._set_status("Could not change audio output device")
        finally:
            dlg.Destroy()

    def _refresh_runtime_labels(self) -> None:
        self.backend_label.SetLabel(f"Audio backend: {self._get_audio_backend_text()}")
        self.audio_device_label.SetLabel(f"Audio output: {self._get_audio_device_text()}")

    def _on_manage_clocks(self, event: wx.CommandEvent) -> None:
        """Handle manage clocks menu item."""
        from .dialogs import ClockManagerDialog
        
        dlg = ClockManagerDialog(self, self.app)
        dlg.ShowModal()
        dlg.Destroy()
        
        # Refresh clock selection in case packs changed
        self._refresh_clock_choices()
        self._set_status("Clock manager closed")
        logger.info("Clock manager dialog closed")
    
    def _refresh_clock_choices(self) -> None:
        """Refresh the clock pack dropdown."""
        clock_choices = self.app.get_available_clocks()
        current_selection = self.clock_selection.GetValue()
        
        self.clock_selection.Clear()
        for choice in clock_choices:
            self.clock_selection.Append(choice)
        
        # Try to restore selection
        if current_selection in clock_choices:
            self.clock_selection.SetValue(current_selection)
        elif clock_choices:
            self.clock_selection.SetSelection(0)

    def _on_about(self, event: wx.CommandEvent) -> None:
        """Show about dialog."""
        from ..constants import APP_NAME, APP_VERSION

        info = wx.adv.AboutDialogInfo()
        info.SetName(APP_NAME)
        info.SetVersion(APP_VERSION)
        info.SetDescription(
            "An accessible talking clock with customizable\n"
            "clock packs and AI voice support.\n\n"
            "Designed for screen reader users."
        )
        info.SetCopyright("© 2025 Orinks")
        info.SetWebSite("https://github.com/orinks/AccessiClock")

        wx.adv.AboutBox(info)

    def _on_exit(self, event: wx.CommandEvent) -> None:
        """Handle exit menu item."""
        self.app.request_exit()

    def _on_close(self, event: wx.CloseEvent) -> None:
        """Handle window close."""
        logger.info("Main window closing")
        if self.app.should_minimize_to_tray():
            event.Veto()
            self.Hide()
            self._set_status("AccessiClock minimized to the system tray")
            return

        # Stop timer
        if self._clock_timer:
            self._clock_timer.Stop()

        # Save config
        self.app.save_config()

        # Destroy window
        self.Destroy()

    def _on_iconize(self, event: wx.IconizeEvent) -> None:
        """Hide the window when minimized if tray minimization is enabled."""
        if event.IsIconized() and self.app.should_minimize_to_tray():
            self.Hide()
            self._set_status("AccessiClock minimized to the system tray")
            return
        event.Skip()

    def _set_status(self, message: str) -> None:
        """Update the status label."""
        self.status_label.SetLabel(message)
        logger.debug(f"Status: {message}")

    def set_status_from_app(self, message: str) -> None:
        """Allow app/tray actions to update the accessible status text."""
        self._set_status(message)
