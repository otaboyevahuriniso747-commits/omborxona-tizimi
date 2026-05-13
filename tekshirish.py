import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_CONN_STR = os.getenv('AZURE_SQL_CONNECTIONSTRING')

def check():
    if not AZURE_CONN_STR:
        print("Xatolik: .env faylida ulanish kodi topilmadi.")
        return

    print("Azure SQL bazasiga ulanish tekshirilmoqda...")
    try:
        # Bizda hozircha faqat legacy 'SQL Server' drayveri borligi uchun shuni ishlatamiz
        conn = pyodbc.connect(AZURE_CONN_STR)
        cursor = conn.cursor()
        
        print("\n--- BAZADAGI MAHSULOTLAR RO'YXATI ---")
        cursor.execute("SELECT name, category, quantity, unit, price FROM products")
        rows = cursor.fetchall()
        
        if not rows:
            print("Baza bo'sh yoki mahsulotlar topilmadi.")
        else:
            for row in rows:
                print(f"Nomi: {row[0]} | Toifa: {row[1]} | Miqdori: {row[2]} {row[3]} | Narxi: {row[4]} so'm")
        
        print("\n--- TRANZAKSIYALAR SONI ---")
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        print(f"Jami tranzaksiyalar soni: {count}")
        
        conn.close()
        print("\nUlanish muvaffaqiyatli! Baza to'g'ri ishlayapti.")
        
    except Exception as e:
        print(f"Ulanishda xatolik yuz berdi: {e}")

if __name__ == "__main__":
    check()
