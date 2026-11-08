from datetime import datetime
from typing import List, Optional
from utils import Utils

DATE_FORMAT = "%Y-%m-%d"


class Inventory:
    """
    Base class for inventory items. Handles common functionalities for inventory-related operations.
    """

    cls_item_type: str = ""

    def __init__(self, name: str = "Unnamed") -> None:
        """
        Initializes the inventory item with a name and a list of fields.
        """
        self.name: str = name
        self.fields: List[str] = []

    def get_fields(self) -> None:
        """
        Prompts for every field of the item. The 'name' field is mandatory and
        fields ending in 'date' are validated and stored as YYYY-MM-DD text.
        """
        for field in self.fields:
            if field == "name":
                value = self._prompt_required(field)
            elif field.endswith("date"):
                value = self._prompt_date(field)
            else:
                value = Utils.rich_prompting(
                    f"Enter {field} of {self.cls_item_type}", tag="info"
                )
            setattr(self, field, value)

    def _prompt_required(self, field: str) -> str:
        """
        Keeps prompting until a non-empty value is entered.
        """
        while True:
            value = Utils.rich_prompting(
                f"Enter {field} of {self.cls_item_type}(cannot be empty)", tag="info"
            ).strip()
            if value:
                return value
            Utils.rich_print(
                f"Name is compulsory. Please enter the name of {self.cls_item_type}",
                tag="error",
            )

    def _prompt_date(self, field: str, date_format: str = DATE_FORMAT) -> Optional[str]:
        """
        Prompts for an optional date, re-asking until it is empty or valid.

        :return: The date as YYYY-MM-DD text, or None if left empty.
        """
        while True:
            value = Utils.rich_prompting(
                f"Enter {field} in YYYY-mm-dd format. Eg: 2014-12-14 (optional)",
                tag="info",
            ).strip()
            if not value:
                return None
            try:
                return datetime.strptime(value, date_format).strftime(DATE_FORMAT)
            except ValueError:
                Utils.rich_print(
                    "Invalid Date format. Please follow the example given.", tag="error"
                )

    def create_inventory_layout_sqlite(self, db_manager) -> None:
        """
        Function that calls create table() function of db manger to create the table

        :param db_manager: The DBManager instance for database operations.
        """
        db_manager.create_table(
            table_name=self.__class__.cls_item_type, columns=self.fields
        )

    def add_to_inventory(self, db_manager, user_name: str) -> None:
        """
        Dynamically generates the Insertion query based on the fields of item type
        and call db manager execute to execute the insertion logic.

        :param db_manager: The DBManager instance for database operations.
        :param user_name: The name of the user adding the inventory item.
        """
        values_list = [getattr(self, field) for field in self.fields]
        values_list.append(user_name)
        values = tuple(values_list)
        columns_str = ", ".join(self.fields + ["user_name"])
        placeholders = ", ".join(["?" for _ in self.fields + ["user_name"]])

        query = f"INSERT INTO {self.__class__.cls_item_type} ({columns_str}) VALUES ({placeholders})"
        try:
            db_manager.execute(query, values)
            Utils.rich_print(
                f"{self.name} ({self.cls_item_type}) successfully added to inventory.",
                tag="success",
            )
        except Exception as e:
            Utils.rich_print(f"Error adding to inventory: {e}", tag="error")


class Book(Inventory):
    """
    Represents a book item in the inventory.
    """

    cls_item_type = "book"

    def __init__(self) -> None:
        super().__init__()
        self.fields = ["name", "author", "genre", "date"]


class Magazine(Inventory):
    """
    Represents a magazine item in the inventory.
    """

    cls_item_type = "magazine"

    def __init__(self) -> None:
        super().__init__()
        self.fields = ["name", "publisher", "genre", "date"]


class Journal(Inventory):
    """
    Represents a journal item in the inventory.
    """

    cls_item_type = "journal"

    def __init__(self) -> None:
        super().__init__()
        self.fields = ["name", "author", "journal_name", "volume", "issue", "format"]


class Manga(Inventory):
    """
    Represents a manga item in the inventory.
    """

    cls_item_type = "manga"

    def __init__(self) -> None:
        super().__init__()
        self.fields = ["name", "author", "publisher", "format"]


class WesternComic(Inventory):
    """
    Represents a western comic item in the inventory.
    """

    cls_item_type = "western_comic"

    def __init__(self) -> None:
        super().__init__()
        self.fields = ["name", "author", "publisher", "format"]


class ResearchPaper(Inventory):
    """
    Represents a research paper item in the inventory.
    """

    cls_item_type = "research_paper"

    def __init__(self) -> None:
        super().__init__()
        self.fields = ["name", "author", "journal_name", "abstract", "keywords", "date"]
