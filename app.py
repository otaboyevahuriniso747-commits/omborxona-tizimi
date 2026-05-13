import os
import sqlite3
import pyodbc
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, Response

load_dotenv()

app = Flask(__name__)
DB_FILE = 'database.db'
AZURE_CONN_STR = os.getenv('AZURE_SQL_CONNECTIONSTRING')

def get_db_connection():
    if AZURE_CONN_STR:
        try:
            conn_str = AZURE_CONN_STR.strip('"').strip("'")
            conn = pyodbc.connect(conn_str)
            return conn, True
        except Exception as e:
            print(f"Azure SQL error: {e}")
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn, False

def init_db():
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    if is_azure:
        c.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'products')
            CREATE TABLE products (
                id INT PRIMARY KEY IDENTITY(1,1),
                name NVARCHAR(255) NOT NULL,
                category NVARCHAR(255) NOT NULL,
                quantity FLOAT NOT NULL,
                unit NVARCHAR(50) NOT NULL,
                min_quantity FLOAT NOT NULL,
                price FLOAT DEFAULT 0
            )
        ''')
    else:
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                min_quantity REAL NOT NULL,
                price REAL DEFAULT 0
            )
        ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, category, quantity, unit, min_quantity, price FROM products ORDER BY id DESC')
    rows = c.fetchall()
    
    products = []
    for row in rows:
        if is_azure:
            products.append({
                'id': row[0], 'name': row[1], 'category': row[2],
                'quantity': row[3], 'unit': row[4], 'min': row[5], 'price': row[6]
            })
        else:
            products.append({
                'id': row['id'], 'name': row['name'], 'category': row['category'],
                'quantity': row['quantity'], 'unit': row['unit'], 'min': row['min_quantity'], 'price': row['price']
            })
    conn.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    name = data['name'].strip()
    c.execute('INSERT INTO products (name, category, quantity, unit, min_quantity, price) VALUES (?, ?, ?, ?, ?, ?)',
              (name, data['category'], data['quantity'], data['unit'], data['min'], data.get('price', 0)))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 201

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    # Vaqtincha bo'sh ro'yxat qaytaramiz yoki soddalashtiramiz
    return jsonify([])

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
