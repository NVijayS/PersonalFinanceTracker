# Import necessary modules from Flask and standard libraries
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import sqlite3
import os

# SQLite connection setup (single connection for the app)
db = sqlite3.connect('finance.db', check_same_thread=False)
cursor = db.cursor()

# Create tables if they don't exist
# Users table: stores user credentials and info
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        Uid INTEGER PRIMARY KEY AUTOINCREMENT,
        Uname TEXT NOT NULL UNIQUE,
        Uemail TEXT NOT NULL UNIQUE,
        Upass TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
''')
# Categories table: stores income/expense categories
cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        Catid INTEGER PRIMARY KEY AUTOINCREMENT,
        Catname TEXT NOT NULL,
        Cattype TEXT NOT NULL CHECK (Cattype IN ('income', 'expense'))
    );
''')
# Transactions table: stores all user transactions
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
# Budgets table: stores user budgets per category/month/year
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
# Alerts table: stores user alerts/notifications
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
# Commit table creation
db.commit()

# Initialize Flask app with custom template and static folders
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '../templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '../static')
)

# Helper function to fetch all transactions from the database
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
    # Build a list of transaction dictionaries
    transactions = [
        {
            'id': row[0],
            'title': row[1],
            'category': row[2],
            'amount': row[3],
            'type': row[4],
            'date': row[5],
            'icon': row[6]  # Placeholder for icon logic
        }
        for row in rows
    ]
    return transactions

# Helper function to calculate total income, expenses, and balance
def calculate_totals(transactions):
    income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    return {
        'income': income,
        'expenses': expenses,
        'balance': income - expenses
    }

# Helper function to fetch all categories, grouped by type
def fetch_categories():
    cursor.execute("SELECT Catname, Cattype FROM categories")
    rows = cursor.fetchall()
    income_categories = [row[0] for row in rows if row[1] == 'income']
    expense_categories = [row[0] for row in rows if row[1] == 'expense']
    all_categories = [row[0] for row in rows]
    return income_categories, expense_categories, all_categories

# Home page route (dashboard)
@app.route('/')
def index():
    # Redirect to login if user not logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    transactions = fetch_transactions()
    totals = calculate_totals(transactions)
    income_categories, expense_categories, all_categories = fetch_categories()
    # Render dashboard template with data
    return render_template('dashboard.html', 
                         transactions=transactions,
                         totals=totals,
                         username=session.get('username'),
                         income_categories=income_categories,
                         expense_categories=expense_categories,
                         categories=all_categories)

# Dashboard page route (duplicate of index for direct access)
@app.route('/dashboard')
def dashboard_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    transactions = fetch_transactions()
    totals = calculate_totals(transactions)
    income_categories, expense_categories, all_categories = fetch_categories()
    return render_template('dashboard.html', 
                         transactions=transactions,
                         totals=totals,
                         username=session.get('username'),
                         income_categories=income_categories,
                         expense_categories=expense_categories,
                         categories=all_categories)

# Transactions page route
@app.route('/transactions')
def transactions_page():
    transactions = fetch_transactions()
    income_categories, expense_categories, all_categories = fetch_categories()
    return render_template(
        'transactions.html',
        transactions=transactions,
        income_categories=income_categories,
        expense_categories=expense_categories,
        categories=all_categories
    )

# Budget page route
@app.route('/budget')
def budget_page():
    # Fetch budgets and calculate spent/received from transactions for the current user (replace 1 with session['user_id'] as needed)
    cursor.execute("""
        SELECT 
            c.Catname, 
            c.Cattype, 
            b.month, 
            b.year, 
            b.amount,
            (
                SELECT IFNULL(SUM(t.amount), 0)
                FROM transactions t
                WHERE t.Catid = b.Catid
                  AND t.type = 'expense'
                  AND strftime('%m', t.date) = printf('%02d', b.month)
                  AND strftime('%Y', t.date) = CAST(b.year AS TEXT)
                  AND t.Uid = b.Uid
            ) as spent,
            (
                SELECT IFNULL(SUM(t.amount), 0)
                FROM transactions t
                WHERE t.Catid = b.Catid
                  AND t.type = 'income'
                  AND strftime('%m', t.date) = printf('%02d', b.month)
                  AND strftime('%Y', t.date) = CAST(b.year AS TEXT)
                  AND t.Uid = b.Uid
            ) as received
        FROM budgets b
        JOIN categories c ON b.Catid = c.Catid
        WHERE b.Uid = ?
        ORDER BY b.year DESC, b.month DESC, c.Cattype, c.Catname
    """, (1,))  # Replace 1 with session['user_id'] for real users
    budgets = [
        {
            'category': row[0],
            'type': row[1],
            'month': row[2],
            'year': row[3],
            'amount': row[4],
            'spent': row[5],
            'received': row[6]
        }
        for row in cursor.fetchall()
    ]
    income_categories, expense_categories, all_categories = fetch_categories()
    import datetime
    current_year = datetime.datetime.now().year
    return render_template(
        'budget.html',
        budgets=budgets,
        categories=all_categories,
        income_categories=income_categories,
        expense_categories=expense_categories,
        current_year=current_year
    )

