from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from functools import wraps

# SQLite connection setup
db = sqlite3.connect('finance.db', check_same_thread=False)
cursor = db.cursor()

# Create tables if they don't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        Uid INTEGER PRIMARY KEY AUTOINCREMENT,
        Uname TEXT NOT NULL UNIQUE,
        Uemail TEXT NOT NULL UNIQUE,
        Upass TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
    Catid INTEGER PRIMARY KEY AUTOINCREMENT,
    Catname TEXT NOT NULL,
    Cattype TEXT NOT NULL CHECK (Cattype IN ('income', 'expense'))
);
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
    Tid INTEGER PRIMARY KEY AUTOINCREMENT,
    Uid INTEGER NOT NULL,
    amount REAL NOT NULL,
    Catid INTEGER,
    Description TEXT,
    date TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Uid) REFERENCES users(Uid) ON DELETE CASCADE,
    FOREIGN KEY (Catid) REFERENCES categories(Catid)
);
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
    Aid INTEGER PRIMARY KEY AUTOINCREMENT,
    Uid INTEGER NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Uid) REFERENCES users(Uid) ON DELETE CASCADE
);
''')

db.commit()

app = Flask(__name__)

# Sample data - in a real app, this would come from a database 
transactions = [
    {
        'id': 1,
        'title': 'Monthly Allowance',
        'category': 'Income',
        'amount': 1000,
        'type': 'income',
        'date': '2025-05-01',
        'icon': 'money-bill-wave'
    },
    {
        'id': 2,
        'title': 'Grocery Shopping',
        'category': 'Food',
        'amount': 150,
        'type': 'expense',
        'icon': 'shopping-basket'
    },
    {
        'id': 3,
        'title': 'Textbooks',
        'category': 'Education',
        'amount': 200,
        'type': 'expense',
        'date': '2025-05-05',
        'icon': 'book'
    },
    {
        'id': 4,
        'title': 'Part-time Job',
        'category': 'Income',
        'amount': 500,
        'type': 'income',
        'date': '2025-05-10',
        'icon': 'briefcase'
    },
    {
        'id': 5,
        'title': 'Dining Out',
        'category': 'Food',
        'amount': 75,
        'type': 'expense',
        'date': '2025-05-11',
        'icon': 'utensils'
    }
]

def calculate_totals():
    income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    return {
        'income': income,
        'expenses': expenses,
        'balance': income - expenses
    }

@app.route('/')
@app.route('/index1')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    totals = calculate_totals()
    return render_template('index1.html', 
                         transactions=get_sample_transactions(),
                         totals=totals,
                         username=session.get('username'))

def get_sample_transactions():
    return transactions

@app.route('/api/transactions')
def get_transactions():
    return jsonify(get_sample_transactions())

@app.route('/scholarships-loans')
def scholarships_loans():
    return render_template('scholarships.html')

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('images/favicon.ico')

@app.route('/transactions')
def show_transactions():
    return render_template('index1.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor.execute('SELECT Uid, Uname, Upass FROM users WHERE Uname = ?', (username,))
        user = cursor.fetchone()
        
        if user and user[2] == password:  # In production, use proper password hashing
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        try:
            cursor.execute('INSERT INTO users (Uname, Uemail, Upass) VALUES (?, ?, ?)', 
                         (username, email, password))  # In production, hash the password
            db.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        try:
            cursor.execute('UPDATE users SET Uname = ?, Uemail = ? WHERE Uid = ?', (new_username, new_email, session['user_id']))
            db.commit()
            session['username'] = new_username
            flash('Profile updated successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
    
    cursor.execute('SELECT Uname, Uemail FROM users WHERE Uid = ?', (session['user_id'],))
    user = cursor.fetchone()
    return render_template('profile.html', username=user[0], email=user[1])

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Set a secret key for sessions
app.secret_key = 'your-secret-key-here'  # In production, use a secure random key

if __name__ == '__main__':
    app.run(debug=True, port=5000)
