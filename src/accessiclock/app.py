"""
A fully accessible clock desktop app, complete with clock sound packs
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from .utils.logging_config import setup_logging, get_logger
from .utils.error_handler import get_error_handler, ErrorCategory


class AccessiClock(toga.App):
    def __init__(self, *args, **kwargs):
        """Initialize the AccessiClock application."""
        super().__init__(*args, **kwargs)
        
        # Set up logging
        self.logger = setup_logging()
        self.logger.info("AccessiClock application initializing")
        
        # Set up error handling
        self.error_handler = get_error_handler(self)
        
        # Initialize component loggers
        self.app_logger = get_logger("app")
        
    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        try:
            self.app_logger.info("Starting up AccessiClock application")
            
            main_box = toga.Box()

            self.main_window = toga.MainWindow(title=self.formal_name)
            self.main_window.content = main_box
            self.main_window.show()
            
            self.app_logger.info("AccessiClock application startup completed")
            
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                ErrorCategory.UI, 
                "application startup",
                show_user_notification=True
            )
            raise
    
    def on_exit(self):
        """Handle application exit."""
        try:
            self.app_logger.info("AccessiClock application shutting down")
            # Cleanup will be added in future tasks
            return True
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI,
                "application shutdown",
                show_user_notification=False
            )
            return True


def main():
    return AccessiClock()
