import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "PublicDonationInventory"))

from main import item_types  # noqa: E402
from managers import DBManager, UserManager  # noqa: E402
from transaction_manager import TransactionManager  # noqa: E402


class TransactionTestCase(unittest.TestCase):
    def setUp(self):
        self.db = DBManager(":memory:")
        self.db.setup_transactions_table()
        self.db.create_users_table()
        for cls in item_types.values():
            cls().create_inventory_layout_sqlite(self.db)
        self.db.execute(
            "INSERT INTO book (name, author, user_name) VALUES ('Dune', 'Herbert', 'alice')"
        )
        self.db.execute(
            "INSERT INTO book (name, author, user_name) VALUES ('Emma', 'Austen', 'bob')"
        )
        self.alice = TransactionManager(self.db, "alice", item_types)
        self.bob = TransactionManager(self.db, "bob", item_types)

    def tearDown(self):
        self.db.close()

    def active_borrows(self, manager):
        return manager.get_transaction_history(is_active=True)[1]


class BorrowTests(TransactionTestCase):
    def test_borrow_and_return(self):
        self.bob.borrow_item("book", 1)
        self.assertEqual(len(self.active_borrows(self.bob)), 1)
        self.bob.return_item(1)
        self.assertEqual(self.active_borrows(self.bob), [])

    def test_cannot_borrow_own_item(self):
        self.alice.borrow_item("book", 1)
        self.assertEqual(self.active_borrows(self.alice), [])

    def test_cannot_borrow_unknown_category_or_item(self):
        self.bob.borrow_item("potion", 1)
        self.bob.borrow_item("book", 99)
        self.assertEqual(self.active_borrows(self.bob), [])

    def test_cannot_borrow_item_already_borrowed(self):
        self.bob.borrow_item("book", 1)
        TransactionManager(self.db, "carol", item_types).borrow_item("book", 1)
        rows = self.db.fetchall("SELECT user_name FROM transactions")
        self.assertEqual(rows, [("bob",)])

    def test_cannot_return_someone_elses_borrow(self):
        self.bob.borrow_item("book", 1)
        self.alice.return_item(1)
        self.assertEqual(len(self.active_borrows(self.bob)), 1)


class SearchTests(TransactionTestCase):
    def test_search_matches_any_field(self):
        _, rows = self.alice.search_with_auto_complete(item_types["1"](), "Austen")
        self.assertEqual(len(rows), 1)

    def test_wildcards_are_literal(self):
        _, rows = self.alice.search_with_auto_complete(item_types["1"](), "%")
        self.assertEqual(rows, [])

    def test_return_search_is_scoped_to_user_and_status(self):
        self.bob.borrow_item("book", 1)
        _, rows = self.alice.get_borrowed_given_item(item_types["1"](), "Dune")
        self.assertEqual(rows, [])
        _, rows = self.bob.get_borrowed_given_item(item_types["1"](), "Dune")
        self.assertEqual(len(rows), 1)

    def test_search_every_type(self):
        _, rows = self.alice.search_for_every_item_type("Dune")
        self.assertEqual(len(rows), 1)


class InjectionTests(TransactionTestCase):
    def test_crafted_username_sees_nothing(self):
        attacker = TransactionManager(self.db, "x' OR '1'='1", item_types)
        self.assertEqual(attacker.get_items_added_by_user()[1], [])
        self.assertEqual(attacker.get_transaction_history(False)[1], [])


class UserTests(unittest.TestCase):
    def setUp(self):
        self.db = DBManager(":memory:")
        self.db.create_users_table()

    def tearDown(self):
        self.db.close()

    def make(self, name, password):
        manager = UserManager(self.db)
        manager.user_name, manager.password = name, password
        return manager

    def test_register_then_login(self):
        self.assertTrue(self.make("alice", "secret1").validate_credentials() is None)
        self.db.execute(
            "INSERT INTO users VALUES (?, ?)",
            ("alice", UserManager.hash_password("secret1")),
        )
        self.assertTrue(self.make("alice", "secret1").login())
        self.assertFalse(self.make("alice", "wrong").login())
        self.assertFalse(self.make("nobody", "secret1").login())

    def test_rejects_empty_credentials(self):
        self.assertFalse(self.make("  ", "secret1").login())
        self.assertFalse(self.make("alice", "").login())


if __name__ == "__main__":
    unittest.main()
