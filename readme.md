# DonorWare

A console application for a community library. Members donate books and other reading
material, and other members borrow and return it. Built with Python, SQLite and
[Rich](https://github.com/Textualize/rich).

## Features

- **Accounts**: register and log in. Passwords are hashed with bcrypt, must be 6-72 bytes and are confirmed on registration.
- **Donate**: books, magazines, journals, manga, western comics and research papers. Only the name is required, and dates use `YYYY-MM-DD`.
- **Search**: by category or across all categories. A term matches any field of the item, and `%` and `_` are treated literally.
- **Borrow and return**: items are lent for 7 days. You can't borrow your own donations or an item someone else has out.
- **Personal inventory**: what you donated, your full borrow history, and your current borrows ordered by due date.

## Requirements

- Python 3.9+
- A real terminal. Some IDE consoles echo password input and render Rich badly; in PyCharm enable *Run > Edit Configurations > Emulate terminal in output console*.

## Setup

```bash
git clone https://github.com/ShreyNiraula/CS521-DonorWare.git
cd CS521-DonorWare

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python3 PublicDonationInventory/main.py
```

The SQLite database `library.db` is created next to the code on first run.
Delete that file to start over.

### Walkthrough

1. **Register** a user, or log in.
2. **Add Items** and pick a type.
3. Log out, register a second user, then use **Search Items** or **Borrow Items** to borrow the first user's item.
4. Use **Return Items** and **Personal Inventory** to return it and review history.

Borrowing and returning need two users, since you can't borrow your own donations.

## Tests

```bash
python3 -m unittest discover -s tests -t .
```

The tests use an in-memory database and cover borrowing rules, search scoping,
wildcard escaping, login validation and SQL injection safety.

## Project layout

```
PublicDonationInventory/
  main.py                 entry point: database setup, auth menu, session menu
  managers.py             DBManager (SQLite access) and UserManager (register/login)
  inventory.py            Inventory base class and one subclass per item type
  transaction_manager.py  add, search, borrow, return and history logic
  utils.py                Rich helpers for coloured output and tables
tests/                    unit tests
```

### Adding a new item type

Subclass `Inventory` in `inventory.py` with a `cls_item_type` and a `fields` list,
then register it in the `item_types` dict in `main.py`. The table, prompts, search
and history views pick it up automatically. A field named `name` is mandatory and
fields ending in `date` are validated.

## Data model

| Table | Columns |
|-------|---------|
| `users` | `user_name` (PK), `password` (bcrypt hash) |
| one per item type | `id`, the type's fields, `user_name` (donor) |
| `transactions` | `id`, `user_name`, `item_type`, `item_id`, `borrow_date`, `due_date`, `return_date`, `status` (`borrowed` / `returned`) |

## Known limitations

- No renewals, overdue handling, or editing and deleting donated items.
- The borrow availability check and insert are not atomic, which is fine for a single-user CLI.
- The loan period is fixed at 7 days.
