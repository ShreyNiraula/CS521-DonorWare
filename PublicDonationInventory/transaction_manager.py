from datetime import datetime, timedelta
from utils import CATEGORY_ICONS, Utils
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

    @staticmethod
    def build_like_clause(fields):
        """
        Builds a parenthesised OR-joined LIKE clause for the given fields.
        Pair it with like_params(), which escapes wildcard characters.
        """
        return "(" + " OR ".join(f"{f} LIKE ? ESCAPE '\\'" for f in fields) + ")"

    @staticmethod
    def like_params(search_word: str, count: int) -> tuple:
        """
        Builds the parameters for build_like_clause, escaping %, _ and the escape character.
        """
        escaped = (
            search_word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        return tuple(f"%{escaped}%" for _ in range(count))

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
        valid_types = {cls.cls_item_type for cls in self.item_types.values()}
        if item_type not in valid_types:
            Utils.rich_print(f"Unknown category '{item_type}'.", tag="error")
            return

        owner = self.db_manager.fetchall(
            f"SELECT user_name FROM {item_type} WHERE id = ?", (item_id,)
        )
        if not owner:
            Utils.rich_print(f"No {item_type} found with ID {item_id}.", tag="error")
            return
        if owner[0][0] == self.user_name:
            Utils.rich_print("You cannot borrow an item you donated.", tag="error")
            return

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
        like_clauses = self.build_like_clause(fields)
        query = f"SELECT '{cls_item_type}' as Category, * FROM {cls_item_type} WHERE {like_clauses}"

        like_params = self.like_params(search_word, len(fields))
        results = self.db_manager.fetchall(query, like_params)
        return ["Category", "id"] + fields, results

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

            like_clauses = self.build_like_clause(fields)
            sub_queries.append(
                f"SELECT '{table_name}' as Category, id, {column_selection} FROM {table_name} WHERE {like_clauses}"
            )
            like_params.extend(self.like_params(search_word, len(fields)))

        query = "\n UNION \n".join(sub_queries)

        results = self.db_manager.fetchall(query, tuple(like_params))
        return ["Category", "id"] + common_columns, results

    def get_borrowed_given_item(self, item_type, search_word):
        """
        Retrieves a list of borrowed items based on the item type and search criteria.

        :param item_type: The type of the item (e.g., 'book').
        :param search_word: The keyword to filter by name.
        :return: List of columns used in involved and query result
        """
        fields = item_type.fields
        cls_item_type = item_type.cls_item_type

        like_clauses = self.build_like_clause([f"i.{field}" for field in fields])
        query = f"""
        SELECT t.id as TransactionId, i.*
        FROM transactions t
        JOIN {cls_item_type} i ON t.item_id = i.id
        WHERE t.user_name = ? AND t.item_type='{cls_item_type}' AND t.status = 'borrowed' AND {like_clauses}
        """
        params = (self.user_name,) + self.like_params(search_word, len(fields))

        results = self.db_manager.fetchall(query, params)
        return ["TransactionId", "id"] + fields, results

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
                WHERE user_name = ?
            """
            )

        query = "\n UNION ALL \n".join(sub_queries)
        final_query = (
            f"SELECT Category, {', '.join(common_columns)}, user_name FROM ({query})"
        )
        params = tuple(self.user_name for _ in self.item_types)
        return ["Category"] + common_columns + ["user_name"], self.db_manager.fetchall(
            final_query, params
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
                WHERE t.item_type = '{table_name}' AND t.user_name = ? {borrow_filter}
                """
            )

        query = "\n UNION ALL \n".join(sub_queries)
        params = tuple(self.user_name for _ in self.item_types)
        if is_active:
            query = f"""
            SELECT * FROM ({query}) 
            ORDER BY due_date ASC
            """
        return [
            "Category",
            "TransactionId",
        ] + common_columns + extra_columns + [
            "user_name"
        ], self.db_manager.fetchall(query, params)

    def complete_add_action(self):
        """
        Completes process for the addition of a new item to the inventory.
        """
        while True:
            exit_option = len(self.item_types) + 1

            self.show_item_menu("Add an item", [(str(exit_option), "Back to main menu")])

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

            self.show_item_menu(
                f"Select item type {action}",
                [
                    (str(unsure_option), "Unsure about the category"),
                    (str(exit_option), "Back to main menu"),
                ],
            )

            item_type_choice = Utils.rich_prompting(
                "Enter your choice (number)", tag="prompt"
            )

            if item_type_choice.isdigit():
                item_type_choice = int(item_type_choice)

                if item_type_choice == exit_option:
                    Utils.rich_print("Returning to the main menu...", tag="success")
                    return [], [], None  # Exit to main menu

                elif item_type_choice == unsure_option:
                    search_word = Utils.rich_prompting(
                        f"Search by anything you are looking {action}", tag="prompt"
                    )
                    if is_return:
                        involved_cols, results = self.get_transaction_history(
                            is_active=True
                        )
                        needle = search_word.strip().lower()
                        results = [
                            row
                            for row in results
                            if any(needle in str(cell).lower() for cell in row)
                        ]
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
            id_label = "Txn ID"

        if str(item_type_choice) not in self.item_types.keys():
            choice_category = (
                Utils.rich_prompting(
                    f"Please select the category of the item you want {action}",
                    tag="prompt",
                )
                .strip()
                .lower()
                .replace(" ", "_")
            )
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

    def show_item_menu(self, title: str, extras=()) -> None:
        """
        Shows the item types as a menu, followed by any extra (key, label) entries.
        """
        options = [
            (
                key,
                f"{CATEGORY_ICONS.get(cls.cls_item_type, '•')}  "
                f"{cls.cls_item_type.replace('_', ' ').title()}",
            )
            for key, cls in self.item_types.items()
        ]
        Utils.show_menu(title, options + list(extras))

    def get_dashboard_stats(self) -> dict:
        """
        Counts the current user's donations and borrows for the dashboard.
        """
        donated = sum(
            self.db_manager.fetchall(
                f"SELECT COUNT(*) FROM {cls.cls_item_type} WHERE user_name = ?",
                (self.user_name,),
            )[0][0]
            for cls in self.item_types.values()
        )
        rows = self.db_manager.fetchall(
            "SELECT status, due_date FROM transactions WHERE user_name = ?",
            (self.user_name,),
        )
        today = datetime.now().strftime("%Y-%m-%d")
        active = [due for status, due in rows if status == "borrowed"]
        return {
            "donated": donated,
            "borrowing": len(active),
            "overdue": sum(1 for due in active if due < today),
            "returned": sum(1 for status, _ in rows if status == "returned"),
        }
