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
            conn = pyodbc.connect(AZURE_CONN_STR)
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
        # Azure SQL (T-SQL) uchun jadval yaratish
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
        # SQLite uchun jadval yaratish
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
        
        # Eskidan bor bazalarni yangilash (price ustuni bo'lmasa)
        try:
            c.execute('ALTER TABLE products ADD COLUMN price REAL DEFAULT 0')
        except sqlite3.OperationalError:
            pass

    # Boshlang'ich ma'lumotlarni qo'shish agar baza bo'sh bo'lsa
    c.execute('SELECT COUNT(*) FROM products')
    count = c.fetchone()[0]
    if count == 0:
        initial_products = [
            ('MacBook Pro M2', 'Elektronika', 15, 'dona', 5, 25000000),
            ('A4 Qog\'oz (Svetocopy)', 'Kantselyariya', 3, 'quti', 10, 45000),
            ('Simsiz Sishqoncha', 'Elektronika', 0, 'dona', 8, 120000),
            ('Zavod Suyuqligi (Moy)', 'Xom-ashyo', 45.5, 'litr', 50, 75000)
        ]
        if is_azure:
            for p in initial_products:
                c.execute('INSERT INTO products (name, category, quantity, unit, min_quantity, price) VALUES (?, ?, ?, ?, ?, ?)', p)
        else:
            c.executemany('INSERT INTO products (name, category, quantity, unit, min_quantity, price) VALUES (?, ?, ?, ?, ?, ?)', initial_products)
        
    conn.commit()
    conn.close()

def dict_from_row(row, is_azure=False):
    if is_azure:
        # pyodbc row to dict
        columns = [column[0] for column in row.cursor_description]
        return dict(zip(columns, row))
    else:
        # sqlite3 row to dict
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
            'id': r['id'],
            'name': r['name'],
            'category': r['category'],
            'quantity': r['quantity'],
            'unit': r['unit'],
            'min': r['min_quantity'],
            'price': r['price']
        })
    conn.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    
    product_name = data['name'].strip()
    
    # Mahsulot bazada bor-yo'qligini nomiga qarab tekshirish
    c.execute('SELECT id, quantity FROM products WHERE LOWER(name) = LOWER(?)', (product_name,))
    existing_product = c.fetchone()
    
    if existing_product:
        existing_id = existing_product[0]
        new_qty = float(existing_product[1]) + float(data['quantity'])
        c.execute('UPDATE products SET quantity=? WHERE id=?', (new_qty, existing_id))
        conn.commit()
        conn.close()
        
        data['id'] = existing_id
        data['quantity'] = new_qty
        return jsonify(data), 200
    else:
        c.execute('INSERT INTO products (name, category, quantity, unit, min_quantity, price) VALUES (?, ?, ?, ?, ?, ?)',
                  (product_name, data['category'], data['quantity'], data['unit'], data['min'], data.get('price', 0)))
        
        if is_azure:
            c.execute("SELECT @@IDENTITY")
            new_id = c.fetchone()[0]
        else:
            new_id = c.lastrowid
        
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
    c.execute('SELECT quantity, name FROM products WHERE id=?', (id,))
    product = c.fetchone()
    
    if not product:
        conn.close()
        return jsonify({"error": "Mahsulot topilmadi"}), 404
        
    current_qty = product[0]
    if current_qty < amount:
        conn.close()
        return jsonify({"error": f"Omborda yetarli mahsulot yo'q! (Hozirgi qoldiq: {current_qty})"}), 400
        
    new_qty = current_qty - amount
    c.execute('UPDATE products SET quantity=? WHERE id=?', (new_qty, id))
    
    # Tranzaksiyaga yozish (Chiqim)
    c.execute('INSERT INTO transactions (product_id, type, quantity, price) VALUES (?, ?, ?, ?)',
              (id, 'Chiqim', amount, data.get('price', 0)))
    
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "new_quantity": new_qty})

@app.route('/api/products/all', methods=['DELETE'])
def delete_all_products():
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM products')
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

import io
import csv
from flask import Response

@app.route('/api/export/csv')
def export_csv():
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT name, category, quantity, unit, min_quantity, price FROM products ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Mahsulot Nomi', 'Toifa', 'Miqdori', "O'lchov Birligi", 'Minimal Chegara', 'Narxi'])
    for row in rows:
        writer.writerow(list(row))
    
    csv_data = '\ufeff' + output.getvalue()
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=omborxona_hisoboti.csv"}
    )

import codecs

@app.route('/api/import/csv', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        return jsonify({"error": "Fayl topilmadi"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Fayl tanlanmadi"}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Faqat .csv formatdagi fayllar qabul qilinadi"}), 400

    try:
        stream = codecs.iterdecode(file.stream, 'utf-8-sig')
        csv_reader = csv.reader(stream)
        next(csv_reader, None)
        
        conn, is_azure = get_db_connection()
        c = conn.cursor()
        
        added_count = 0
        updated_count = 0
        
        for row in csv_reader:
            if not row or len(row) < 3:
                continue 
                
            name = str(row[0]).strip()
            category = str(row[1]).strip()
            
            try:
                quantity = float(row[2])
            except ValueError:
                quantity = 0.0
                
            unit = str(row[3]).strip() if len(row) > 3 and row[3].strip() else "dona"
            
            try:
                min_quantity = float(row[4]) if len(row) > 4 else 0.0
            except ValueError:
                min_quantity = 0.0

            try:
                price = float(row[5]) if len(row) > 5 else 0.0
            except ValueError:
                price = 0.0
                
            if not name:
                continue
                
            c.execute('SELECT id, quantity FROM products WHERE LOWER(name) = LOWER(?)', (name,))
            existing = c.fetchone()
            
            if existing:
                existing_id = existing[0]
                c.execute('''
                    UPDATE products 
                    SET category=?, quantity=?, unit=?, min_quantity=?, price=? 
                    WHERE id=?
                ''', (category, quantity, unit, min_quantity, price, existing_id))
                updated_count += 1
            else:
                c.execute('INSERT INTO products (name, category, quantity, unit, min_quantity, price) VALUES (?, ?, ?, ?, ?, ?)',
                          (name, category, quantity, unit, min_quantity, price))
                added_count += 1
                
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "added": added_count, "updated": updated_count}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT TOP 50 t.*, p.name as product_name, p.unit 
        FROM transactions t 
        LEFT JOIN products p ON t.product_id = p.id 
        ORDER BY t.date DESC
    ''') if is_azure else c.execute('''
        SELECT t.*, p.name as product_name, p.unit 
        FROM transactions t 
        LEFT JOIN products p ON t.product_id = p.id 
        ORDER BY t.date DESC LIMIT 50
    ''')
    
    rows = c.fetchall()
    transactions = []
    for row in rows:
        r = dict_from_row(row, is_azure)
        transactions.append({
            'id': r['id'],
            'product_name': r['product_name'] or "O'chirilgan mahsulot",
            'type': r['type'],
            'quantity': r['quantity'],
            'price': r['price'],
            'unit': r['unit'],
            'date': r['date']
        })
    conn.close()
    return jsonify(transactions)

# Bazani ilova yuklanishi bilan ishga tushiramiz
init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
