import shlex
import random
from functools import wraps
from typing import Callable, List, Dict, Optional, Tuple, Any

from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.align import Align

from assistant_bot.config import DEFAULT_BIRTHDAY_LOOKAHEAD_DAYS
from assistant_bot.domain.models import Record
from assistant_bot.domain.exceptions import BotException, ValidationError
from assistant_bot.services.address_book_service import AddressBookService
from assistant_bot.ui.console import (
    console, print_error, print_success, print_info
)
from assistant_bot.import_export import import_file, export_file

from assistant_bot.utils import ux_messages as messages

# --- MESSAGES GROUPS ---
CMD_ERRORS = {
    "unknown": messages.UNKNOWN_COMMAND_MESSAGES,
    "missing_args": messages.MISSING_ARGS_MESSAGES,
}

CONTACT_MESSAGES = {
    "added": messages.CONTACT_ADDED_MESSAGES,
    "updated": messages.CONTACT_UPDATED_MESSAGES,
    "deleted": messages.CONTACT_DELETED_MESSAGES,
}

PHONE_MESSAGES = {
    "added": messages.PHONE_ADDED_MESSAGES,
    "updated": messages.PHONE_UPDATED_MESSAGES,
}

EMAIL_MESSAGES = {
    "updated": messages.EMAIL_UPDATED_MESSAGES,
}

BIRTHDAY_MESSAGES = {
    "updated": messages.BIRTHDAY_UPDATED_MESSAGES,
}

NOTE_MESSAGES = {
    "added": messages.NOTE_ADDED_MESSAGES,
    "updated": messages.NOTE_UPDATED_MESSAGES,
    "deleted": messages.NOTE_DELETED_MESSAGES,
}

TAG_MESSAGES = {
    "added": messages.TAG_ADDED_MESSAGES,
    "removed": messages.TAG_REMOVED_MESSAGES,
}

SYSTEM_MESSAGES = {
    "import_success": messages.IMPORT_SUCCESS_MESSAGES,
    "export_success": messages.EXPORT_SUCCESS_MESSAGES,
    "delete_all": messages.DELETE_ALL_MESSAGES,
}


# --- COMMAND REGISTRY ---
COMMAND_REGISTRY: Dict[str, Tuple[Callable[..., Any], str]] = {}


def command(name: str, help_text: str = "") -> Callable:
    """Decorator to register a bot command."""
    def decorator(func: Callable) -> Callable:
        COMMAND_REGISTRY[name] = (func, help_text)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# --- COMMAND HANDLERS ---

@command("help", "Show available commands")
def handle_help(service: AddressBookService, args: List[str]) -> None:
    """Displays commands grouped by category."""
    
    categories = {
        "📇 Contact Management": [
            "add", "all", "change", "add_phone", "phone", "delete", 
            "add_email", "add_birthday", "birthdays", "days_to_bday", 
            "search", "list"
        ],
        "📝 Notes": [
            "add_note", "edit_note", "delete_note", "search_notes", "list_notes"
        ],
        "🏷️ Tags": [
            "add_tag", "remove_tag", "list_tags", "filter_by_tag"
        ],
        "💾 System & Data": [
            "import", "export", "delete_all", "help", "exit", "close"
        ]
    }

    console.print(Align.center(Panel(
        "🤖 [bold magenta]Assistant Bot Help Menu[/bold magenta]", 
        border_style="magenta",
        subtitle="[dim]Type a command to proceed[/dim]",
        width=90,
        box=box.ROUNDED
    )))

    for category, cmds in categories.items():
        table = Table(
            title=category, 
            title_style="bold cyan", 
            show_header=True, 
            header_style="bold white", 
            box=box.ROUNDED,
            width=90,
            show_lines=True,
            border_style="bright_blue"
        )
        table.add_column("Command", style="cyan", width=35)
        table.add_column("Description", style="white")
        
        has_rows = False
        for name in cmds:
            if name in COMMAND_REGISTRY:
                _, help_text = COMMAND_REGISTRY[name]
                table.add_row(name, help_text)
                has_rows = True
        
        if has_rows:
            console.print(Align.center(table))
            console.print()


