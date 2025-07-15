"""
Tests for logging configuration and error handling framework.
"""

import pytest
import logging
import tempfile
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from accessiclock.utils.logging_config import setup_logging, get_logger
from accessiclock.utils.error_handler import ErrorHandler, ErrorCategory, AccessiClockError


class TestLoggingConfig:
    """Test logging configuration functionality."""
    
    def test_setup_logging_default(self):
        """Test default logging setup."""
        logger = setup_logging()
        assert logger.name == "accessiclock"
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1  # At least console handler
    
    def test_setup_logging_with_file(self):
        """Test logging setup with custom file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            logger = setup_logging(log_file=tmp_file.name)
            assert logger.name == "accessiclock"
            # Should have both console and file handlers
            assert len(logger.handlers) >= 2
    
    def test_get_logger(self):
        """Test getting module-specific logger."""
        logger = get_logger("test_module")
        assert logger.name == "accessiclock.test_module"


class TestErrorHandler:
    """Test error handling framework."""
    
    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        handler = ErrorHandler()
        assert handler.app is None
        assert handler.logger.name == "accessiclock.error_handler"
    
    def test_accessiclock_error(self):
        """Test AccessiClockError creation."""
        error = AccessiClockError("Test error", ErrorCategory.AUDIO)
        assert error.message == "Test error"
        assert error.category == ErrorCategory.AUDIO
        assert error.original_error is None
    
    def test_handle_error(self):
        """Test basic error handling."""
        handler = ErrorHandler()
        test_error = Exception("Test exception")
        
        result = handler.handle_error(
            test_error,
            ErrorCategory.AUDIO,
            context="test context",
            show_user_notification=False
        )
        
        assert result is True
    
    def test_category_specific_handlers(self):
        """Test category-specific error handlers."""
        handler = ErrorHandler()
        test_error = Exception("Test exception")
        
        # Test each category-specific handler
        assert handler.handle_audio_error(test_error, "test context") is True
        assert handler.handle_network_error(test_error, "test service") is True
        assert handler.handle_file_error(test_error, "test/path") is True
        assert handler.handle_config_error(test_error, "test config") is True
        assert handler.handle_tts_error(test_error, "test tts") is True
    
    def test_error_callback_registration(self):
        """Test error callback registration and execution."""
        handler = ErrorHandler()
        callback_called = False
        
        def test_callback(error, context):
            nonlocal callback_called
            callback_called = True
        
        handler.register_error_callback(ErrorCategory.AUDIO, test_callback)
        
        test_error = Exception("Test exception")
        handler.handle_error(
            test_error,
            ErrorCategory.AUDIO,
            show_user_notification=False
        )
        
        assert callback_called is True