# Route to add a new transaction
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    title = request.form['title']
    amount = float(request.form['amount'])
    ttype = request.form['type']
    category_name = request.form['category']
    date = request.form['date']

    # Get Catid from categories table, or create if not exists
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
    # Redirect to dashboard so summary is updated immediately
    return redirect(url_for('dashboard_page'))

# Route to delete a transaction by ID
@app.route('/delete_transaction/<int:tid>', methods=['POST'])
def delete_transaction(tid):
    cursor.execute("DELETE FROM transactions WHERE Tid = ?", (tid,))
    db.commit()
    # Redirect to dashboard so summary is updated immediately
    return redirect(url_for('dashboard_page'))

# Route to add a new budget
@app.route('/add_budget', methods=['POST'])
def add_budget():
    category_name = request.form['budget_category']
    budget_type = request.form['budget_type']
    month = int(request.form['budget_month'])
    year = int(request.form['budget_year'])
    amount = float(request.form['budget_amount'])
    # Get Catid from categories table, or create if not exists
    cursor.execute("SELECT Catid FROM categories WHERE Catname = ? AND Cattype = ?", (category_name, budget_type))
    cat_row = cursor.fetchone()
    if cat_row:
        catid = cat_row[0]
    else:
        cursor.execute("INSERT INTO categories (Catname, Cattype) VALUES (?, ?)", (category_name, budget_type))
        db.commit()
        catid = cursor.lastrowid
    # For demo, use Uid=1 (update for real users)
    cursor.execute(
        "INSERT INTO budgets (Uid, Catid, month, year, amount) VALUES (?, ?, ?, ?, ?)",
        (1, catid, month, year, amount)
    )
    db.commit()
    return redirect(url_for('budget_page'))

# Login route (GET and POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute('SELECT Uid, Uname, Upass FROM users WHERE Uname = ?', (username,))
        user = cursor.fetchone()
        # Check if user exists and password matches
        if user and user[2] == password:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', login_bg='loginbg.jpg')

# Registration route (GET and POST)
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

# Profile page route (GET and POST)
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

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Scholarships and loans info page
@app.route('/scholarships-loans')
def scholarships_loans():
    return render_template('scholarships.html')

# Financial learning resources page
@app.route('/financial-learning')
def financial_learning():
    return render_template('financial-learning.html')

# Before each request, require login for protected routes
@app.before_request
def require_login():
    allowed_routes = {'login', 'register', 'static'}
    # Allow static files and favicon.ico
    if request.endpoint is None:
        return
    if (request.endpoint not in allowed_routes and not request.endpoint.startswith('static')) and 'user_id' not in session:
        return redirect(url_for('login'))

# Set a secret key for sessions (should be random and secure in production)
app.secret_key = 'your-secret-key-here'  # In production, use a secure random key

# Route to add a new category
@app.route('/add_category', methods=['POST'])
def add_category():
    category_name = request.form['category_name']
    category_type = request.form['category_type']
    # Prevent duplicate categories
    cursor.execute("SELECT 1 FROM categories WHERE Catname = ? AND Cattype = ?", (category_name, category_type))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO categories (Catname, Cattype) VALUES (?, ?)", (category_name, category_type))
        db.commit()
    return redirect(url_for('transactions_page'))

# FAQ page route
@app.route('/faq')
def faq_page():
    return render_template('faq.html')

# Run the Flask app if this file is executed directly
if __name__ == '__main__':
    app.run(debug=True, port=5000)
