import os
import sqlite3
import pyodbc
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, Response

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    # Azure drayverlarini avtomatik topish
    available_drivers = [d for d in pyodbc.drivers()]
    print(f"Available drivers: {available_drivers}")
    
    # Bizga kerakli drayverni tanlash
    driver = None
    for d in available_drivers:
        if "ODBC Driver" in d and "SQL Server" in d:
            driver = d
            break
    if not driver and available_drivers:
        driver = available_drivers[0]
    
    if driver:
        try:
            conn_str = (
                f"Driver={{{driver}}};"
                "Server=tcp:demo-azure-4testing.database.windows.net,1433;"
                "Database=demoDB4Azure;"
                "Uid=azure-admin2;"
                "Pwd=Omborxona2026!;"
                "Encrypt=yes;"
                "TrustServerCertificate=no;"
                "Connection Timeout=30;"
            )
            conn = pyodbc.connect(conn_str)
            return conn, True
        except Exception as e:
            print(f"Azure connection error: {e}")
            raise e # Xatoni ko'rish uchun tashqariga chiqaramiz
    
    # Fallback to SQLite (faqat mahalliyda yoki drayver bo'lmasa)
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
        # Xatolikni foydalanuvchiga aniq ko'rsatamiz
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['POST'])
def add_product():
    try:
        data = request.json
        conn, is_azure = get_db_connection()
        c = conn.cursor()
        name = data['name'].strip()
        c.execute('INSERT INTO products (name, category, quantity, unit, min_quantity, price) VALUES (?, ?, ?, ?, ?, ?)',
                  (name, data['category'], data['quantity'], data['unit'], data['min'], data.get('price', 0)))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
