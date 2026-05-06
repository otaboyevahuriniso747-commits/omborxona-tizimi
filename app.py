from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)
DB_FILE = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
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
            type TEXT NOT NULL, -- 'Kirim' yoki 'Chiqim'
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Eskidan bor bazalarni yangilash (agar price ustuni bo'lmasa qo'shish)
    try:
        c.execute('ALTER TABLE products ADD COLUMN price REAL DEFAULT 0')
    except sqlite3.OperationalError:
        pass # Ustun allaqachon mavjud bo'lsa xato bermasligi uchun
    
    # Boshlang'ich ma'lumotlarni qo'shish agar baza bo'sh bo'lsa
    c.execute('SELECT COUNT(*) FROM products')
    if c.fetchone()[0] == 0:
        initial_products = [
            ('MacBook Pro M2', 'Elektronika', 15, 'dona', 5, 25000000),
            ('A4 Qog\'oz (Svetocopy)', 'Kantselyariya', 3, 'quti', 10, 45000),
            ('Simsiz Sishqoncha', 'Elektronika', 0, 'dona', 8, 120000),
            ('Zavod Suyuqligi (Moy)', 'Xom-ashyo', 45.5, 'litr', 50, 75000)
        ]
        c.executemany('INSERT INTO products (name, category, quantity, unit, min_quantity, price) VALUES (?, ?, ?, ?, ?, ?)', initial_products)
        
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM products ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    
    products = []
    for row in rows:
        products.append({
            'id': row['id'],
            'name': row['name'],
            'category': row['category'],
            'quantity': row['quantity'],
            'unit': row['unit'],
            'min': row['min_quantity'],
            'price': row['price']
        })
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    product_name = data['name'].strip()
    
    # Mahsulot bazada bor-yo'qligini nomiga qarab tekshirish (katta-kichik harfni inobatga olmasdan)
    c.execute('SELECT id, quantity FROM products WHERE lower(name) = lower(?)', (product_name,))
    existing_product = c.fetchone()
    
    if existing_product:
        # Agar bor bo'lsa, faqat miqdorini (sonini) qo'shish
        existing_id = existing_product[0]
        new_qty = existing_product[1] + float(data['quantity'])
        c.execute('UPDATE products SET quantity=? WHERE id=?', (new_qty, existing_id))
        conn.commit()
        conn.close()
        
        data['id'] = existing_id
        data['quantity'] = new_qty
        return jsonify(data), 200
    else:
        # Agar yo'q bo'lsa, yangi yaratish
        c.execute('INSERT INTO products (name, category, quantity, unit, min_quantity, price) VALUES (?, ?, ?, ?, ?, ?)',
                  (product_name, data['category'], data['quantity'], data['unit'], data['min'], data.get('price', 0)))
        new_id = c.lastrowid
        
        # Tranzaksiyaga yozish (Kirim)
        c.execute('INSERT INTO transactions (product_id, type, quantity, price) VALUES (?, ?, ?, ?)',
                  (new_id, 'Kirim', data['quantity'], data.get('price', 0)))
        
        conn.commit()
        conn.close()
        
        data['id'] = new_id
        return jsonify(data), 201

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE products SET name=?, category=?, quantity=?, unit=?, min_quantity=?, price=? WHERE id=?',
              (data['name'], data['category'], data['quantity'], data['unit'], data['min'], data.get('price', 0), id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/products/<int:id>/withdraw', methods=['POST'])
def withdraw_product(id):
    data = request.json
    amount = float(data.get('amount', 0))
    
    conn = sqlite3.connect(DB_FILE)
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
    conn = sqlite3.connect(DB_FILE)
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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT name, category, quantity, unit, min_quantity FROM products ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    # Sarlavhalarni yozish
    writer.writerow(['Mahsulot Nomi', 'Toifa', 'Miqdori', "O'lchov Birligi", 'Minimal Chegara', 'Narxi'])
    for row in rows:
        writer.writerow(row)
    
    # BOM (Byte Order Mark) qo'shish - Excel da UTF-8 harflar to'g'ri ko'rinishi uchun
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
        # Faylni o'qish (UTF-8 formatida, Excel yozadigan BOM belgilarisiz)
        stream = codecs.iterdecode(file.stream, 'utf-8-sig')
        csv_reader = csv.reader(stream)
        
        # Birinchi qator (Sarlavhalar) ni o'tkazib yuborish
        next(csv_reader, None)
        
        conn = sqlite3.connect(DB_FILE)
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
                
            # Bazadan qidirish
            c.execute('SELECT id, quantity FROM products WHERE lower(name) = lower(?)', (name,))
            existing = c.fetchone()
            
            if existing:
                existing_id = existing[0]
                new_qty = existing[1] + quantity
                c.execute('UPDATE products SET quantity=? WHERE id=?', (new_qty, existing_id))
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
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT t.*, p.name as product_name, p.unit 
        FROM transactions t 
        LEFT JOIN products p ON t.product_id = p.id 
        ORDER BY t.date DESC LIMIT 50
    ''')
    rows = c.fetchall()
    conn.close()
    
    transactions = []
    for row in rows:
        transactions.append({
            'id': row['id'],
            'product_name': row['product_name'] or "O'chirilgan mahsulot",
            'type': row['type'],
            'quantity': row['quantity'],
            'price': row['price'],
            'unit': row['unit'],
            'date': row['date']
        })
    return jsonify(transactions)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
