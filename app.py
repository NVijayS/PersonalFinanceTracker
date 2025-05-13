from flask import Flask, render_template, jsonify
from datetime import datetime

app = Flask(__name__, 
            static_folder='../static',
            template_folder='../templates')

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
    return jsonify(transactions)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