# --- CONTACT MANAGEMENT ---

@command("add", "Add contact: add <name> [phone] [email] [birthday]")
def handle_add(service: AddressBookService, args: List[str]) -> None:
    if not args:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="add <name> [phone] [email] [birthday]"))
        return
    
    name = args[0]
    phone = args[1] if len(args) > 1 else None
    email = args[2] if len(args) > 2 else None
    birthday = args[3] if len(args) > 3 else None

    # Service call
    try:
        status = service.add_contact(name, phone, email, birthday)
        
        if "Contact created" in status:
             print_success(random.choice(CONTACT_MESSAGES["added"]).format(name=name))
        elif status:
             msg = random.choice(CONTACT_MESSAGES["updated"]).format(name=name)
             print_success(f"{msg} (Changed: {', '.join(status)})")
        else:
             print_info(f"Contact '{name}' already up to date.")
             
    except BotException as e:
        print_error(str(e))


@command("change", "Change phone: change <name> <old_phone> <new_phone>")
def handle_change(service: AddressBookService, args: List[str]) -> None:
    if len(args) < 3:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="change <name> <old_phone> <new_phone>"))
        return
    
    name, old_phone, new_phone = args[0], args[1], args[2]
    
    try:
        service.change_phone(name, old_phone, new_phone)
        print_success(random.choice(PHONE_MESSAGES["updated"]).format(name=name))
    except BotException as e:
        print_error(str(e))


@command("add_phone", "Add extra phone: add_phone <name> <phone>")
def handle_add_phone(service: AddressBookService, args: List[str]) -> None:
    if len(args) < 2:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="add_phone <name> <phone>"))
        return
    
    name, phone = args[0], args[1]
    
    try:
        service.add_phone_to_contact(name, phone)
        print_success(random.choice(PHONE_MESSAGES["added"]).format(name=name))
    except BotException as e:
        print_error(str(e))


@command("delete", "Delete contact: delete <name>")
def handle_delete(service: AddressBookService, args: List[str]) -> None:
    if not args:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="delete <name>"))
        return
    
    name = args[0]
    try:
        service.delete_contact(name)
        print_success(random.choice(CONTACT_MESSAGES["deleted"]).format(name=name))
    except BotException as e:
        print_error(str(e))


@command("search", "Search contacts: search <query>")
def handle_search(service: AddressBookService, args: List[str]) -> None:
    if not args:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="search <query>"))
        return
    
    query = args[0]
    results = service.search_contacts(query)
    
    if not results:
        print_info(f"No contacts found matching '{query}'")
        return
        
    _print_contacts_table(results)


@command("phone", "Show phones: phone <name>")
def handle_phone(service: AddressBookService, args: List[str]) -> None:
    if not args:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="phone <name>"))
        return
    
    name = args[0]
    try:
        record = service.get_contact(name)
        phones = [p.value for p in record.phones]
        console.print(f"[bold]{name}[/bold]: {', '.join(phones) if phones else 'No phones'}")
    except BotException as e:
        print_error(str(e))


@command("add_email", "Add/Edit email: add_email <name> <email>")
def handle_add_email(service: AddressBookService, args: List[str]) -> None:
    if len(args) < 2:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="add_email <name> <email>"))
        return
    
    name, email = args[0], args[1]
    
    try:
        service.add_email(name, email)
        print_success(random.choice(EMAIL_MESSAGES["updated"]).format(name=name))
    except BotException as e:
        print_error(str(e))


@command("add_birthday", "Add/Edit birthday: add_birthday <name> <DD-MM-YYYY>")
def handle_add_birthday(service: AddressBookService, args: List[str]) -> None:
    if len(args) < 2:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="add_birthday <name> <date>"))
        return
    
    name, bday = args[0], args[1]
    
    try:
        service.add_birthday(name, bday)
        print_success(random.choice(BIRTHDAY_MESSAGES["updated"]).format(name=name))
    except BotException as e:
        print_error(str(e))


