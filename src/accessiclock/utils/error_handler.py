"""
Error handling framework for AccessiClock application.

This module provides centralized error handling with categorized error types
and appropriate fallback mechanisms.
"""

import logging
from enum import Enum
from typing import Optional, Callable, Any
import traceback


class ErrorCategory(Enum):
    """Categories of errors that can occur in the application."""
    AUDIO = "audio"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    CONFIGURATION = "configuration"
    PLATFORM = "platform"
    TTS = "tts"
    UI = "ui"


class AccessiClockError(Exception):
    """Base exception class for AccessiClock application errors."""
    
    def __init__(self, message: str, category: ErrorCategory, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.category = category
        self.original_error = original_error
        self.message = message


class ErrorHandler:
    """
    Centralized error handling system for the AccessiClock application.
    
    Provides categorized error handling with appropriate fallback mechanisms
    and user notifications.
    """
    
    def __init__(self, app_instance=None):
        """
        Initialize the error handler.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance
        self.logger = logging.getLogger("accessiclock.error_handler")
        self._error_callbacks = {}
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable):
        """
        Register a callback function for specific error categories.
        
        Args:
            category: Error category to handle
            callback: Function to call when this error category occurs
        """
        self._error_callbacks[category] = callback
    
    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory,
        context: str = "",
        fallback_action: Optional[Callable] = None,
        show_user_notification: bool = True
    ) -> bool:
        """
        Handle an error with appropriate logging, fallbacks, and user notification.
        
        Args:
            error: The exception that occurred
            category: Category of the error
            context: Additional context about where the error occurred
            fallback_action: Optional fallback action to execute
            show_user_notification: Whether to show notification to user
            
        Returns:
            True if error was handled successfully, False otherwise
        """
        # Create AccessiClock error if not already one
        if not isinstance(error, AccessiClockError):
            error = AccessiClockError(str(error), category, error)
        
        # Log the error
        error_msg = f"{category.value.upper()} ERROR"
        if context:
            error_msg += f" in {context}"
        error_msg += f": {error.message}"
        
        self.logger.error(error_msg)
        if error.original_error:
            self.logger.debug(f"Original error: {traceback.format_exc()}")
        
        # Execute category-specific callback if registered
        if category in self._error_callbacks:
            try:
                self._error_callbacks[category](error, context)
            except Exception as callback_error:
                self.logger.error(f"Error in callback for {category.value}: {callback_error}")
        
        # Execute fallback action if provided
        if fallback_action:
            try:
                fallback_action()
                self.logger.info(f"Fallback action executed for {category.value} error")
            except Exception as fallback_error:
                self.logger.error(f"Fallback action failed: {fallback_error}")
        
        # Show user notification if requested and app is available
        if show_user_notification and self.app:
            self._show_user_notification(error, category, context)
        
        return True
    
    def handle_audio_error(self, error: Exception, context: str = "", fallback_action: Optional[Callable] = None):
        """Handle audio-related errors."""
        return self.handle_error(error, ErrorCategory.AUDIO, context, fallback_action)
    
    def handle_network_error(self, error: Exception, service: str = "", fallback_action: Optional[Callable] = None):
        """Handle network-related errors."""
        context = f"service: {service}" if service else ""
        return self.handle_error(error, ErrorCategory.NETWORK, context, fallback_action)
    
    def handle_file_error(self, error: Exception, file_path: str = "", fallback_action: Optional[Callable] = None):
        """Handle file system errors."""
        context = f"file: {file_path}" if file_path else ""
        return self.handle_error(error, ErrorCategory.FILE_SYSTEM, context, fallback_action)
    
    def handle_config_error(self, error: Exception, config_type: str = "", fallback_action: Optional[Callable] = None):
        """Handle configuration errors."""
        context = f"config: {config_type}" if config_type else ""
        return self.handle_error(error, ErrorCategory.CONFIGURATION, context, fallback_action)
    
    def handle_tts_error(self, error: Exception, tts_service: str = "", fallback_action: Optional[Callable] = None):
        """Handle text-to-speech errors."""
        context = f"TTS service: {tts_service}" if tts_service else ""
        return self.handle_error(error, ErrorCategory.TTS, context, fallback_action)
    
    def _show_user_notification(self, error: AccessiClockError, category: ErrorCategory, context: str):
        """
        Show user-friendly error notification.
        
        Args:
            error: The error that occurred
            category: Error category
            context: Additional context
        """
        try:
            # Create user-friendly error messages
            user_messages = {
                ErrorCategory.AUDIO: "Audio system error. Some sounds may not play correctly.",
                ErrorCategory.NETWORK: "Network connection error. Some features may be unavailable.",
                ErrorCategory.FILE_SYSTEM: "File access error. Check file permissions.",
                ErrorCategory.CONFIGURATION: "Configuration error. Settings may have been reset.",
                ErrorCategory.PLATFORM: "Platform-specific error occurred.",
                ErrorCategory.TTS: "Text-to-speech error. Voice announcements may not work.",
                ErrorCategory.UI: "User interface error occurred."
            }
            
            title = f"AccessiClock - {category.value.title()} Error"
            message = user_messages.get(category, "An unexpected error occurred.")
            
            # If we have access to the app, show a dialog
            if hasattr(self.app, 'main_window') and self.app.main_window:
                # Note: This would need to be implemented with actual Toga dialog
                # For now, just log the user message
                self.logger.info(f"User notification: {title} - {message}")
            else:
                self.logger.info(f"User notification: {title} - {message}")
                
        except Exception as notification_error:
            self.logger.error(f"Failed to show user notification: {notification_error}")


# Global error handler instance
_global_error_handler = None


def get_error_handler(app_instance=None) -> ErrorHandler:
    """
    Get the global error handler instance.
    
    Args:
        app_instance: Optional app instance to set if not already set
        
    Returns:
        Global ErrorHandler instance
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(app_instance)
    elif app_instance and not _global_error_handler.app:
        _global_error_handler.app = app_instance
    return _global_error_handler