import json
import csv
from typing import Dict, Any, List

from assistant_bot.domain.models import Record, AddressBook
from assistant_bot.domain.exceptions import ValidationError

# Constants
CSV_HEADERS = ['name', 'phones', 'email', 'birthday', 'notes', 'tags']
CSV_DELIMITERS = {
    'phones': '|',
    'notes': ' ; ',
    'tags': ','
}


def export_file(address_book: AddressBook, path: str) -> None:
    """Exports AddressBook data to a file (JSON or CSV)."""
    if not path:
        raise ValueError('Path required')
    
    extension = path.lower().split('.')[-1]
    
    if extension == 'json':
        _export_json(address_book, path)
    elif extension == 'csv':
        _export_csv(address_book, path)
    else:
        raise ValueError('Unsupported export format')


def import_file(address_book: AddressBook, path: str) -> None:
    """Imports data from a file (JSON or CSV) into AddressBook."""
    if not path:
        raise ValueError('Path required')
    
    extension = path.lower().split('.')[-1]
    
    if extension == 'json':
        _import_json(address_book, path)
    elif extension == 'csv':
        _import_csv(address_book, path)
    else:
        raise ValueError('Unsupported import format')


# --- Internal Helpers ---

def _prepare_export_data(address_book: AddressBook) -> Dict[str, Any]:
    """Converts AddressBook to a serializable dictionary."""
    export_data = {}
    for name, record in address_book.data.items():
        export_data[name] = {
            "phones": [p.value for p in record.phones],
            "email": record.email.value if record.email else "",
            "birthday": record.birthday.value if record.birthday else "",
            "notes": record.notes,
            "tags": record.tags
        }
    return export_data


def _export_json(address_book: AddressBook, path: str) -> None:
    """Writes data to a JSON file."""
    data = _prepare_export_data(address_book)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _export_csv(address_book: AddressBook, path: str) -> None:
    """Writes data to a CSV file."""
    data = _prepare_export_data(address_book)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        
        for name, entry in data.items():
            phones = CSV_DELIMITERS['phones'].join(entry['phones'])
            notes = CSV_DELIMITERS['notes'].join(entry['notes'])
            tags = CSV_DELIMITERS['tags'].join(entry['tags'])
            
            writer.writerow([
                name,
                phones,
                entry['email'],
                entry['birthday'],
                notes,
                tags
            ])


def _import_json(address_book: AddressBook, path: str) -> None:
    """Reads data from a JSON file and populates AddressBook."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for name, entry in data.items():
        if isinstance(entry, dict):
            _create_record_from_entry(address_book, name, entry)


def _import_csv(address_book: AddressBook, path: str) -> None:
    """Reads data from a CSV file and populates AddressBook."""
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('name')
            if not name:
                continue
            
            # Helper to split fields safely
            def split_field(key: str, delimiter: str) -> List[str]:
                val = row.get(key, '')
                return [item for item in val.split(delimiter) if item] if val else []

            entry = {
                'phones': split_field('phones', CSV_DELIMITERS['phones']),
                'email': row.get('email', ''),
                'birthday': row.get('birthday', ''),
                'notes': split_field('notes', CSV_DELIMITERS['notes']),
                'tags': split_field('tags', CSV_DELIMITERS['tags'])
            }
            
            _create_record_from_entry(address_book, name, entry)


def _create_record_from_entry(address_book: AddressBook, name: str, entry: Dict[str, Any]) -> None:
    """Helper to create and add a Record from a data dictionary."""
    try:
        record = Record(name)
        
        for phone in entry.get('phones', []):
            record.add_phone(str(phone))
            
        email = entry.get('email')
        if email:
            record.add_email(str(email))
            
        birthday = entry.get('birthday')
        if birthday:
            record.add_birthday(str(birthday))
            
        for note in entry.get('notes', []):
            record.add_note(str(note))
            
        for tag in entry.get('tags', []):
            record.add_tag(str(tag))
            
        address_book.add_record(record)
    except (ValueError, ValidationError):
        # Skip invalid records (standard behavior akin to storage loading)
        pass


__all__ = ['export_file', 'import_file']
