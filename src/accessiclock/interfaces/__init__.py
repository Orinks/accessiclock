"""
Interface abstractions for AccessiClock application.

This package contains abstract interfaces that allow for easy testing
and potential backend swapping.
"""

from .audio_interface import AudioBackend, MockAudioBackend, AudioType

__all__ = ['AudioBackend', 'MockAudioBackend', 'AudioType']