@command("all", "Show all contact info")
def handle_all(service: AddressBookService, args: List[str]) -> None:
    records = service.get_all_contacts()
    if not records:
        print_info("No contacts found.")
        return

    table = Table(title="All Contacts Details")
    table.add_column("Full Name", style="cyan")
    table.add_column("Phone", style="green")
    table.add_column("Email", style="blue")
    table.add_column("Birthday", style="yellow")
    table.add_column("Days to B-day", style="magenta")
    table.add_column("Note", style="white")
    table.add_column("Tag", style="red")

    for record in records:
        phones = ", ".join(p.value for p in record.phones)
        email = record.email.value if record.email else "-"
        bday_str = record.birthday.value if record.birthday else "-"
        
        days_until = "-"
        if record.birthday:
            d = record.days_to_birthday()
            if d is not None:
                days_until = str(d)
        
        note_str = "\n".join(record.notes) if record.notes else "-"
        tag_str = ", ".join(record.tags) if record.tags else "-"
        
        table.add_row(record.name.value, phones, email, bday_str, days_until, note_str, tag_str)
    
    console.print(Align.center(table))


@command("list", "List all contacts")
def handle_list(service: AddressBookService, args: List[str]) -> None:
    records = service.get_all_contacts()
    if not records:
        print_info("No contacts found.")
        return
    _print_contacts_table(records)


def _print_contacts_table(records: List[Record]) -> None:
    table = Table(title="Contacts List")
    table.add_column("Name", style="cyan")
    table.add_column("Phones", style="green")
    table.add_column("Email", style="blue")
    table.add_column("Birthday", style="yellow")

    for record in records:
        phones = ", ".join(p.value for p in record.phones)
        email = record.email.value if record.email else "-"
        birthday = record.birthday.value if record.birthday else "-"
        table.add_row(record.name.value, phones, email, birthday)
    
    console.print(table)


# --- NOTES MANAGEMENT ---

@command("add_note", "Add note: add_note <name> <text>")
def handle_add_note(service: AddressBookService, args: List[str]) -> None:
    if len(args) < 2:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="add_note <name> <text>"))
        return
    
    name = args[0]
    note = " ".join(args[1:])
    try:
        service.add_note(name, note)
        print_success(random.choice(NOTE_MESSAGES["added"]).format(name=name))
    except BotException as e:
        print_error(str(e))


@command("edit_note", "Edit note: edit_note <name> <index> <new_text>")
def handle_edit_note(service: AddressBookService, args: List[str]) -> None:
    if len(args) < 3:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="edit_note <name> <index> <new_text>"))
        return
    
    name = args[0]
    try:
        index = int(args[1]) - 1
        new_text = " ".join(args[2:])
        service.edit_note(name, index, new_text)
        print_success(random.choice(NOTE_MESSAGES["updated"]).format(name=name))
    except (ValueError, BotException) as e:
        if isinstance(e, ValueError):
            print_error("Index must be a number.")
        else:
            print_error(str(e))


@command("delete_note", "Delete note: delete_note <name> <index>")
def handle_delete_note(service: AddressBookService, args: List[str]) -> None:
    if len(args) < 2:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="delete_note <name> <index>"))
        return
    
    name, index_str = args[0], args[1]
    try:
        index = int(index_str) - 1
        service.delete_note(name, index)
        print_success(random.choice(NOTE_MESSAGES["deleted"]).format(name=name))
    except ValueError:
        print_error("Index must be a number.")
    except BotException as e:
        print_error(str(e))


@command("search_notes", "Search notes: search_notes <query>")
def handle_search_notes(service: AddressBookService, args: List[str]) -> None:
    if not args:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="search_notes <query>"))
        return
    
    query = args[0]
    results = service.search_notes(query)
    # Results is list of dicts
    
    if not results:
        print_info(f"No notes found matching '{query}'")
        return
        
    for item in results:
        console.print(f"[bold cyan]{item['contact']}[/bold cyan] (Note {item['note_index']+1}): {item['note']}")


