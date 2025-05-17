from flask import Flask, render_template, jsonify
from datetime import datetime
import sqlite3

# SQLite connection setup
db = sqlite3.connect('finance.db', check_same_thread=False)
cursor = db.cursor()

# Create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        amount REAL,
        type TEXT,
        date TEXT,
        icon TEXT
    )
''')
db.commit()

app = Flask(__name__, template_folder='../templates', static_folder='../static')

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
        'date': '2025-05-03',
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
def index():
    totals = calculate_totals()
    return render_template('index.html', 
                         transactions=transactions,
                         totals=totals)

@app.route('/api/transactions')
def get_transactions():
    # Fetch transactions from SQLite
    cursor.execute("SELECT id, title, category, amount, type, date, icon FROM transactions ORDER BY date DESC")
    rows = cursor.fetchall()
    transactions_db = [
        {
            'id': row[0],
            'title': row[1],
            'category': row[2],
            'amount': row[3],
            'type': row[4],
            'date': row[5].strftime('%Y-%m-%d') if hasattr(row[5], 'strftime') else str(row[5]),
            'icon': row[6]
        }
        for row in rows
    ]
    return jsonify(transactions_db)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
