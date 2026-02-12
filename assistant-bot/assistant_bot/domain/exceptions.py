class BotException(Exception):
    """Base exception for the application."""
    pass


class ValidationError(BotException):
    """Raised when data validation fails (e.g., invalid phone format)."""
    pass


class ContactNotFound(BotException):
    """Raised when a requested contact does not exist."""
    pass


class DuplicateContact(BotException):
    """Raised when trying to add a contact that already exists."""
    pass


class PhoneNotFound(BotException):
    """Raised when a specific phone number is not found for a contact."""
    pass


class DuplicatePhone(BotException):
    """Raised when a phone number already exists globally or for a contact."""
    pass


class DuplicateEmail(BotException):
    """Raised when an email already exists globally."""
    pass


class NoteNotFound(BotException):
    """Raised when a note index is invalid."""
    pass