@command("list_notes", "List notes: list_notes [name]")
def handle_list_notes(service: AddressBookService, args: List[str]) -> None:
    name = args[0] if args else None
    
    try:
        results = service.get_notes(name)
        if not results:
             print_info(f"No notes found{' for ' + name if name else ''}.")
             return

        for contact_name, note_list in results.items():
            if note_list:
                console.print(f"[bold]{contact_name}[/bold]:")
                for i, note in enumerate(note_list, 1):
                    console.print(f"  {i}. {note}")
                    
    except BotException as e:
        print_error(str(e))


# --- TAGS MANAGEMENT ---

@command("add_tag", "Add tag: add_tag <name> <tag>")
def handle_add_tag(service: AddressBookService, args: List[str]) -> None:
    if len(args) < 2:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="add_tag <name> <tag>"))
        return
    
    name = args[0]
    tag = " ".join(args[1:])
    try:
        service.add_tag(name, tag)
        print_success(random.choice(TAG_MESSAGES["added"]).format(name=name, tag=tag))
    except BotException as e:
        print_error(str(e))


@command("remove_tag", "Remove tag: remove_tag <name> <tag>")
def handle_remove_tag(service: AddressBookService, args: List[str]) -> None:
    if len(args) < 2:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="remove_tag <name> <tag>"))
        return
    
    name = args[0]
    tag = " ".join(args[1:])
    
    try:
        service.remove_tag(name, tag)
        print_success(random.choice(TAG_MESSAGES["removed"]).format(name=name))
    except BotException as e:
        print_error(str(e))


@command("list_tags", "List all tags")
def handle_list_tags(service: AddressBookService, args: List[str]) -> None:
    results = service.get_all_tags()
    if not results:
        print_info("No tags found.")
        return
    
    for name, t_list in results.items():
        if t_list:
            console.print(f"[bold]{name}[/bold]: {', '.join(t_list)}")


@command("filter_by_tag", "Find contacts by tag: filter_by_tag <tag>")
def handle_filter_by_tag(service: AddressBookService, args: List[str]) -> None:
    if not args:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="filter_by_tag <tag>"))
        return
    
    tag = " ".join(args)
    records = service.filter_by_tag(tag)
    
    if not records:
        print_info(f"No contacts found with tag '{tag}'")
        return

    table = Table(title=f"Contacts with Tag: {tag}")
    table.add_column("Tag", style="red")
    table.add_column("Full Name", style="cyan")
    table.add_column("Days to B-day", style="magenta")
    table.add_column("Phone", style="green")
    table.add_column("Email", style="blue")
    table.add_column("Birthday", style="yellow")
    table.add_column("Note", style="white")

    for record in records:
        phones = ", ".join(p.value for p in record.phones)
        email = record.email.value if record.email else "-"
        bday = record.birthday.value if record.birthday else "-"
        
        days_until = "-"
        if record.birthday:
            d = record.days_to_birthday()
            if d is not None:
                days_until = str(d)
        
        note_str = "\n".join(record.notes) if record.notes else "-"
        
        table.add_row(tag, record.name.value, days_until, phones, email, bday, note_str)
    
    console.print(Align.center(table))


# --- BIRTHDAYS ---

@command("days_to_bday", "Days until birthday (one contact)")
def handle_days_to_bday(service: AddressBookService, args: List[str]) -> None:
    if not args:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="days_to_bday <name>"))
        return
    
    name = args[0]
    try:
        days = service.get_days_to_birthday(name)
        print_info(f"Days until {name}'s birthday: [bold]{days}[/bold]")
    except BotException as e:
        print_error(str(e))


