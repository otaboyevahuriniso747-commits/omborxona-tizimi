import sqlite3

DB_FILE = 'database.db'
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

dummy_products = [
    ('Noutbuk Dell XPS 15', 'Elektronika', 8, 'dona', 3),
    ('Printer HP LaserJet', 'Texnika', 12, 'dona', 5),
    ('Klaviatura Logitech', 'Aksessuar', 25, 'dona', 10),
    ('Stol chirog\'i', 'Mebel', 40, 'dona', 15),
    ('Qora ruchka (Karobka)', 'Kantselyariya', 120, 'quti', 50),
    ('A4 Fayl papka', 'Kantselyariya', 300, 'dona', 100),
    ('Internet kabeli (Cat6)', 'Tarmoq', 500.5, 'metr', 100),
    ('Ofis stul (Qora)', 'Mebel', 5, 'dona', 2),
    ('Kuler uchin Suv', 'Oziq-ovqat', 1, 'litr', 5),
    ('Zaxira Batareyalar (AA)', 'Elektronika', 85, 'dona', 20),
    ('Qurilish Qorishmasi', 'Xom-ashyo', 450.5, 'kg', 100),
    ('Yopishtiruvchi Skotch', 'Kantselyariya', 4, 'dona', 10)
]

c.executemany('INSERT INTO products (name, category, quantity, unit, min_quantity) VALUES (?, ?, ?, ?, ?)', dummy_products)
conn.commit()
conn.close()

print("Mahsulotlar muvaffaqiyatli qo'shildi!")
