from flask import Flask, render_template, jsonify
import sqlite3

# SQLite connection setup
db = sqlite3.connect('finance.db', check_same_thread=False)
cursor = db.cursor()

# ... your table creation code here ...
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


app = Flask(__name__, template_folder='../templates', static_folder='../static')

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

@app.route('/')
def index():
    transactions = fetch_transactions()
    totals = calculate_totals(transactions)
    return render_template('index.html', 
                         transactions=transactions,
                         totals=totals)

@app.route('/api/transactions')
def get_transactions():
    transactions = fetch_transactions()
    return jsonify(transactions)

@app.route('/transactions')
def transactions_page():
    transactions = fetch_transactions()
    return render_template('transactions.html', transactions=transactions)

if __name__ == '__main__':
    app.run(debug=True, port=5000)