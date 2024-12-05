# DonorWare: Book Management System

DonorWare is a Python-based warehouse management system designed to facilitate the donation, organization, and sharing of literary resources. It provides a console-based interface for users to manage books, magazines, journals, and other informational items.

## Features

- **User Management**:
  - Register and log in to access features.
  - Maintain a personal inventory of contributions and borrowings.

- **Donation Management**:
  - Add items to the inventory by type:
    - Books
    - Magazines
    - Journals
    - Manga
    - Western Comics
    - Research Papers

- **Search Functionality**:
  - Search items by category or globally.
  - Use filters to refine searches by item attributes.

- **Borrow and Return**:
  - Borrow items from the inventory.
  - Return borrowed items seamlessly.

- **Personal Inventory**:
  - View contributions.
  - Track transaction history.
  - Monitor currently borrowed items with due dates.

## How To:

1. Clone the repository:
   ```bash
   git clone https://github.com/ShreyNiraula/CS521-DonorWare.git

2. Navigate to project directory
    ```bash
   cd CS521-DonorWare

3. Create the virtual environment
    ```bash
    python3 -m venv <name_of_virutalenv>

    For mac/linux: source <name_of_virutalenv>/bin/activate

4. In Virtual environment, pip install requirements as:
   ```bash
    pip install -r requirements.txt

5. Run the application:
    ```bash
   python main.py
   

## Once the application is running, follow These Steps:
1. **Register** with a `user_name` and `password`.
2. Use the **Add Items** option to add any item you want.
3. You can **Search**, **Borrow**, and **Return** items.
4. Visit your **Personal Inventory** to:
   - View contributions.
   - Check transaction history.
   - Monitor active borrowings.

## Note:
- some of terminal may not support the rich console UI. Do these steps:
  - for Pycharm: Go to Run -> Edit Configuration -> Emulate the console environment


