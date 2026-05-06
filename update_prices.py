import sqlite3

DB_FILE = 'database.db'

def update_sample_prices():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Namuna narxlar (Mahsulot nomiga qarab taxminiy narxlar qo'yamiz)
    price_map = {
        'MacBook Pro M2': 25000000,
        'A4 Qog\'oz (Svetocopy)': 45000,
        'Simsiz Sishqoncha': 120000,
        'Zavod Suyuqligi (Moy)': 75000,
        'Noutbuk Dell XPS 15': 18000000,
        'Printer HP LaserJet': 3500000,
        'Klaviatura Logitech': 450000,
        'Stol chirog\'i': 150000,
        'Qora ruchka (Karobka)': 25000,
        'A4 Fayl papka': 2500,
        'Internet kabeli (Cat6)': 5000,
        'Ofis stul (Qora)': 850000,
        'Kuler uchin Suv': 15000,
        'Zaxira Batareyalar (AA)': 4000,
        'Qurilish Qorishmasi': 55000,
        'Yopishtiruvchi Skotch': 8000,
        'Monitor Samsung 27': 2800000,
        'Kreslo (Ofis)': 1200000,
        'Flashka 64GB': 85000,
        'Marker (Ko\'k)': 6000,
        'Qahva (Arabica)': 180000,
        'Printer bo\'yog\'i': 45000,
        'USB-C Kabel': 35000,
        'Stol (Yozuv)': 950000,
        'Xo\'jalik sovuni': 5000,
        'Nam salfetka': 12000
    }
    
    c.execute('SELECT id, name FROM products')
    products = c.fetchall()
    
    for product_id, name in products:
        # Agar xaritada bo'lsa o'shani, yo'q bo'lsa tasodifiy 10,000 - 1,000,000 oralig'ida
        price = price_map.get(name, 50000)
        c.execute('UPDATE products SET price=? WHERE id=?', (price, product_id))
        
    conn.commit()
    conn.close()
    print("Narxlar muvaffaqiyatli yangilandi!")

if __name__ == '__main__':
    update_sample_prices()
