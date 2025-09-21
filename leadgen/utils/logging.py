"""Basic logging utilities until Rich/Loguru are available."""

import sys
from datetime import datetime
from typing import Optional


class Logger:
    """Simple logger with levels and colors."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self, name: str = "leadgen"):
        self.name = name
        self.level = "INFO"

    def _log(self, level: str, message: str, extra: Optional[str] = None):
        """Internal logging method."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = self.COLORS.get(level, "")
        reset = self.COLORS["RESET"]

        # Format: [HH:MM:SS] LEVEL: message
        log_msg = f"[{timestamp}] {color}{level}{reset}: {message}"

        if extra:
            log_msg += f" - {extra}"

        print(log_msg, file=sys.stderr if level == "ERROR" else sys.stdout)

    def debug(self, message: str, extra: Optional[str] = None):
        """Log debug message."""
        if self.level in ["DEBUG"]:
            self._log("DEBUG", message, extra)

    def info(self, message: str, extra: Optional[str] = None):
        """Log info message."""
        if self.level in ["DEBUG", "INFO"]:
            self._log("INFO", message, extra)

    def warning(self, message: str, extra: Optional[str] = None):
        """Log warning message."""
        if self.level in ["DEBUG", "INFO", "WARNING"]:
            self._log("WARNING", message, extra)

    def error(self, message: str, extra: Optional[str] = None):
        """Log error message."""
        self._log("ERROR", message, extra)

    def success(self, message: str, extra: Optional[str] = None):
        """Log success message in green."""
        self._log("INFO", f"✓ {message}", extra)


# Global logger instance
logger = Logger()
