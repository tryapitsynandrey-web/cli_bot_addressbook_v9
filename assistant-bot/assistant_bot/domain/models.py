import re
from collections import UserDict
from datetime import datetime, date
from typing import Optional, List, Any, Dict, Set

from assistant_bot.domain.exceptions import (
    ValidationError, 
    ContactNotFound, 
    PhoneNotFound,
    NoteNotFound
)

# Validation patterns
PHONE_VALIDATION_PATTERN = r'^\+38\d{10}$'
EMAIL_VALIDATION_PATTERN = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'


class Field:
    """Base class for record fields."""
    def __init__(self, value: Any):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    """Class for storing contact name. Mandatory field."""
    def __init__(self, value: str):
        if not value:
            raise ValidationError("Name cannot be empty.")
        super().__init__(value)


class Phone(Field):
    """Class for storing phone number. Validates format."""
    def __init__(self, value: str):
        normalized = self._normalize(value)
        if not self._validate(normalized):
            raise ValidationError(f"Invalid phone number: {value}. Use format +380.........")
        super().__init__(normalized)

    @staticmethod
    def _normalize(phone: str) -> str:
        if not phone:
            return ''
        digits = re.sub(r"\D", "", phone)
        if len(digits) == 10:
            return f"+38{digits}"
        if len(digits) == 12:
            return f"+{digits}"
        return f"+{digits}"

    @staticmethod
    def _validate(normalized_phone: str) -> bool:
        return bool(re.match(PHONE_VALIDATION_PATTERN, normalized_phone))


class Email(Field):
    """Class for storing email address. Validates format."""
    def __init__(self, value: str):
        if not self._validate(value):
            raise ValidationError(f"Invalid email format: {value}")
        super().__init__(value)

    @staticmethod
    def _validate(email: str) -> bool:
        return bool(re.match(EMAIL_VALIDATION_PATTERN, email))


class Birthday(Field):
    """Class for storing birthday. Validates format DD-MM-YYYY."""
    def __init__(self, value: str):
        try:
            self.date_obj = datetime.strptime(value, "%d-%m-%Y").date()
        except ValueError:
            raise ValidationError(f"Invalid date format: {value}. Use DD-MM-YYYY")
        super().__init__(value)


class Record:
    """
    Class for storing contact information.
    Enforces strict encapsulation to prevent mutation hazards.
    """
    def __init__(self, name: str):
        self.name = Name(name)
        self._phones: List[Phone] = []
        self.email: Optional[Email] = None
        self.birthday: Optional[Birthday] = None
        self._notes: List[str] = []
        self._tags: List[str] = []

    @property
    def phones(self) -> List[Phone]:
        return self._phones[:]

    @property
    def notes(self) -> List[str]:
        return self._notes[:]

    @property
    def tags(self) -> List[str]:
        return self._tags[:]

    # --- Phone Management ---

    def add_phone(self, phone: str) -> None:
        if self.find_phone(phone):
            return 
        
        new_phone_obj = Phone(phone)
        if any(p.value == new_phone_obj.value for p in self._phones):
             raise ValidationError(f"Phone {phone} already exists for this contact.")
        
        self._phones.append(new_phone_obj)

    def remove_phone(self, phone: str) -> None:
        norm_phone = Phone._normalize(phone)
        initial_len = len(self._phones)
        self._phones = [p for p in self._phones if p.value != norm_phone]
        if len(self._phones) == initial_len:
            raise PhoneNotFound(f"Phone {phone} not found.")

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        norm_old = Phone._normalize(old_phone)
        for i, phone in enumerate(self._phones):
            if phone.value == norm_old:
                self._phones[i] = Phone(new_phone)
                return
        raise PhoneNotFound(f"Phone {old_phone} not found.")

    def find_phone(self, phone: str) -> Optional[Phone]:
        norm_phone = Phone._normalize(phone)
        for p in self._phones:
            if p.value == norm_phone:
                return p
        return None

    # --- Email & Birthday ---

    def add_email(self, email: str) -> None:
        self.email = Email(email)

    def add_birthday(self, birthday: str) -> None:
        self.birthday = Birthday(birthday)

    def days_to_birthday(self, today: Optional[date] = None) -> Optional[int]:
        if not self.birthday:
            return None
        
        if today is None:
            today = date.today()

        bdate = self.birthday.date_obj
        try:
            this_year_bday = bdate.replace(year=today.year)
        except ValueError:
            # Handle leap year case: Feb 29 -> Feb 28 or Mar 1
            this_year_bday = bdate.replace(year=today.year, day=bdate.day - 1)

        if this_year_bday < today:
            try:
                this_year_bday = bdate.replace(year=today.year + 1)
            except ValueError:
                this_year_bday = bdate.replace(year=today.year + 1, day=bdate.day - 1)
            
        return (this_year_bday - today).days

    # --- Notes ---

    def add_note(self, note: str) -> None:
        if note:
             self._notes.append(note)

    def edit_note(self, index: int, new_note: str) -> None:
        if 0 <= index < len(self._notes):
            self._notes[index] = new_note
        else:
            raise NoteNotFound("Note index out of range")

    def remove_note(self, index: int) -> None:
        if 0 <= index < len(self._notes):
            self._notes.pop(index)
        else:
            raise NoteNotFound("Note index out of range")

    # --- Tags ---

    def add_tag(self, tag: str) -> None:
        tag = self._normalize_tag(tag)
        if tag and tag not in self._tags:
            self._tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        tag = self._normalize_tag(tag)
        if tag in self._tags:
            self._tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        return self._normalize_tag(tag) in self._tags

    @staticmethod
    def _normalize_tag(tag: str) -> str:
        return tag.strip().casefold()

    def __str__(self) -> str:
        phones_str = '; '.join(p.value for p in self._phones)
        return f"Contact name: {self.name.value}, phones: {phones_str}"


class AddressBook(UserDict):
    """Class for storing and managing records."""
    
    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        return self.data.get(name)

    def delete(self, name: str) -> bool:
        if name in self.data:
            del self.data[name]
            return True
        raise ContactNotFound(f"Contact {name} not found.")

    def get_upcoming_birthdays(self, days: int = 7) -> List[Dict[str, Any]]:
        upcoming = []
        today = date.today()
        
        for record in self.data.values():
            if not record.birthday:
                continue

            days_until = record.days_to_birthday(today)
            
            if days_until is not None and 0 <= days_until <= days:
                upcoming.append({
                    "name": record.name.value,
                    "birthday": record.birthday.value,
                    "days_until": days_until
                })
                
        return sorted(upcoming, key=lambda x: x['days_until'])

    def find_by_tag(self, tag: str) -> List[str]:
        return [record.name.value for record in self.data.values() if record.has_tag(tag)]
        
    def get_all_tags(self) -> Dict[str, List[str]]:
        return {name: r.tags for name, r in self.data.items() if r.tags}

    def get_unique_tags(self) -> Set[str]:
        unique_tags = set()
        for record in self.data.values():
            unique_tags.update(record.tags)
        return unique_tags