@command("birthdays", "Upcoming birthdays: birthdays [days]")
def handle_birthdays(service: AddressBookService, args: List[str]) -> None:
    days = DEFAULT_BIRTHDAY_LOOKAHEAD_DAYS
    if args:
        try:
            days = int(args[0])
        except ValueError:
            print_error("Days must be a number.")
            return
            
    upcoming = service.get_upcoming_birthdays(days)
    if not upcoming:
        print_info(f"No birthdays in the next {days} days.")
        return

    console.print(f"[bold]Birthdays in the next {days} days:[/bold]")
    
    table = Table(title=f"Upcoming Birthdays (Next {days} days)")
    table.add_column("Birthday", style="yellow")
    table.add_column("Days to B-day", style="magenta")
    table.add_column("Full Name", style="cyan")
    table.add_column("Tag", style="red")
    table.add_column("Phone", style="green")
    table.add_column("Email", style="blue")
    table.add_column("Note", style="white")
    
    for item in upcoming:
        name = item['name']
        try:
             record = service.get_contact(name)
             phones = ", ".join(p.value for p in record.phones)
             email = record.email.value if record.email else "-"
             note_str = "\n".join(record.notes) if record.notes else "-"
             tag_str = ", ".join(record.tags) if record.tags else "-"
             
             table.add_row(
                item['birthday'], 
                str(item['days_until']), 
                name,
                tag_str,
                phones, 
                email, 
                note_str
            )
        except BotException:
             continue
        
    console.print(Align.center(table))


# --- IMPORT/EXPORT ---

@command("import", "Import data: import <file.json|csv>")
def handle_import(service: AddressBookService, args: List[str]) -> None:
    if not args:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="import <path>"))
        return
    
    path = args[0]
    try:
        import_file(service.book, path)
        print_success(random.choice(SYSTEM_MESSAGES["import_success"]).format(path=path))
    except Exception as e:
        print_error(f"Import failed: {e}")


@command("export", "Export data: export <file.json|csv>")
def handle_export(service: AddressBookService, args: List[str]) -> None:
    if not args:
        print_error(random.choice(CMD_ERRORS["missing_args"]).format(syntax="export <path>"))
        return
    
    path = args[0]
    try:
        export_file(service.book, path)
        print_success(random.choice(SYSTEM_MESSAGES["export_success"]).format(path=path))
    except Exception as e:
        print_error(f"Export failed: {e}")


@command("delete_all", "Delete ALL content: delete_all")
def handle_delete_all(service: AddressBookService, args: List[str]) -> None:
    console.print("[bold red]⚠️  WARNING: This will delete ALL contacts, notes, and tags![/bold red]")
    confirm = console.input("[bold yellow]Are you sure? Type 'YES' to confirm: [/bold yellow]")
    
    if confirm == "YES":
        service.delete_all()
        print_success(random.choice(SYSTEM_MESSAGES["delete_all"]))
    else:
        print_info("Operation canceled. Your data is safe.")


@command("exit", "Exit the application")
def handle_exit(service: AddressBookService, args: List[str]) -> None:
    pass

@command("close", "Exit the application")
def handle_close(service: AddressBookService, args: List[str]) -> None:
    pass


# --- PARSER & DISPATCHER ---

def parse(raw: str) -> Tuple[Optional[str], List[str]]:
    try:
        parts = shlex.split(raw)
        if not parts:
            return None, []
        return parts[0].lower(), parts[1:]
    except ValueError:
        return None, []

def dispatch(service: AddressBookService, raw_input: str) -> bool:
    """Parses and executes a command."""
    cmd, args = parse(raw_input)
    
    if not cmd:
        return True

    if cmd in ('exit', 'close'):
        return False
    
    if cmd in COMMAND_REGISTRY:
        handler, _ = COMMAND_REGISTRY[cmd]
        try:
            handler(service, args)
        except Exception as e:
            # We print the error but keep the bot alive
            print_error(f"Error executing '{cmd}': {e}")
    else:
        msg = random.choice(CMD_ERRORS["unknown"]).format(cmd=cmd)
        print_error(msg)
    
    return True
