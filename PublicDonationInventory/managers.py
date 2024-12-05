from getpass import getpass
import bcrypt

import sqlite3
from typing import List, Tuple, Optional
from utils import Utils


class DBManager:
    """
    Handles database operations such as table creation, data insertion, querying, and connection management.
    """

    def __init__(self, db_name: str = "library.db") -> None:
        """
        Initializes the database connection.

        :param db_name: Name of the SQLite database file.
        """
        self.db_name: str = db_name
        self.connection: sqlite3.Connection = sqlite3.connect(self.db_name)
        self.cursor: sqlite3.Cursor = self.connection.cursor()

    def create_users_table(self) -> None:
        """
        Creates the 'users' table if it doesn't already exist.
        """
        try:
            query = """
            CREATE TABLE IF NOT EXISTS users (
                user_name TEXT PRIMARY KEY,
                password TEXT
            )
            """
            self.cursor.execute(query)
            self.connection.commit()
        except sqlite3.Error as e:
            Utils.rich_print(f"Error setting up users table: {e}", tag="error")

    def create_table(self, table_name: str, columns: List[str]) -> None:
        """
            Dynamic table creation logic to create the table based on table
            name and columns passed. ’users’ table, and corresponding tables
            from the available item types (eg: books, magazine, journal tables
            etc) are created

        :param table_name: Name of the table to create.
        :param columns: List of column names.
        """
        try:
            has_user_column = "user_name" in columns
            columns_str = "id INTEGER PRIMARY KEY AUTOINCREMENT, " + ", ".join(
                [f"{col} TEXT" for col in columns if col != "id"]
            )
            if not has_user_column:
                columns_str += ", user_name TEXT"

            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
            self.cursor.execute(query)
            self.connection.commit()
        except sqlite3.Error as e:
            Utils.rich_print(f"Error creating table {table_name}: {e}", tag="error")

    def setup_transactions_table(self) -> None:
        """
        Creates ’transaction’ table if it has not been created.
        """
        try:
            query = """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                item_type TEXT,
                item_id INTEGER,
                borrow_date TEXT,
                due_date TEXT,
                return_date TEXT,
                status TEXT
            )
            """
            self.cursor.execute(query)
            self.connection.commit()
        except sqlite3.Error as e:
            Utils.rich_print(f"Error setting up transactions table: {e}", tag="error")

    def execute(self, query: str, params: Tuple = ()) -> None:
        """
        Executes a query being passed. Runs create, insert and delete logics

        :param query: The SQL query string.
        :param params: A tuple of parameters for the query.
        """
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except sqlite3.Error as e:
            Utils.rich_print(f"Error executing query: {e}", tag="error")
            raise

    def fetchall(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """
        Executes a query to fetch all results matching the given parameters

        :param query: The SQL SELECT query string.
        :param params: A tuple of parameters for the query.
        :return: A list of tuples containing query results.
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            Utils.rich_print(f"Error fetching data: {e}", tag="error")
            return []

    def close(self) -> None:
        """
        Closes the database connection.
        """
        self.connection.close()


class UserManager:
    """
    Manages user-related operations such as registration, login, and database interaction.
    """

    def __init__(self, db_manager: "DBManager") -> None:
        """
        Initialize UserManager with required fields and database manager.

        :param db_manager: An instance of DBManager for database operations.
        """
        self.fields: List[str] = ["user_name", "password"]
        self.db_manager: "DBManager" = db_manager
        self.user_name: Optional[str] = None
        self.password: Optional[str] = None

    def get_fields(self) -> None:
        """
        Prompts the user for login/register credentials defined in the fields.
        For password, getpass library is used to hide visibility when typing a password
        """
        for field in self.fields:
            value = (
                getpass(f"Enter {field}: ")
                if field == "password"
                else input(f"Enter {field}: ")
            )
            setattr(self, field, value)

    def create_inventory_layout_sqlite(self) -> None:
        """
         Connector function with db manager to create the users table
        """
        self.db_manager.create_users_table()

    def register(self) -> None:
        """
        Prepares query to register the user using db manager execute function.
        Password is hashed while storing in database
        """
        try:
            hashed_password = self.hash_password(self.password)
            self.db_manager.execute(
                "INSERT INTO users (user_name, password) VALUES (?, ?)",
                (self.user_name, hashed_password),
            )
            Utils.rich_print(
                f"User '{self.user_name}' registered successfully!", tag="success"
            )
        except Exception as e:
            Utils.rich_print(f"User '{self.user_name}' already exist.", tag="error")
            raise

    def login(self) -> bool:
        """
        Prepares the query to check if the current users exists and set the current user to logged in user

        :return: True if login is successful, False otherwise.
        """
        user = self.db_manager.fetchall(
            "SELECT password FROM users WHERE user_name = ?", (self.user_name,)
        )
        if user:
            stored_hash = user[0][0]
            if bcrypt.checkpw(self.password.encode("utf-8"), stored_hash):
                Utils.rich_print(f"Welcome back, {self.user_name}!", tag="success")
                return True

        Utils.rich_print("Invalid user_name or password.", tag="error")
        return False

    @staticmethod
    def hash_password(password: str) -> bytes:
        """
        Hashes a password using bcrypt.

        :param password: The plain-text password to hash.
        :return: The hashed password as bytes.
        """
        hashing = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), hashing)
        return hashed_password
