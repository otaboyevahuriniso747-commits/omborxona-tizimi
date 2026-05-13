import os
import sqlite3
import pyodbc
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, Response

load_dotenv()

app = Flask(__name__)

# Azure (Linux) serveri uchun to'g'ri drayver nomidan foydalanamiz
CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=tcp:demo-azure-4testing.database.windows.net,1433;"
    "Database=demoDB4Azure;"
    "Uid=azure-admin2;"
    "Pwd=Omborxona2026!;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

def get_db_connection():
    try:
        conn = pyodbc.connect(CONN_STR)
        return conn, True
    except Exception as e:
        print(f"Azure error with Driver 17: {e}")
        # Agar Driver 17 bo'lmasa, Driver 18 ni sinab ko'ramiz
        try:
            conn_str18 = CONN_STR.replace("Driver 17", "Driver 18")
            conn = pyodbc.connect(conn_str18 + "TrustServerCertificate=yes;")
            return conn, True
        except:
            print("Fallback to SQLite")
            conn = sqlite3.connect('database.db')
            conn.row_factory = sqlite3.Row
            return conn, False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
