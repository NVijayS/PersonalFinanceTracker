from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash


app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'Darshan'  # Replace with your MySQL username
app.config['MYSQL_PASSWORD'] = 'DARs@2906'  # Replace with your MySQL password
app.config['MYSQL_DB'] = 'FINANCE'  # Replace with your database name

# Initialize MySQL
mysql = MySQL(app)

# Root route
@app.route('/')
def home():
    return "✅ Finance Tracker API Connected with MySQL!"

# Register new user
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    uname = data.get('username')
    email = data.get('email')
    hashed_password = generate_password_hash(password)


    conn = mysql.connection
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO USERS (Uname, Uemail, Upass) VALUES (%s, %s, %s)",
            (uname, email, password)
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()

# Get all users
@app.route('/users', methods=['GET'])
def get_users():
    conn = mysql.connection
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT Uid, Uname, Uemail, created_at FROM USERS")
    users = cursor.fetchall()
    cursor.close()

    return jsonify(users)

if __name__ == '__main__':
    app.run(debug=True)