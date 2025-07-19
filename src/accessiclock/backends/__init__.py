"""
Audio backend implementations for AccessiClock application.

This package contains concrete implementations of the AudioBackend interface.
"""

from .pygame_backend import PygameAudioBackend

__all__ = ['PygameAudioBackend']