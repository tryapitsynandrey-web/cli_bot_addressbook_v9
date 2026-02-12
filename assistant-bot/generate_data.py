import os
import argparse
import random
from datetime import date, timedelta
from typing import List, Set, Dict

from assistant_bot.domain.models import AddressBook, Record
from assistant_bot import storage
from assistant_bot import import_export

# --- Constants ---

COUNT = 400

TAGS_POOL = [
    "work", "friend", "family", "gym", "cigar club", "tennis club", 
    "school mate", "neighbor", "colleague", "vip", "client", 
    "football team", "book club", "gaming buddy"
]

FIRST_NAMES = [
    "John", "Jane", "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Hannah",
    "Ivan", "Jack", "Kathy", "Leo", "Mike", "Nina", "Oscar", "Paul", "Quinn", "Rose",
    "Steve", "Tom", "Uma", "Victor", "Wendy", "Xander", "Yara", "Zack",
    "Liam", "Noah", "Oliver", "Elijah", "James", "William", "Benjamin", "Lucas",
    "Henry", "Alexander", "Mason", "Michael", "Ethan", "Daniel", "Jacob", "Logan",
    "Sophia", "Emma", "Olivia", "Ava", "Isabella", "Mia", "Amelia", "Harper",
    "Evelyn", "Abigail", "Emily", "Ella", "Scarlett", "Victoria", "Aria",
    "Samuel", "Joseph", "Matthew", "Andrew", "Joshua", "Christopher", "Ryan",
    "Nathan", "Aaron", "Caleb", "Dylan", "Isaac", "Julian", "Sebastian"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen",
    "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall",
    "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Gomez",
    "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards"
]

NOTES_LONG = [
    "Enjoys psychological thrillers like Shutter Island and Inception. Big fan of Christopher Nolan.",
    "Favorite color is azure blue. Loves 80s synth-pop, especially Depeche Mode.",
    "Prefers single malt scotch, especially Lagavulin 16. Strong dislike for gin.",
    "Dedicated Beatles fan who listens only on vinyl. Considers Abbey Road their best work.",
    "Passionate about gardening and growing exotic orchids. Maintains a small greenhouse.",
    "Collects vintage cameras from the 1960s, especially Leica models. Practices darkroom development.",
    "Loves Italian cuisine and makes homemade pasta regularly. Enjoys experimenting with recipes.",
    "Avid Stephen King reader and collector. Owns a first edition of The Shining.",
    "Enjoys hiking in the Swiss Alps and has visited Zermatt multiple times.",
    "Passionate about specialty coffee and roasts Ethiopian beans at home."
]

NOTES_SHORT = [
    "Call back later.", "Meeting next week.", " owe him $5.", "Nice guy.", 
    "Met at conference.", "Don't forget birthday.", "Sent invoice.", 
    "Needs updated contract.", "New phone number.", "Discuss project."
]

DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "icloud.com", "ukr.net", "proton.me", "aol.com",
    "live.com", "msn.com", "zoho.com", "mail.com", "yandex.com",
    "pm.me", "tutanota.com", "gmx.com",
    "protonmail.com", "fastmail.com", "hey.com", "inbox.com",
    "orange.fr", "bluewin.ch", "web.de"
]

PREFIXES = [
    "050", "066", "095", "099",
    "067", "068", "096", "097", "098",
    "063", "093", "073",
    "091", "092", "094", "089", "090"
]


# --- Generators ---

def generate_phone() -> str:
    """Generates a random valid phone number."""
    prefix = random.choice(PREFIXES)
    suffix = ''.join(random.choices('0123456789', k=7))
    return f"+38{prefix}{suffix}"


def generate_email(name: str, index: int) -> str:
    """Generates a random email based on name."""
    clean_name = name.lower().replace(" ", ".")
    domain = random.choice(DOMAINS)
    return f"{clean_name}.{index}@{domain}"


def generate_birthday() -> str:
    """Generates a random birthday between 1940 and 2007."""
    start_date = date(1940, 1, 1)
    end_date = date(2007, 12, 31)
    days_range = (end_date - start_date).days
    
    rand_days = random.randint(0, days_range)
    bday = start_date + timedelta(days=rand_days)
    return bday.strftime("%d-%m-%Y")


def generate_address_book(count: int = COUNT) -> AddressBook:
    """Generates a populated AddressBook with random data."""
    book = AddressBook()
    generated_names: Set[str] = set()
    used_phones: Set[str] = set()

    print(f"Generating {count} contacts...")

    for i in range(count):
        # 1. Unique Name Generation
        while True:
            if i < (count // 2): 
                # First 50%: First + Last Name
                fn = random.choice(FIRST_NAMES)
                ln = random.choice(LAST_NAMES)
                candidate = f"{fn} {ln}"
            else:
                # Second 50%: Single Name
                fn = random.choice(FIRST_NAMES)
                candidate = fn
            
            # Handle collisions by appending index
            if candidate in generated_names:
                candidate = f"{candidate} {i}"
            
            if candidate not in generated_names:
                generated_names.add(candidate)
                break
        
        try:
            record = Record(candidate)

            # 2. Unique Phone
            while True:
                phone = generate_phone()
                if phone not in used_phones:
                    used_phones.add(phone)
                    record.add_phone(phone)
                    break

            # 3. Email
            record.add_email(generate_email(candidate, i))

            # 4. Birthday
            record.add_birthday(generate_birthday())

            # 5. Notes (87% chance)
            if i < (count * 0.87):
                # 30% Long, 70% Short
                if random.random() < 0.3:
                    record.add_note(random.choice(NOTES_LONG))
                else:
                    record.add_note(random.choice(NOTES_SHORT))

            # 6. Tags (76% chance)
            if i < (count * 0.76):
                 record.add_tag(random.choice(TAGS_POOL))

            book.add_record(record)

        except ValueError as e:
            print(f"Skipping invalid generation entry for {candidate}: {e}")

    return book


def save_examples(book: AddressBook, output_dir: str) -> None:
    """Saves generated book to the specified directory in all formats."""
    os.makedirs(output_dir, exist_ok=True)
    
    json_path = os.path.join(output_dir, "ex_contacts.json")
    csv_path = os.path.join(output_dir, "ex_contacts.csv")
    pkl_path = os.path.join(output_dir, "ex_contacts.pkl")
    
    print(f"Saving examples to {output_dir}...")
    
    storage.save_address_book(book, json_path)
    print(f"Created {json_path}")
    
    import_export.export_file(book, csv_path)
    print(f"Created {csv_path}")
    
    storage.save_pickle(book, pkl_path)
    print(f"Created {pkl_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate random contact data.")
    parser.add_argument("--output", help="Output directory for files", default="test_addressbook")
    parser.add_argument("--count", type=int, default=COUNT, help="Number of contacts to generate")
    
    args = parser.parse_args()
    
    book = generate_address_book(args.count)
    save_examples(book, args.output)
    print("Done.")


if __name__ == "__main__":
    main()
