from utils import Utils
from managers import DBManager, UserManager
from inventory import Book, Magazine, Journal, Manga, WesternComic, ResearchPaper
from transaction_manager import TransactionManager


def main():
    Utils.rich_print("\nWELCOME TO PUBLIC DONATION SYSTEM\n", tag="prompt")

    while True:
        Utils.rich_print("1. Register\n2. Login\n3. Exit", tag="info")
        action = Utils.rich_prompting(
            "From the options, select your choice (number)", tag="prompt"
        )

        # validate input
        if action.isdigit():  # check if input is numeric
            if action in ["1", "2", "3"]:
                break
            else:
                Utils.rich_print(
                    "\nInvalid Number. Choose only the numbers given!!\n", tag="error"
                )
        else:
            Utils.rich_print(
                "\nInvalid Input. Choose only the numbers given!!\n", tag="error"
            )

    # necessary database setup
    db_manager = DBManager()
    db_manager.setup_transactions_table()

    # user database operations
    user_manager = UserManager(db_manager)
    user_manager.get_fields()
    user_manager.create_inventory_layout_sqlite()

    transaction_manager = TransactionManager(
        db_manager, user_name=user_manager.user_name, item_types=item_types
    )

    # initialize all tables
    for item_type_cls in item_types.values():
        item_type = item_type_cls()
        item_type.create_inventory_layout_sqlite(db_manager)

    # program logic
    if action == "1":  # register
        try:
            user_manager.register()
        except Exception:
            Utils.rich_print("Error during registration. Exiting...", tag="error")
            return  # terminate if unable to register user

    elif action == "2":  # login
        if not user_manager.login():
            Utils.rich_print("Login failed. Exiting...", tag="error")
            return  # terminate if not a valid user

    # main menu loop after login
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
        action = Utils.rich_prompting("Enter your choice (number)", tag="prompt")

        # add items
        if action == "1":
            transaction_manager.complete_add_action()

        # search items
        elif action == "2":
            involved_cols, results, item_type_choice = (
                transaction_manager.initiate_search_or_borrow_or_return_action()
            )
            if results:
                Utils.format_output_display(
                    columns=involved_cols, results=results
                )

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
            else:
                Utils.rich_print("No items found for your search.", tag="error")

        # borrow items
        elif action == "3":
            involved_cols, results, item_type_choice = (
                transaction_manager.initiate_search_or_borrow_or_return_action(
                    is_borrow=True
                )
            )
            if results:
                Utils.format_output_display(
                    columns=involved_cols, results=results
                )
                transaction_manager.complete_borrow_or_return_action(
                    item_type_choice=item_type_choice,
                )
            else:
                Utils.rich_print("No items found for your search.", tag="error")

        # return items
        elif action == "4":
            involved_cols, results, item_type_choice = (
                transaction_manager.initiate_search_or_borrow_or_return_action(
                    is_borrow=True,
                    is_return=True,
                )
            )
            if results:
                Utils.format_output_display(
                    columns=involved_cols, results=results
                )
                transaction_manager.complete_borrow_or_return_action(
                    item_type_choice=item_type_choice,
                    is_return=True,
                )
            else:
                Utils.rich_print("Nothing has been borrowed to return.", tag="error")

        # personal inventory
        elif action == "5":
            Utils.rich_print(
                "\nWhat do you want to do?\n"
                "1. View items you have contributed.\n"
                "2. View items you have borrowed so far.\n"
                "3. View items you are currently borrowing.",
                tag="info",
            )
            add_action = Utils.rich_prompting("Enter your choice (number)", tag="prompt")

            if add_action == "1":
                involved_cols, results = transaction_manager.get_items_added_by_user()
                if results:
                    Utils.format_output_display(
                        columns=involved_cols, results=results
                    )
                else:
                    Utils.rich_print("Nothing has been contributed.", tag="prompt")

            elif add_action == "2":
                # show borrow actions till now, including returned items
                involved_cols, results = transaction_manager.get_transaction_history(
                    is_active=False
                )
                if results:
                    Utils.format_output_display(
                        columns=involved_cols, results=results
                    )
                else:
                    Utils.rich_print("No transaction history so far.", tag="prompt")

            elif add_action == "3":
                # show only active borrow items
                involved_cols, results = transaction_manager.get_transaction_history(
                    is_active=True,
                )
                if results:
                    Utils.format_output_display(
                        columns=involved_cols, results=results
                    )
                else:
                    Utils.rich_print("No active borrowed items found.", tag="prompt")

        # log out
        elif action == "6":
            Utils.rich_print("Logged out successfully.", tag="success")
            break

        else:
            Utils.rich_print("Invalid choice. Please try again!", tag="error")


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

if __name__ == "__main__":
    main()
