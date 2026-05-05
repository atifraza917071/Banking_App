from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import sqlite3
import os
import hashlib

app = Flask(__name__)
app.secret_key = 'banking_secret_key_2024'
DB = 'banking.db'


# ---------- DB SETUP ----------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            account_type TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            balance_after REAL NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(account_id) REFERENCES accounts(id)
        );
    ''')
    conn.commit()
    conn.close()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def gen_account_number():
    import random
    return 'ACC' + str(random.randint(1000000000, 9999999999))


# ---------- AUTH ----------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        account_type = request.form['account_type']

        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        conn = get_db()
        try:
            c = conn.cursor()
            c.execute('INSERT INTO users (name, email, password) VALUES (?,?,?)',
                      (name, email, hash_password(password)))
            user_id = c.lastrowid
            acc_no = gen_account_number()
            c.execute('INSERT INTO accounts (user_id, account_number, account_type, balance) VALUES (?,?,?,?)',
                      (user_id, acc_no, account_type, 0.0))
            conn.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'error')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email=? AND password=?',
                            (email, hash_password(password))).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------- DASHBOARD ----------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    accounts = conn.execute('SELECT * FROM accounts WHERE user_id=?', (session['user_id'],)).fetchall()
    recent_txns = []
    for acc in accounts:
        txns = conn.execute(
            'SELECT * FROM transactions WHERE account_id=? ORDER BY timestamp DESC LIMIT 5',
            (acc['id'],)
        ).fetchall()
        recent_txns.extend(txns)
    recent_txns.sort(key=lambda x: x['timestamp'], reverse=True)
    conn.close()
    return render_template('dashboard.html', accounts=accounts, transactions=recent_txns[:10])


# ---------- DEPOSIT ----------

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    accounts = conn.execute('SELECT * FROM accounts WHERE user_id=?', (session['user_id'],)).fetchall()

    if request.method == 'POST':
        acc_id = int(request.form['account_id'])
        amount = float(request.form['amount'])
        desc = request.form.get('description', 'Deposit')

        if amount <= 0:
            flash('Amount must be positive.', 'error')
        else:
            acc = conn.execute('SELECT * FROM accounts WHERE id=? AND user_id=?',
                               (acc_id, session['user_id'])).fetchone()
            if acc:
                new_balance = acc['balance'] + amount
                conn.execute('UPDATE accounts SET balance=? WHERE id=?', (new_balance, acc_id))
                conn.execute('INSERT INTO transactions (account_id, type, amount, description, balance_after) VALUES (?,?,?,?,?)',
                             (acc_id, 'Deposit', amount, desc, new_balance))
                conn.commit()
                flash(f'₹{amount:,.2f} deposited successfully!', 'success')
                conn.close()
                return redirect(url_for('dashboard'))

    conn.close()
    return render_template('deposit.html', accounts=accounts)


# ---------- WITHDRAWAL ----------

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    accounts = conn.execute('SELECT * FROM accounts WHERE user_id=?', (session['user_id'],)).fetchall()

    if request.method == 'POST':
        acc_id = int(request.form['account_id'])
        amount = float(request.form['amount'])
        desc = request.form.get('description', 'Withdrawal')

        if amount <= 0:
            flash('Amount must be positive.', 'error')
        else:
            acc = conn.execute('SELECT * FROM accounts WHERE id=? AND user_id=?',
                               (acc_id, session['user_id'])).fetchone()
            if acc:
                if acc['balance'] < amount:
                    flash('Insufficient balance.', 'error')
                else:
                    new_balance = acc['balance'] - amount
                    conn.execute('UPDATE accounts SET balance=? WHERE id=?', (new_balance, acc_id))
                    conn.execute('INSERT INTO transactions (account_id, type, amount, description, balance_after) VALUES (?,?,?,?,?)',
                                 (acc_id, 'Withdrawal', amount, desc, new_balance))
                    conn.commit()
                    flash(f'₹{amount:,.2f} withdrawn successfully!', 'success')
                    conn.close()
                    return redirect(url_for('dashboard'))

    conn.close()
    return render_template('withdraw.html', accounts=accounts)


# ---------- TRANSFER ----------

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    accounts = conn.execute('SELECT * FROM accounts WHERE user_id=?', (session['user_id'],)).fetchall()

    if request.method == 'POST':
        from_id = int(request.form['from_account'])
        to_acc_no = request.form['to_account_number'].strip()
        amount = float(request.form['amount'])
        desc = request.form.get('description', 'Transfer')

        from_acc = conn.execute('SELECT * FROM accounts WHERE id=? AND user_id=?',
                                (from_id, session['user_id'])).fetchone()
        to_acc = conn.execute('SELECT * FROM accounts WHERE account_number=?', (to_acc_no,)).fetchone()

        if not to_acc:
            flash('Destination account not found.', 'error')
        elif from_acc['id'] == to_acc['id']:
            flash('Cannot transfer to the same account.', 'error')
        elif amount <= 0:
            flash('Amount must be positive.', 'error')
        elif from_acc['balance'] < amount:
            flash('Insufficient balance.', 'error')
        else:
            new_from = from_acc['balance'] - amount
            new_to = to_acc['balance'] + amount
            conn.execute('UPDATE accounts SET balance=? WHERE id=?', (new_from, from_acc['id']))
            conn.execute('UPDATE accounts SET balance=? WHERE id=?', (new_to, to_acc['id']))
            conn.execute('INSERT INTO transactions (account_id, type, amount, description, balance_after) VALUES (?,?,?,?,?)',
                         (from_acc['id'], 'Transfer Out', amount, f'{desc} → {to_acc_no}', new_from))
            conn.execute('INSERT INTO transactions (account_id, type, amount, description, balance_after) VALUES (?,?,?,?,?)',
                         (to_acc['id'], 'Transfer In', amount, f'{desc} ← {from_acc["account_number"]}', new_to))
            conn.commit()
            flash(f'₹{amount:,.2f} transferred successfully!', 'success')
            conn.close()
            return redirect(url_for('dashboard'))

    conn.close()
    return render_template('transfer.html', accounts=accounts)


# ---------- TRANSACTION HISTORY ----------

@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    accounts = conn.execute('SELECT * FROM accounts WHERE user_id=?', (session['user_id'],)).fetchall()
    acc_id = request.args.get('account_id')
    all_txns = []
    selected = None
    for acc in accounts:
        if acc_id and str(acc['id']) == acc_id:
            selected = acc
        txns = conn.execute(
            'SELECT t.*, a.account_number FROM transactions t JOIN accounts a ON t.account_id=a.id WHERE t.account_id=? ORDER BY t.timestamp DESC',
            (acc['id'],)
        ).fetchall()
        if not acc_id or str(acc['id']) == acc_id:
            all_txns.extend(txns)

    all_txns.sort(key=lambda x: x['timestamp'], reverse=True)
    conn.close()
    return render_template('transactions.html', transactions=all_txns, accounts=accounts, selected=selected)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
