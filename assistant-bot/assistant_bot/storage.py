import os
import json
import pickle
from typing import Optional, Dict, Any, List

from assistant_bot.config import (
    JSON_STORAGE_PATH,
    CSV_STORAGE_PATH,
    PICKLE_STORAGE_PATH,
    DATA_DIR
)
from assistant_bot.domain.models import AddressBook, Record
from assistant_bot.domain.exceptions import ValidationError
from assistant_bot.ui.console import print_info
from assistant_bot.import_export import export_file

__all__ = [
    "load_address_book",
    "save_address_book",
    "load_pickle",
    "save_pickle",
    "save_all"
]


def load_address_book() -> AddressBook:
    """
    Loads data from JSON storage.
    Handles migration from legacy dict-based format to OOP Record format.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    book = AddressBook()
    
    if not os.path.exists(JSON_STORAGE_PATH):
        return book

    try:
        with open(JSON_STORAGE_PATH, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        if isinstance(raw_data, dict):
            for name, data in raw_data.items():
                if not isinstance(data, dict):
                    continue

                try:
                    record = Record(name)

                    # Phones
                    for p in data.get('phones', []):
                        record.add_phone(p)

                    # Email
                    email = data.get('email')
                    if email:
                        record.add_email(email)

                    # Birthday
                    bday = data.get('birthday')
                    if bday:
                        record.add_birthday(bday)

                    # Notes
                    notes = data.get('notes', [])
                    for n in notes:
                        record.add_note(n)

                    # Tags
                    tags = data.get('tags', [])
                    for t in tags:
                        record.add_tag(t)

                    book.add_record(record)
                except (ValueError, ValidationError) as e:
                    print(f"Skipping invalid record '{name}': {e}")

    except Exception as e:
        print_info(f"Warning: Failed to load data or starting fresh: {e}")
            
    return book


def save_address_book(book: AddressBook, path: str = JSON_STORAGE_PATH) -> None:
    """
    Saves AddressBook to JSON storage.
    Serializes Record objects to dictionaries.
    """
    if path != JSON_STORAGE_PATH:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    else:
        os.makedirs(DATA_DIR, exist_ok=True)
    
    save_data = {}
    
    for name, record in book.data.items():
        record_data = {
            "phones": [p.value for p in record.phones],
            "email": record.email.value if record.email else None,
            "birthday": record.birthday.value if record.birthday else None,
            "notes": record.notes,
            "tags": record.tags
        }
        save_data[name] = record_data
        
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")


def load_pickle() -> Optional[AddressBook]:
    """
    Loads AddressBook from pickle file.
    Returns AddressBook or None if failed/missing.
    """
    if not os.path.exists(PICKLE_STORAGE_PATH):
        return None

    try:
        with open(PICKLE_STORAGE_PATH, 'rb') as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError, ModuleNotFoundError, AttributeError) as e:
        print(f"Warning: Failed to load pickle (starting fresh/legacy): {e}")
        return None


def save_pickle(book: AddressBook, path: str = PICKLE_STORAGE_PATH) -> None:
    """
    Saves AddressBook to pickle file.
    """
    if path != PICKLE_STORAGE_PATH:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        with open(path, 'wb') as f:
            pickle.dump(book, f)
    except Exception as e:
        print(f"Error saving pickle data: {e}")


def save_all(book: AddressBook) -> None:
    """
    Strictly synchronizes AddressBook state across all formats:
    - JSON (Legacy/Human Readable)
    - PKL (Persistence)
    - CSV (Export/Backup)
    """
    # 1. Save JSON
    save_address_book(book)

    # 2. Save Pickle
    save_pickle(book)

    # 3. Save CSV
    try:
        export_file(book, CSV_STORAGE_PATH)
    except Exception as e:
        print(f"Error syncing CSV: {e}")
