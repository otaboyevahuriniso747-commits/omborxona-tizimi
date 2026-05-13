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
            print(f"Azure SQL-ga ulanib bo'lmadi: {e}. SQLite-ga o'tilmoqda...")
    
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
        c.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'transactions')
            CREATE TABLE transactions (
                id INT PRIMARY KEY IDENTITY(1,1),
                product_id INT,
                type NVARCHAR(20) NOT NULL,
                quantity FLOAT NOT NULL,
                price FLOAT NOT NULL,
                date DATETIME DEFAULT GETDATE(),
                FOREIGN KEY (product_id) REFERENCES products (id)
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
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
    conn.commit()
    conn.close()

def dict_from_row(row, is_azure=False):
    if is_azure:
        columns = [column[0] for column in row.cursor_description]
        return dict(zip(columns, row))
    return dict(row)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM products ORDER BY id DESC')
    rows = c.fetchall()
    products = []
    for row in rows:
        r = dict_from_row(row, is_azure)
        products.append({
            'id': r['id'], 'name': r['name'], 'category': r['category'],
            'quantity': r['quantity'], 'unit': r['unit'],
            'min': r['min_quantity'], 'price': r['price']
        })
    conn.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    product_name = data['name'].strip()
    c.execute('SELECT id, quantity FROM products WHERE LOWER(name) = LOWER(?)', (product_name,))
    existing = c.fetchone()
    if existing:
        new_qty = float(existing[1]) + float(data['quantity'])
        c.execute('UPDATE products SET quantity=? WHERE id=?', (new_qty, existing[0]))
        conn.commit()
        conn.close()
        data['id'] = existing[0]
        data['quantity'] = new_qty
        return jsonify(data), 200
    else:
        c.execute('INSERT INTO products (name, category, quantity, unit, min_quantity, price) VALUES (?, ?, ?, ?, ?, ?)',
                  (product_name, data['category'], data['quantity'], data['unit'], data['min'], data.get('price', 0)))
        new_id = c.fetchone()[0] if is_azure else c.lastrowid
        c.execute('INSERT INTO transactions (product_id, type, quantity, price) VALUES (?, ?, ?, ?)',
                  (new_id, 'Kirim', data['quantity'], data.get('price', 0)))
        conn.commit()
        conn.close()
        data['id'] = new_id
        return jsonify(data), 201

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.json
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE products SET name=?, category=?, quantity=?, unit=?, min_quantity=?, price=? WHERE id=?',
              (data['name'], data['category'], data['quantity'], data['unit'], data['min'], data.get('price', 0), id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/products/<int:id>/withdraw', methods=['POST'])
def withdraw_product(id):
    data = request.json
    amount = float(data.get('amount', 0))
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT quantity FROM products WHERE id=?', (id,))
    product = c.fetchone()
    if not product or product[0] < amount:
        conn.close()
        return jsonify({"error": "Mahsulot yetarli emas"}), 400
    new_qty = product[0] - amount
    c.execute('UPDATE products SET quantity=? WHERE id=?', (new_qty, id))
    c.execute('INSERT INTO transactions (product_id, type, quantity, price) VALUES (?, ?, ?, ?)',
              (id, 'Chiqim', amount, data.get('price', 0)))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "new_quantity": new_qty})

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    if is_azure:
        c.execute('SELECT TOP 50 t.*, p.name as product_name, p.unit FROM transactions t LEFT JOIN products p ON t.product_id = p.id ORDER BY t.date DESC')
    else:
        c.execute('SELECT t.*, p.name as product_name, p.unit FROM transactions t LEFT JOIN products p ON t.product_id = p.id ORDER BY t.date DESC LIMIT 50')
    rows = c.fetchall()
    transactions = []
    for row in rows:
        r = dict_from_row(row, is_azure)
        transactions.append({
            'id': r['id'], 'product_name': r['product_name'], 'type': r['type'],
            'quantity': r['quantity'], 'price': r['price'], 'unit': r['unit'], 'date': r['date']
        })
    conn.close()
    return jsonify(transactions)

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
