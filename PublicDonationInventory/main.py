from typing import Optional

from utils import Utils
from managers import DBManager, UserManager
from inventory import Book, Magazine, Journal, Manga, WesternComic, ResearchPaper
from transaction_manager import TransactionManager

# Global inventory types
# Add new classes if required
item_types = {
    "1": Book,
    "2": Magazine,
    "3": Journal,
    "4": Manga,
    "5": WesternComic,
    "6": ResearchPaper,
}


def setup_database() -> DBManager:
    """
    Opens the database and makes sure every table exists.
    """
    db_manager = DBManager()
    db_manager.setup_transactions_table()
    db_manager.create_users_table()
    for item_type_cls in item_types.values():
        item_type_cls().create_inventory_layout_sqlite(db_manager)
    return db_manager


def authenticate(db_manager: DBManager) -> Optional[str]:
    """
    Shows the welcome menu until the user logs in, registers, or exits.

    :return: The authenticated user name, or None if the user chose to exit.
    """
    Utils.rich_print("\nWELCOME TO PUBLIC DONATION SYSTEM\n", tag="prompt")

    while True:
        Utils.rich_print("1. Register\n2. Login\n3. Exit", tag="info")
        action = Utils.rich_prompting(
            "From the options, select your choice (number)", tag="prompt"
        ).strip()

        if action == "3":
            return None
        if action not in ("1", "2"):
            Utils.rich_print(
                "\nInvalid choice. Choose only the numbers given!!\n", tag="error"
            )
            continue

        user_manager = UserManager(db_manager)
        user_manager.get_fields()
        user_name = user_manager.user_name.strip()
        user_manager.user_name = user_name

        if action == "1":
            succeeded = user_manager.register()
        else:
            succeeded = user_manager.login()

        if succeeded:
            return user_name


def show_table(columns, results, empty_message: str, empty_tag: str = "error") -> bool:
    """
    Displays results as a table, or a message if there are none.

    :return: True if there was something to display.
    """
    if not columns:
        return False  # the user backed out of the menu
    if not results:
        Utils.rich_print(empty_message, tag=empty_tag)
        return False
    Utils.format_output_display(columns=columns, results=results)
    return True


def personal_inventory(transaction_manager: TransactionManager) -> None:
    """
    Handles the personal inventory submenu.
    """
    Utils.rich_print(
        "\nWhat do you want to do?\n"
        "1. View items you have contributed.\n"
        "2. View items you have borrowed so far.\n"
        "3. View items you are currently borrowing.",
        tag="info",
    )
    choice = Utils.rich_prompting("Enter your choice (number)", tag="prompt").strip()

    if choice == "1":
        columns, results = transaction_manager.get_items_added_by_user()
        show_table(columns, results, "Nothing has been contributed.", "prompt")
    elif choice == "2":
        # show borrow actions till now, including returned items
        columns, results = transaction_manager.get_transaction_history(is_active=False)
        show_table(columns, results, "No transaction history so far.", "prompt")
    elif choice == "3":
        # show only active borrow items
        columns, results = transaction_manager.get_transaction_history(is_active=True)
        show_table(columns, results, "No active borrowed items found.", "prompt")
    else:
        Utils.rich_print("Invalid choice. Please try again!", tag="error")


def run_session(db_manager: DBManager, user_name: str) -> None:
    """
    Main menu loop for a logged in user. Returns when the user logs out.
    """
    transaction_manager = TransactionManager(
        db_manager, user_name=user_name, item_types=item_types
    )

    while True:
        Utils.rich_print("\nChoose action\n", tag="prompt")

        Utils.rich_print(
            "1. Add Items\n"
            "2. Search Items\n"
            "3. Borrow Items\n"
            "4. Return Items\n"
            "5. Personal Inventory\n"
            "6. Log out",
            tag="info",
        )
        action = Utils.rich_prompting("Enter your choice (number)", tag="prompt").strip()

        if action == "1":
            transaction_manager.complete_add_action()

        elif action == "2":
            columns, results, item_type_choice = (
                transaction_manager.initiate_search_or_borrow_or_return_action()
            )
            if not show_table(columns, results, "No items found for your search."):
                continue
            borrow_choice = (
                Utils.rich_prompting(
                    "Would you like to borrow from these items? Type (yes/no)",
                    tag="prompt",
                )
                .strip()
                .lower()
            )
            if borrow_choice in ["yes", "y"]:
                transaction_manager.complete_borrow_or_return_action(
                    item_type_choice=item_type_choice,
                )
            else:
                Utils.rich_print("Borrowing cancelled.", tag="info")

        elif action == "3":
            columns, results, item_type_choice = (
                transaction_manager.initiate_search_or_borrow_or_return_action(
                    is_borrow=True
                )
            )
            if show_table(columns, results, "No items found for your search."):
                transaction_manager.complete_borrow_or_return_action(
                    item_type_choice=item_type_choice,
                )

        elif action == "4":
            columns, results, item_type_choice = (
                transaction_manager.initiate_search_or_borrow_or_return_action(
                    is_borrow=True,
                    is_return=True,
                )
            )
            if show_table(columns, results, "Nothing has been borrowed to return."):
                transaction_manager.complete_borrow_or_return_action(
                    item_type_choice=item_type_choice,
                    is_return=True,
                )

        elif action == "5":
            personal_inventory(transaction_manager)

        elif action == "6":
            Utils.rich_print("Logged out successfully.", tag="success")
            return

        else:
            Utils.rich_print("Invalid choice. Please try again!", tag="error")


def main() -> None:
    db_manager = setup_database()
    try:
        while True:
            user_name = authenticate(db_manager)
            if user_name is None:
                Utils.rich_print("Goodbye!", tag="info")
                return
            run_session(db_manager, user_name)
    except (KeyboardInterrupt, EOFError):
        Utils.rich_print("\nGoodbye!", tag="info")
    finally:
        db_manager.close()


if __name__ == "__main__":
    main()
