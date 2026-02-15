import random
from typing import Dict, Tuple, Any

from rich.console import Console
from rich.theme import Theme

# --- Configuration ---
# Custom theme for consistent, professional branding
THEME_CONFIG = {
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "header": "bold magenta",
    "highlight": "bold white"
}

custom_theme = Theme(THEME_CONFIG)
console = Console(theme=custom_theme)


# --- Output Helpers ---

def print_error(msg: str) -> None:
    """Displays an error message with a cross icon."""
    console.print(f"[error]❌ {msg}[/error]")


def print_success(msg: str) -> None:
    """Displays a success message with a checkmark icon."""
    console.print(f"[success]✅ {msg}[/success]")


def print_info(msg: str) -> None:
    """Displays an informational message with an info icon."""
    console.print(f"[info]ℹ️  {msg}[/info]")


def print_warning(msg: str) -> None:
    """Displays a warning message with a warning icon."""
    console.print(f"[warning]⚠️  {msg}[/warning]")


def print_duplicate_error(owner_name: str, owner_data: Dict[str, Any], value: str, messages: Tuple[str, ...]) -> None:
    """
    Prints a gamified duplicate error message.

    Args:
        owner_name: Name of the contact owning the duplicate data.
        owner_data: Dictionary of data (unused but kept for interface consistency).
        value: The conflicting value (email or phone).
        messages: A tuple of potential error messages to choose from.
    """
    msg = random.choice(messages)

    try:
        # We provide common context variables for formatting
        formatted_msg = msg.format(name=owner_name, email=value, phone=value)
    except (IndexError, KeyError, ValueError):
        # Fallback to raw message if placeholder mismatch occurs
        formatted_msg = msg

    console.print(f"[error]❌ {formatted_msg}[/error] (Owned by: [bold]{owner_name}[/bold])")
