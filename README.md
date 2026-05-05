# BankFlow — Banking Transaction Management System

> A full-stack web application built with Python (Flask) and SQLite for managing banking operations including account creation, deposits, withdrawals, and fund transfers.

---

## Resume Description (copy-paste ready)

**Banking Transaction Management System** | Python, Flask, SQLite, HTML/CSS
- Developed a full-stack banking web application using Flask (Python) with session-based user authentication and SHA-256 password hashing
- Designed a normalized SQLite relational database with 3 tables (users, accounts, transactions) supporting complete CRUD operations
- Implemented core banking features: account creation, deposits, withdrawals, and inter-account fund transfers with real-time balance updates
- Built a responsive multi-page UI using Jinja2 templating with transaction history filtering and live account balance tracking
- Applied MVC architecture separating routing, business logic, and HTML templates for clean, maintainable code

---

## Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Backend    | Python 3, Flask         |
| Database   | SQLite3 (built-in)      |
| Frontend   | HTML5, CSS3, Jinja2     |
| Auth       | SHA-256 password hashing, Flask sessions |
| ORM        | Raw SQL via sqlite3 module |

---

## Features

- User Registration & Login (hashed passwords, session management)
- Account types: Savings, Current, Salary
- Deposit funds with description
- Withdraw with balance validation
- Transfer between accounts (with account number lookup)
- Full transaction history with type-based filtering
- Live balance dashboard with multi-account support

---

## Project Structure

```
banking_app/
├── app.py                  # Main Flask app (routes + DB logic)
├── banking.db              # SQLite database (auto-created)
├── requirements.txt
└── templates/
    ├── base.html           # Shared layout & navbar
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── deposit.html
    ├── withdraw.html
    ├── transfer.html
    └── transactions.html
```

---

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
http://127.0.0.1:5000
```

No extra setup needed — the SQLite database is created automatically on first run.

---

## Database Schema

```sql
users       (id, name, email, password, created_at)
accounts    (id, user_id, account_number, account_type, balance, created_at)
transactions(id, account_id, type, amount, description, balance_after, timestamp)
```
