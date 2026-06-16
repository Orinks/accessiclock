"""Audio output device picker dialog."""

from __future__ import annotations

from typing import TYPE_CHECKING

import wx

if TYPE_CHECKING:
    from ...app import AccessiClockApp


class AudioDeviceDialog(wx.Dialog):
    """Keyboard-friendly dialog for choosing the sound_lib output device."""

    def __init__(self, parent: wx.Window, app: AccessiClockApp):
        super().__init__(
            parent,
            title="Audio Device",
            size=(460, 220),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.app = app
        self._create_widgets()
        self.CentreOnParent()

    def _create_widgets(self) -> None:
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(panel, label="Audio output device:")
        main_sizer.Add(label, 0, wx.ALL, 10)

        choices = self.app.get_audio_output_devices()
        self.device_choice = wx.Choice(panel, choices=choices, name="Audio output device")
        current_name = self.app.audio_device_name or "Default system device"
        if current_name in choices:
            self.device_choice.SetSelection(choices.index(current_name))
        elif choices:
            self.device_choice.SetSelection(0)
        main_sizer.Add(self.device_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.test_button = wx.Button(panel, label="&Test Device")
        main_sizer.Add(self.test_button, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        buttons = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        ok_btn.SetDefault()
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        buttons.AddButton(ok_btn)
        buttons.AddButton(cancel_btn)
        buttons.Realize()
        main_sizer.Add(buttons, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        panel.SetSizer(main_sizer)
        self.test_button.Bind(wx.EVT_BUTTON, self._on_test_device)

    def get_selected_device_name(self) -> str:
        value = self.device_choice.GetStringSelection()
        return "" if value == "Default system device" else value

    def _on_test_device(self, event: wx.CommandEvent) -> None:
        previous = self.app.audio_device_name
        selected = self.get_selected_device_name()
        if self.app.set_audio_device(selected):
            self.app.play_test_sound()
        self.app.set_audio_device(previous)

