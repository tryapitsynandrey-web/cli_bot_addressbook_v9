# Assistant Bot (CLI Address Book)

A resilient, high-performance Command Line Interface (CLI) application for secure contact and note management. 

## Architecture Overview

The project follows Domain-Driven Design (DDD) principles to strictly separate business logic, user interface, and data persistence.

- **`domain/`**: Houses core business entities (Models, Fields, Records, Contacts, Notes) and custom domain exceptions. This layer is entirely independent of UI or storage mechanisms.
- **`services/`**: Orchestrates application logic (`AddressBookService`). Acts as an intermediary between the UI commands and the domain models.
- **`ui/`**: Manages terminal input/output, interactive prompts via `prompt_toolkit`, standard console output formatting via `rich`, and command routing (`commands.py`).
- **`utils/`**: Shared utilities, primarily UX copy (`ux_messages.py`) ensuring standardized feedback across the app.
- **`storage.py` & `import_export.py`**: Infrastructure components handling dual-format persistence (Pickle and JSON fallbacks) and data migration (CSV/JSON/Pickle pipelines).

## Features
- **Interactive CLI Environment**: Persistent command prompt with context-aware tab autocompletion.
- **Rich Output Formatting**: Vibrant, structured, and colorized terminal outputs.
- **Resilient Data Storage**: Dual-format saving (Pickle & JSON) ensuring zero data loss upon critical failure.
- **Tag Management**: Support for assigning, filtering, and removing custom tags attached to contacts and notes.
- **Data Export/Import**: Built-in mechanisms to serialize and read data across CSV, JSON, and Pickle native formats.

## Project Structure

```text
assistant-bot/
├── main.py                     # Entry point for the CLI application
├── generate_data.py            # Utility script for seeding test data
├── user_address_book/          # Local persistent storage directory
└── assistant_bot/
    ├── app.py                  # CLI event loop & completion logic
    ├── config.py               # Shared constants & configurations
    ├── import_export.py        # Adapter layer for CSV/JSON handling
    ├── storage.py              # Save/load dual-format persistent layer
    ├── domain/                 # Domain constraints & models
    ├── services/               # AddressBook orchestrator logic
    ├── ui/                     # Rich console wrappers & command registry
    └── utils/                  # UX message catalogs
```

## Installation

### Local Environment
1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd cli_bot_addressbook_v9
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   *(Note: Relies on `rich` and `prompt_toolkit`)*
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python assistant-bot/main.py
   ```

### Docker
*Docker setup is not currently provided within the repository base.*

## Usage

### CLI Usage
Launch the application by running the main entry script:
```bash
python assistant-bot/main.py
```
You will enter the interactive `bot>` prompt. 
- Type commands to interact with the bot (e.g., `add`, `filter_by_tag`, `add-note`).
- Press `Tab` to leverage context-aware command and tag autocompletion.
- Type `exit` or `close` to safely shutdown the application and commit pending writes to disk.

### Web Usage
*This project does not contain a web server component; it operates strictly as a CLI tool.*

## Data Storage
The application utilizes a dual-serialization strategy to protect against data corruption:
- **Formats Supported**: Default storage is in `.pkl` (Python Pickle), with automated synchronous fallback mechanisms leveraging `.json`. `.csv` formats are strictly supported for import/export routines.
- **Storage Location**: By default, data dumps are written into the `assistant-bot/user_address_book/` directory relative to the repository root.

## Configuration
Application bounds and heuristics (e.g., the threshold for consecutive errors to prompt an automated help dialogue) can be adjusted globally by modifying the constants located within `assistant-bot/assistant_bot/config.py`.

## Development Notes
- **Extensibility**: The command dictionary mapped in `ui/commands.py` allows straightforward attachment of additional user commands. Handlers parse the standardized user input and defer processing immediately to `services.AddressBookService`.
- **Design Decisions**: Memory footprint is prioritized for I/O speed. The entire dataset is loaded into operational memory during the bootstrap validation in `main.py`, serialized, and rewritten dynamically upon application termination.

## Limitations / Assumptions
- The application executes single-threaded without implemented resource locking. Concurrent process execution mapped to the exact same disk storage target may yield file corruption or race conditions.
- Datasets are aggressively loaded into memory on startup; it assumes address books will not inherently exceed local hardware RAM availability limits.

## License
*Not specified within the current repository structure.*
