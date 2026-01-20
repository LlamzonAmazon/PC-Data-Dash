"""
Terminal output utilities for consistent, structured logging across modules.
Provides standardized formatting for module headers, progress bars, and summaries.
"""

from typing import Optional
import sys


class TerminalOutput:
    """Utility class for consistent terminal output formatting."""
    
    @staticmethod
    def module_header(module: str, source: str) -> None:
        """
        Print a module header.
        
        Args:
            module: Module name (e.g., 'FETCH', 'CLEAN')
            source: Data source name (e.g., 'UN SDG', 'World Bank', 'ND-GAIN')
        """
        print(f"\n[{module}] {source}")
    
    @staticmethod
    def progress_bar(current: int, total: int, width: int = 30, prefix: str = "") -> str:
        """
        Generate a horizontal progress bar string.
        
        Args:
            current: Current progress value
            total: Total value
            width: Width of the progress bar in characters
            prefix: Optional prefix text
            
        Returns:
            Formatted progress bar string
        """
        if total == 0:
            percent = 100
        else:
            percent = int((current / total) * 100)
        
        filled = int((current / total) * width) if total > 0 else width
        bar = '=' * filled + '>' + ' ' * (width - filled - 1)
        
        return f"{prefix}[{bar}] {percent}% ({current}/{total})"
    
    @staticmethod
    def print_progress(current: int, total: int, width: int = 30, prefix: str = "") -> None:
        """
        Print a progress bar that overwrites the same line.
        
        Args:
            current: Current progress value
            total: Total value
            width: Width of the progress bar in characters
            prefix: Optional prefix text
        """
        bar = TerminalOutput.progress_bar(current, total, width, prefix)
        print(f"\r{bar}", end='', flush=True)
        
        # Print newline when complete
        if current >= total:
            print()
    
    @staticmethod
    def info(message: str, indent: int = 0) -> None:
        """
        Print an info message with optional indentation.
        
        Args:
            message: Message to print
            indent: Number of spaces to indent
        """
        print(f"{'  ' * indent}{message}")
    
    @staticmethod
    def summary(label: str, value: any, indent: int = 0) -> None:
        """
        Print a summary line with label and value.
        
        Args:
            label: Summary label
            value: Summary value
            indent: Number of spaces to indent
        """
        print(f"{'  ' * indent}{label}: {value}")
    
    @staticmethod
    def separator() -> None:
        """Print a separator line."""
        print("-" * 60)
    
    @staticmethod
    def complete(message: str = "Complete") -> None:
        """
        Print a completion message.
        
        Args:
            message: Completion message
        """
        print(f"  {message}")


# Convenience functions for common operations
def fetch_header(source: str) -> None:
    """Print a fetch module header."""
    TerminalOutput.module_header("FETCH", source)


def clean_header(source: str) -> None:
    """Print a clean module header."""
    TerminalOutput.module_header("CLEAN", source)
