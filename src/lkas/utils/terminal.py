"""
Terminal utilities for structured logging with persistent footer.

Provides clean, organized output similar to installation progress displays:
- Main log area (scrolling content)
- Persistent footer line (status/progress)
"""

import sys
import threading
import time
from typing import Optional


class TerminalDisplay:
    """
    Manages terminal display with a persistent footer line.

    This creates a two-section display:
    1. Main content area (scrolls normally)
    2. Footer line (stays at bottom, updates in-place)

    Similar to how npm/apt show progress during installation.
    """

    def __init__(self, enable_footer: bool = True):
        """
        Initialize terminal display.

        Args:
            enable_footer: Whether to enable the persistent footer
        """
        self.enable_footer = enable_footer
        self.footer_text = ""
        self.lock = threading.Lock()
        self._has_footer = False

        # ANSI escape codes
        self.CLEAR_LINE = "\033[2K"
        self.CURSOR_UP = "\033[1A"
        self.CURSOR_DOWN = "\033[1B"
        self.SAVE_CURSOR = "\033[s"
        self.RESTORE_CURSOR = "\033[u"
        self.HIDE_CURSOR = "\033[?25l"
        self.SHOW_CURSOR = "\033[?25h"

    def print(self, message: str, prefix: str = ""):
        """
        Print a message to the main content area.

        Args:
            message: Message to print
            prefix: Optional prefix (e.g., "[DETECTION]")
        """
        with self.lock:
            # Clear footer if present
            if self._has_footer and self.enable_footer:
                sys.stdout.write(self.CLEAR_LINE + "\r")

            # Print the actual message
            if prefix:
                sys.stdout.write(f"{prefix} {message}\n")
            else:
                sys.stdout.write(f"{message}\n")

            # Restore footer if enabled
            if self.enable_footer and self.footer_text:
                sys.stdout.write(self.footer_text)
                sys.stdout.flush()
                self._has_footer = True
            else:
                sys.stdout.flush()
                self._has_footer = False

    def update_footer(self, text: str):
        """
        Update the persistent footer line.

        Args:
            text: Footer text to display
        """
        if not self.enable_footer:
            return

        with self.lock:
            # Clear current footer if present
            if self._has_footer:
                sys.stdout.write(self.CLEAR_LINE + "\r")

            # Write new footer
            self.footer_text = text
            sys.stdout.write(text)
            sys.stdout.flush()
            self._has_footer = True

    def clear_footer(self):
        """Clear the footer line."""
        if not self.enable_footer:
            return

        with self.lock:
            if self._has_footer:
                sys.stdout.write(self.CLEAR_LINE + "\r")
                sys.stdout.flush()
                self._has_footer = False
            self.footer_text = ""

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup."""
        self.clear_footer()


class OrderedLogger:
    """
    Logger that buffers messages until explicitly flushed.

    Useful for ensuring initialization messages from concurrent
    processes appear in order instead of being interleaved.
    """

    def __init__(self, prefix: str, terminal: Optional[TerminalDisplay] = None):
        """
        Initialize ordered logger.

        Args:
            prefix: Prefix for all messages
            terminal: Optional terminal display to use
        """
        self.prefix = prefix
        self.terminal = terminal
        self.buffer = []
        self.lock = threading.Lock()

    def log(self, message: str):
        """
        Add a message to the buffer.

        Args:
            message: Message to buffer
        """
        with self.lock:
            self.buffer.append(message)

    def flush(self):
        """Flush all buffered messages to output."""
        with self.lock:
            for msg in self.buffer:
                if self.terminal:
                    self.terminal.print(msg, self.prefix)
                else:
                    print(f"{self.prefix} {msg}")
            self.buffer.clear()

    def print_immediate(self, message: str):
        """
        Print a message immediately without buffering.

        Args:
            message: Message to print
        """
        if self.terminal:
            self.terminal.print(message, self.prefix)
        else:
            print(f"{self.prefix} {message}")


def create_progress_bar(current: int, total: int, width: int = 30) -> str:
    """
    Create a progress bar string.

    Args:
        current: Current progress value
        total: Total/max value
        width: Width of the progress bar in characters

    Returns:
        Progress bar string like: [===========>          ] 50%
    """
    if total == 0:
        percent = 0
    else:
        percent = min(100, int(100 * current / total))

    filled = int(width * current / total) if total > 0 else 0
    filled = min(filled, width)

    bar = "=" * filled + ">" if filled < width else "=" * width
    bar = bar.ljust(width)

    return f"[{bar}] {percent:3d}%"


def format_fps_stats(
    fps: float,
    frame_id: int,
    processing_time_ms: float,
    extra_info: str = ""
) -> str:
    """
    Format FPS and processing stats for footer display.

    Args:
        fps: Frames per second
        frame_id: Current frame ID
        processing_time_ms: Processing time in milliseconds
        extra_info: Additional information to display

    Returns:
        Formatted stats string
    """
    base = f"FPS: {fps:5.1f} | Frame: {frame_id:6d} | Time: {processing_time_ms:6.2f}ms"
    if extra_info:
        base += f" | {extra_info}"
    return base
