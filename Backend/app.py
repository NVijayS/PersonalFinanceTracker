from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import sqlite3
import os

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
        type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
        Catid INTEGER,
        Description TEXT,
        date TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Uid) REFERENCES users(Uid) ON DELETE CASCADE,
        FOREIGN KEY (Catid) REFERENCES categories(Catid)
    );
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS budgets (
        Bid INTEGER PRIMARY KEY AUTOINCREMENT,
        Uid INTEGER NOT NULL,
        Catid INTEGER NOT NULL,
        month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
        year INTEGER NOT NULL,
        amount REAL NOT NULL,
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

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '../templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '../static')
)

# Helper functions
def fetch_transactions():
    cursor.execute("""
        SELECT 
            t.Tid, 
            t.Description, 
            c.Catname, 
            t.amount, 
            t.type, 
            t.date, 
            NULL as icon
        FROM transactions t
        LEFT JOIN categories c ON t.Catid = c.Catid
        ORDER BY t.date DESC
    """)
    rows = cursor.fetchall()
    transactions = [
        {
            'id': row[0],
            'title': row[1],
            'category': row[2],
            'amount': row[3],
            'type': row[4],
            'date': row[5],
            'icon': row[6]  # You can add logic for icons if needed
        }
        for row in rows
    ]
    return transactions

def calculate_totals(transactions):
    income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    return {
        'income': income,
        'expenses': expenses,
        'balance': income - expenses
    }

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    transactions = fetch_transactions()
    totals = calculate_totals(transactions)
    return render_template('dashboard.html', 
                         transactions=transactions,
                         totals=totals,
                         username=session.get('username'))

@app.route('/dashboard')
def dashboard_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    transactions = fetch_transactions()
    totals = calculate_totals(transactions)
    return render_template('dashboard.html', 
                         transactions=transactions,
                         totals=totals,
                         username=session.get('username'))

@app.route('/api/transactions')
def get_transactions():
    transactions = fetch_transactions()
    return jsonify(transactions)

@app.route('/transactions')
def transactions_page():
    transactions = fetch_transactions()
    cursor.execute("SELECT Catname FROM categories")
    categories = [row[0] for row in cursor.fetchall()]
    return render_template('transactions.html', transactions=transactions, categories=categories)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    title = request.form['title']
    amount = float(request.form['amount'])
    ttype = request.form['type']
    category_name = request.form['category']
    date = request.form['date']

    # Get Catid from categories table
    cursor.execute("SELECT Catid FROM categories WHERE Catname = ?", (category_name,))
    cat_row = cursor.fetchone()
    if cat_row:
        catid = cat_row[0]
    else:
        cursor.execute("INSERT INTO categories (Catname, Cattype) VALUES (?, ?)", (category_name, ttype))
        db.commit()
        catid = cursor.lastrowid

    # For demo, use Uid=1 (update for real users)
    cursor.execute(
        "INSERT INTO transactions (Uid, amount, type, Catid, Description, date) VALUES (?, ?, ?, ?, ?, ?)",
        (1, amount, ttype, catid, title, date)
    )
    db.commit()
    return redirect(url_for('transactions_page'))

@app.route('/delete_transaction/<int:tid>', methods=['POST'])
def delete_transaction(tid):
    cursor.execute("DELETE FROM transactions WHERE Tid = ?", (tid,))
    db.commit()
    return redirect(url_for('transactions_page'))

@app.route('/budget')
def budget_page():
    budgets = [
        {
            'category': 'Food',
            'month': 5,
            'year': 2025,
            'amount': 300,
            'spent': 120
        },
        # ... more budgets ...
    ]
    return render_template('budget.html', budgets=budgets)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute('SELECT Uid, Uname, Upass FROM users WHERE Uname = ?', (username,))
        user = cursor.fetchone()
        if user and user[2] == password:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', login_bg='loginbg.jpg')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        try:
            cursor.execute('INSERT INTO users (Uname, Uemail, Upass) VALUES (?, ?, ?)', 
                         (username, email, password))
            db.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
    return render_template('register.html', register_bg='registerbg.jpg')

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

@app.route('/scholarships-loans')
def scholarships_loans():
    return render_template('scholarships.html')

@app.before_request
def require_login():
    allowed_routes = {'login', 'register', 'static'}
    # Allow static files and favicon.ico
    if request.endpoint is None:
        return
    if (request.endpoint not in allowed_routes and not request.endpoint.startswith('static')) and 'user_id' not in session:
        return redirect(url_for('login'))

# Set a secret key for sessions
app.secret_key = 'your-secret-key-here'  # In production, use a secure random key

if __name__ == '__main__':
    app.run(debug=True, port=5000)
