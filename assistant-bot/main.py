import os
import sys

# Ensure the package is in the python path if running from root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from assistant_bot import storage
from assistant_bot.app import App
from assistant_bot.utils.ux_messages import GOODBYE_MESSAGES
from assistant_bot.services.address_book_service import AddressBookService


def main() -> None:
    """
    Main entry point for the Assistant Bot application.
    Handles data loading, application lifecycle, and clean shutdown.
    """
    # 1. Load Data (Pickle with JSON fallback)
    address_book = storage.load_pickle()

    if address_book is None:
        address_book = storage.load_address_book()

    # 2. Strict Sync (Ensure all formats are consistent on startup)
    storage.save_all(address_book)

    # 3. Initialize Service
    service = AddressBookService(address_book)

    # 4. Application Loop
    app = App(service)
    try:
        app.run()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # 5. Save & Exit
        storage.save_all(address_book)
        print(GOODBYE_MESSAGES[0])


if __name__ == '__main__':
    main()
