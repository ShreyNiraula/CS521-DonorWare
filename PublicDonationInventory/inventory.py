from datetime import datetime
from typing import List
from utils import Utils


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
        Function that calls create table() function of db manger to create the table
        """

        # loop through fields to prompt for values
        for field in self.fields:
            # handle mandatory name fields
            if "name" in field:
                while True:
                    value = Utils.rich_prompting(
                        f"Enter {field} of {self.cls_item_type}(cannot be empty)",
                        tag="info",
                    )
                    if value.strip():  # make sure that field is not empty
                        break
                    else:
                        Utils.rich_print(
                            f"Name is compulsory. Please enter the name of {self.cls_item_type}",
                            tag="error",
                        )

            # handle other fields
            else:
                value = Utils.rich_prompting(
                    f"Enter {field} of {self.cls_item_type}", tag="info"
                )

            # set the attribute for the field
            setattr(self, field, value)

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

    def get_date_with_fields(self, date_format: str = "%Y-%m-%d") -> None:
        """
        Similar to get fields() function with customized date handling.
        Child class overrides the get fields() function
            by calling this function if date related field is present in its attributes

        :param date_format: The expected date format for input.
        """
        date_format_mapper = {
            "%Y-%m-%d": "YYYY-mm-dd format. Eg: 2014-12-14",
            "%Y": "YYYY (year only). Eg: 2014.",
        }

        # loop through fields to prompt for values
        for field in self.fields:
            # handle mandatory name fields
            if "name" in field:
                while True:
                    value = Utils.rich_prompting(
                        f"Enter {field} of {self.cls_item_type}(cannot be empty)",
                        tag="info",
                    )
                    if value.strip():  # make sure that field is not empty
                        break
                    else:
                        Utils.rich_print(
                            f"Name is compulsory. Please enter the name of {self.cls_item_type}",
                            tag="error",
                        )

            # handle date field
            elif "date" in field:
                while True:
                    try:
                        value = Utils.rich_prompting(
                            f"Enter {field} in {date_format_mapper[date_format]}",
                            tag="info",
                        )
                        if value.strip():  # make sure that field is not empty
                            value = datetime.strptime(value, date_format).date()
                        else:
                            value = None
                        break
                    except ValueError:
                        Utils.rich_print(
                            f"Invalid Date format. Please follow the example given.",
                            tag="error",
                        )

            # handle other fields
            else:
                value = Utils.rich_prompting(
                    f"Enter {field} of {self.cls_item_type}", tag="info"
                )

            # set the attribute for the field
            setattr(self, field, value)


class Book(Inventory):
    """
    Represents a book item in the inventory.
    """

    cls_item_type = "book"

    def __init__(self) -> None:
        super().__init__()
        self.fields = ["name", "author", "genre", "date"]

    def get_fields(self) -> None:
        self.get_date_with_fields()


class Magazine(Inventory):
    """
    Represents a magazine item in the inventory.
    """

    cls_item_type = "magazine"

    def __init__(self) -> None:
        super().__init__()
        self.fields = ["name", "publisher", "genre", "date"]

    def get_fields(self) -> None:
        self.get_date_with_fields()


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

    def get_fields(self) -> None:
        self.get_date_with_fields()
