from datetime import datetime, timedelta
from utils import Utils
from ordered_set import OrderedSet

from rich.console import Console

console = Console()


class TransactionManager:
    """
    Manages transactions (borrow, return, renew) and utilities for inventory.
    """

    def __init__(self, db_manager, user_name: str, item_types: dict) -> None:
        """
        Initializes the TransactionManager instance with params: the database manager, the current user’s name, item types

        :param db_manager: Instance of DBManager for database operations.
        :param user_name: Name of the user performing transactions.
        """
        self.db_manager = db_manager
        self.user_name = user_name
        self.item_types = item_types

    def borrow_item(
        self, item_type: str, item_id: int, borrow_duration_days: int = 7
    ) -> None:
        """
        Handles the borrowing process of an item.
        The method checks availability of item and registers the item as borrowed if currently not being borrowed by any one

        :param item_type: The type of the item (e.g., 'book').
        :param item_id: The ID of the item to borrow.
        :param borrow_duration_days: Duration for borrowing in days.
        """
        query = "SELECT * FROM transactions WHERE item_id = ? AND item_type = ? AND status = 'borrowed'"
        active_borrows = self.db_manager.fetchall(query, (item_id, item_type))

        if active_borrows:
            Utils.rich_print("The item is currently borrowed by another user.", tag="error")
            return

        try:
            borrow_date = datetime.now().strftime("%Y-%m-%d")
            due_date = (datetime.now() + timedelta(days=borrow_duration_days)).strftime(
                "%Y-%m-%d"
            )

            query = """INSERT INTO transactions (user_name, item_type, item_id, borrow_date, due_date, status) 
                       VALUES (?, ?, ?, ?, ?, 'borrowed')"""
            self.db_manager.execute(
                query, (self.user_name, item_type, item_id, borrow_date, due_date)
            )
            Utils.rich_print(
                f"Item borrowed successfully. Due date: {due_date}", tag="success"
            )
        except Exception as e:
            Utils.rich_print(f"Error borrowing item: {e}", tag="error")

    def return_item(self, transaction_id: int) -> None:
        """
        Processes the return of an item by updating and marking the item as returned.
        It also makes sure that items to return are in borrowed status

        :param transaction_id: The ID of the self.
        """
        query = "SELECT * FROM transactions WHERE id = ? AND user_name = ? AND status = 'borrowed'"
        transaction = self.db_manager.fetchall(query, (transaction_id, self.user_name))

        if not transaction:
            Utils.rich_print("No active borrow found with this transaction ID.", tag="error")
            return

        try:
            return_date = datetime.now().strftime("%Y-%m-%d")
            query = "UPDATE transactions SET return_date = ?, status = 'returned' WHERE id = ?"
            self.db_manager.execute(query, (return_date, transaction_id))
            Utils.rich_print("Item returned successfully.", tag="success")
        except Exception as e:
            Utils.rich_print(f"Error returning item: {e}", tag="error")

    def search_with_auto_complete(self, item_type, search_word: str):
        """
        Provides a search feature for specific item type. Allows to search by any field associated with that item type

        :param item_type: The item_type to search for.
        :param search_word: The search word used to filter out the item.
        :return: List of columns used in involved and query result
        """
        fields = item_type.fields
        cls_item_type = item_type.cls_item_type

        # search by anything using fields present in item_type
        like_clauses = " OR ".join([f"{field} LIKE ?" for field in fields])
        query = f"SELECT '{cls_item_type}' as Category, * FROM {cls_item_type} WHERE {like_clauses}"

        like_params = tuple(f"%{search_word}%" for _ in fields)
        try:
            results = self.db_manager.fetchall(query, like_params)
            return ["Category", "id"] + fields, results
        except Exception as e:
            Utils.rich_print(f"[red bold]Error during search[/red bold] {e}", tag="error")

    def search_for_every_item_type(self, search_word):
        """
        Similar to search with auto complete function, but allows to search for any item types

        :param search_word: The search word used to filter out the item.
        :return: List of columns used in involved and query result
        """
        sub_queries = []
        like_params = []

        common_columns = []
        for item_cls in self.item_types.values():
            common_columns.extend(item_cls().fields)
        common_columns = list(OrderedSet(common_columns))

        for item_cls in self.item_types.values():
            item_obj = item_cls()
            fields = item_obj.fields
            table_name = item_obj.cls_item_type

            selected_columns = [
                f"{field} AS {field}" if field in fields else f"NULL AS {field}"
                for field in common_columns
            ]
            column_selection = ", ".join(selected_columns)

            like_clauses = " OR ".join([f"{field} LIKE ?" for field in fields])
            sub_queries.append(
                f"SELECT '{table_name}' as Category, id, {column_selection} FROM {table_name} WHERE {like_clauses}"
            )
            like_params.extend(f"%{search_word}%" for _ in fields)

        query = "\n UNION \n".join(sub_queries)

        try:
            results = self.db_manager.fetchall(query, tuple(like_params))
            Utils.rich_print("Search results retrieved successfully!", tag="success")
            return ["Category", "id"] + common_columns, results
        except Exception as e:
            Utils.rich_print(f"Error during search: {e}", tag="error")

    def get_borrowed_given_item(self, item_type, search_word):
        """
        Retrieves a list of borrowed items based on the item type and search criteria.

        :param item_type: The type of the item (e.g., 'book').
        :param search_word: The keyword to filter by name.
        :return: List of columns used in involved and query result
        """
        fields = item_type.fields
        cls_item_type = item_type.cls_item_type

        like_clauses = " OR ".join([f"{field} LIKE ?" for field in fields])
        query = f"""
        SELECT t.id as TransactionId, i.*
        FROM transactions t
        JOIN {cls_item_type} i ON t.item_id = i.id
        WHERE t.user_name = ? AND t.item_type='{cls_item_type}' AND t.status = 'borrowed' AND {like_clauses}
        """
        params = tuple([self.user_name] + [f"%{search_word}%" for _ in fields])

        try:
            results = self.db_manager.fetchall(query, params)
            Utils.rich_print(f"Borrowed items found for {self.user_name}.", tag="success")
            return ["TransactionId", "id"] + fields, results
        except Exception as e:
            Utils.rich_print(f"Error during retrieval of borrowed items: {e}", tag="error")

    def get_items_added_by_user(self):
        """
        Fetches all items added by the current user.
        :return: List of columns used in involved and query result
        """
        sub_queries = []
        common_columns = []
        for item_cls in self.item_types.values():
            common_columns.extend(item_cls().fields)
        common_columns = list(OrderedSet(common_columns))

        for item_cls in self.item_types.values():
            item_obj = item_cls()
            table_name = item_obj.cls_item_type
            select_columns = [
                f"{col}" if col in item_obj.fields else f"NULL AS {col}"
                for col in common_columns
            ]

            sub_queries.append(
                f"""
                SELECT '{table_name}' as category, {', '.join(select_columns)}, user_name
                FROM {table_name}
                WHERE user_name = '{self.user_name}'
            """
            )

        query = "\n UNION ALL \n".join(sub_queries)
        final_query = (
            f"SELECT Category, {', '.join(common_columns)}, user_name FROM ({query})"
        )
        print(final_query)
        return ["Category"] + common_columns + ["user_name"], self.db_manager.fetchall(
            final_query
        )

    def get_transaction_history(self, is_active):
        """
        Retrieves the transaction history for the current user, filtering by active or completed transactions.
        Active filtering is performed for the Active Borrow transaction display.

        :param is_active: Whether the transaction is active. Ie, whether it is referring to active borrow or all borrows
        :return: List of columns used in involved and query result
        """
        extra_columns = ["borrow_date", "due_date", "return_date", "status"]

        common_columns = []
        for item_cls in self.item_types.values():
            common_columns.extend(item_cls().fields)
        common_columns = list(OrderedSet(common_columns))

        sub_queries = []
        for item_cls in self.item_types.values():
            item_obj = item_cls()
            table_name = item_obj.cls_item_type

            select_columns = [
                f"{col}" if col in item_obj.fields else f"NULL AS {col}"
                for col in common_columns
            ]
            select_columns.extend(extra_columns)

            borrow_filter = "AND t.status = 'borrowed'" if is_active else ""
            sub_queries.append(
                f"""
                SELECT '{table_name}' as Category, t.id as TransactionId, {', '.join(select_columns)}, t.user_name as user_name
                FROM transactions t
                JOIN {table_name} b ON t.item_id = b.id
                WHERE t.item_type = '{table_name}' AND t.user_name = '{self.user_name}' {borrow_filter}
                """
            )

        query = "\n UNION ALL \n".join(sub_queries)
        if is_active:
            query = f"""
            SELECT * FROM ({query}) 
            ORDER BY ABS(julianday(due_date) - julianday(borrow_date)) ASC
            """
        return [
            "Category",
            "TransactionId",
        ] + common_columns + extra_columns + [
            "user_name"
        ], self.db_manager.fetchall(query)

    def complete_add_action(self):
        """
        Completes process for the addition of a new item to the inventory.
        """
        while True:
            exit_option = len(self.item_types) + 1

            Utils.rich_print("\nSelect item type to add", tag="prompt")

            # dynamically print the item
            self.print_items()
            Utils.rich_print(f"{exit_option}. Exit", tag="info")

            item_type_choice = Utils.rich_prompting(
                "Enter your choice (number)", tag="prompt"
            )

            if item_type_choice.isdigit():
                item_type_choice = int(item_type_choice)
                if item_type_choice == exit_option:
                    Utils.rich_print("Returning to the main menu...", tag="success")
                    return
                elif str(item_type_choice) in self.item_types:
                    item_type_cls = self.item_types[str(item_type_choice)]
                    item_type = item_type_cls()
                    item_type.get_fields()
                    item_type.add_to_inventory(self.db_manager, self.user_name)
                else:
                    Utils.rich_print("Invalid choice. Try again!", tag="error")
            else:
                Utils.rich_print("Invalid input. Please enter a valid number!", tag="error")

    def initiate_search_or_borrow_or_return_action(
        self, is_borrow: bool = False, is_return: bool = False
    ):
        """
        Initiates the search, borrow, or return actions based on the flags provided
        :param is_borrow:
        :param is_return:
        """
        action = "to search"
        if is_borrow:
            action = "to borrow"
        if is_return:
            action = "to return"

        while True:
            unsure_option = len(self.item_types) + 1
            exit_option = len(self.item_types) + 2

            Utils.rich_print(f"Select item type {action}", tag="prompt")
            self.print_items()
            Utils.rich_print(f"{unsure_option}. Unsure about the category", tag="info")
            Utils.rich_print(f"{exit_option}. Exit", tag="info")

            item_type_choice = Utils.rich_prompting(
                "Enter your choice (number)", tag="prompt"
            )

            if item_type_choice.isdigit():
                item_type_choice = int(item_type_choice)

                if item_type_choice == exit_option:
                    Utils.rich_print("Returning to the main menu...", tag="success")
                    return [], []  # Exit to main menu

                elif item_type_choice == unsure_option:
                    search_word = Utils.rich_prompting(
                        f"Search by anything you are looking {action}", tag="prompt"
                    )
                    if is_return:
                        involved_cols, results = self.get_transaction_history(
                            is_active=True
                        )
                    else:
                        involved_cols, results = self.search_for_every_item_type(
                            search_word
                        )
                    return involved_cols, results, item_type_choice

                elif str(item_type_choice) in self.item_types.keys():
                    item_type_cls = self.item_types[str(item_type_choice)]
                    item_type = item_type_cls()
                    cls_item_type = item_type.cls_item_type

                    search_word = Utils.rich_prompting(
                        f"Search by anything for {cls_item_type} you are looking {action}",
                        tag="prompt",
                    )
                    if is_return:
                        involved_cols, results = self.get_borrowed_given_item(
                            item_type=item_type,
                            search_word=search_word,
                        )
                    else:
                        involved_cols, results = self.search_with_auto_complete(
                            item_type, search_word
                        )
                    return involved_cols, results, item_type_choice
                else:
                    Utils.rich_print("Invalid item type selected. Try again!", tag="error")
            else:
                Utils.rich_print("Invalid input. Please enter a valid number!", tag="error")

    def complete_borrow_or_return_action(
        self, item_type_choice: int, is_return: bool = False
    ):
        """
        Completes a borrow or return action based on the type of item and whether it’s a return or borrow
        :param item_type_choice: choice typed by user
        :param is_return: flag to denote if borrow or return operation.
        """
        action = "to borrow"
        id_label = "ID"
        if is_return:
            action = "to return"
            id_label = "TransactionId"

        if str(item_type_choice) not in self.item_types.keys():
            choice_category = Utils.rich_prompting(
                f"Please select the category of the item you want {action}",
                tag="prompt",
            ).lower()
        else:
            choice_category = self.item_types[str(item_type_choice)]().cls_item_type

        while True:
            try:
                choice_id = int(
                    Utils.rich_prompting(
                        f"Please select the {id_label} of {choice_category} you want {action} "
                        f"(Choose the number listed on the leftmost side)",
                        tag="prompt",
                    )
                )
                break
            except ValueError:
                Utils.rich_print(
                    f"Invalid input! Please re-enter a valid {id_label}.", tag="error"
                )

        if is_return:
            self.return_item(transaction_id=choice_id)
        else:
            self.borrow_item(
                item_type=choice_category,
                item_id=choice_id,
            )

    def print_items(self):
        """
        Prints the item types in a formatted manner.
        """
        Utils.rich_print("Available Item Types", tag="prompt")
        for key, val in self.item_types.items():
            Utils.rich_print(
                f"{key}. {val.cls_item_type.capitalize()}", tag="info"
            )  # Styled output

