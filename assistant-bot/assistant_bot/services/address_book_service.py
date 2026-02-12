from typing import List, Dict, Any, Optional, Set

from assistant_bot.domain.models import AddressBook, Record
from assistant_bot.domain.exceptions import (
    ContactNotFound,
    DuplicatePhone,
    DuplicateEmail,
    ValidationError
)

class AddressBookService:
    def __init__(self, book: AddressBook):
        self.book = book

    # --- Helpers ---

    def _check_phone_unique(self, phone: str, exclude_contact_name: Optional[str] = None) -> None:
        """
        idempotent check: raises DuplicatePhone if phone exists in ANY record (except exclude_contact_name).
        """
        from assistant_bot.domain.models import Phone
        norm_phone = Phone._normalize(phone)

        for name, record in self.book.data.items():
            if exclude_contact_name and name == exclude_contact_name:
                continue
            for p in record.phones:
                if p.value == norm_phone:
                     raise DuplicatePhone(f"Phone number {phone} already belongs to {name}.")

    def _check_email_unique(self, email: str, exclude_contact_name: Optional[str] = None) -> None:
        for name, record in self.book.data.items():
            if exclude_contact_name and name == exclude_contact_name:
                continue
            if record.email and record.email.value == email:
                raise DuplicateEmail(f"Email {email} already belongs to {name}.")

    # --- Contact Management ---

    def add_contact(self, name: str, phone: Optional[str] = None, email: Optional[str] = None, birthday: Optional[str] = None) -> List[str]:
        """
        Adds a new contact. If the contact exists, it attempts to update fields.
        Returns a list of actions performed (e.g. ['created', 'phone added']).
        """
        status = []
        record = self.book.find(name)
        
        if not record:
            record = Record(name)
            self.book.add_record(record)
            status.append("Contact created")
        
        if phone:
            self._check_phone_unique(phone, name)
            if not record.find_phone(phone):
                record.add_phone(phone)
                status.append("Phone added")
        
        if email:
            self._check_email_unique(email, name)
            if not record.email or record.email.value != email:
                record.add_email(email)
                status.append("Email added")

        if birthday:
            record.add_birthday(birthday)
            status.append("Birthday added")

        return status

    def change_phone(self, name: str, old_phone: str, new_phone: str) -> None:
        record = self.book.find(name)
        if not record:
            raise ContactNotFound(f"Contact {name} not found.")
        
        # Check if new phone is unique globally
        self._check_phone_unique(new_phone, name)
        
        record.edit_phone(old_phone, new_phone)

    def add_phone_to_contact(self, name: str, phone: str) -> None:
        record = self.book.find(name)
        if not record:
            raise ContactNotFound(f"Contact {name} not found.")
        
        self._check_phone_unique(phone, name)
        
        if record.find_phone(phone):
             raise DuplicatePhone(f"Phone {phone} already exists for {name}.")
             
        record.add_phone(phone)

    def delete_contact(self, name: str) -> None:
        if not self.book.delete(name):
            pass

    def get_contact(self, name: str) -> Record:
        record = self.book.find(name)
        if not record:
             raise ContactNotFound(f"Contact {name} not found.")
        return record

    def get_all_contacts(self) -> List[Record]:
        return list(self.book.data.values())

    # --- Search ---

    def search_contacts(self, query: str) -> List[Record]:
        query = query.lower()
        results = []
        for record in self.book.data.values():
            if query in record.name.value.lower():
                results.append(record)
                continue
            
            # Phones
            if any(query in p.value for p in record.phones):
                results.append(record)
                continue
                
            # Email
            if record.email and query in record.email.value.lower():
                results.append(record)
                
        return results

    # --- Email & Birthday ---

    def add_email(self, name: str, email: str) -> None:
        record = self.book.find(name)
        if not record:
            raise ContactNotFound(f"Contact {name} not found.")
            
        self._check_email_unique(email, name)
        record.add_email(email)

    def add_birthday(self, name: str, birthday: str) -> None:
        record = self.book.find(name)
        if not record:
            raise ContactNotFound(f"Contact {name} not found.")
        record.add_birthday(birthday)

    def get_days_to_birthday(self, name: str) -> int:
        record = self.book.find(name)
        if not record:
            raise ContactNotFound(f"Contact {name} not found.")
            
        days = record.days_to_birthday()
        if days is None:
            raise ValidationError(f"No birthday set for {name}.")
        return days

    def get_upcoming_birthdays(self, days: int) -> List[Dict[str, Any]]:
        return self.book.get_upcoming_birthdays(days)

    # --- Notes ---

    def add_note(self, name: str, note_text: str) -> None:
        record = self.book.find(name)
        if not record:
             raise ContactNotFound(f"Contact {name} not found.")
        record.add_note(note_text)

    def edit_note(self, name: str, index: int, new_text: str) -> None:
        record = self.book.find(name)
        if not record:
             raise ContactNotFound(f"Contact {name} not found.")
        record.edit_note(index, new_text)

    def delete_note(self, name: str, index: int) -> None:
        record = self.book.find(name)
        if not record:
             raise ContactNotFound(f"Contact {name} not found.")
        record.remove_note(index)

    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """
        Returns structure: [{'contact': name, 'note_index': i, 'note': text}]
        """
        query = query.lower()
        results = []
        for name, record in self.book.data.items():
            for i, note in enumerate(record.notes):
                if query in note.lower():
                    results.append({
                        "contact": name,
                        "note_index": i,
                        "note": note
                    })
        return results
        
    def get_notes(self, name: Optional[str] = None) -> Dict[str, List[str]]:
        if name:
            record = self.book.find(name)
            if not record:
                raise ContactNotFound(f"Contact {name} not found.")
            return {name: record.notes}
        else:
             return {n: r.notes for n, r in self.book.data.items() if r.notes}

    # --- Tags ---

    def add_tag(self, name: str, tag: str) -> None:
        record = self.book.find(name)
        if not record:
             raise ContactNotFound(f"Contact {name} not found.")
        record.add_tag(tag)

    def remove_tag(self, name: str, tag: str) -> None:
        record = self.book.find(name)
        if not record:
             raise ContactNotFound(f"Contact {name} not found.")
        record.remove_tag(tag)

    def get_all_tags(self) -> Dict[str, List[str]]:
        return self.book.get_all_tags()

    def get_unique_tags(self) -> Any:
        return self.book.get_unique_tags()

    def filter_by_tag(self, tag: str) -> List[Record]:
        names = self.book.find_by_tag(tag)
        return [self.book.find(n) for n in names if self.book.find(n)]

    # --- Bulk Ops ---
    
    def delete_all(self) -> None:
        self.book.data.clear()
