import sqlite3
import pyodbc
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DB_FILE = 'database.db'
AZURE_CONN_STR = os.getenv('AZURE_SQL_CONNECTIONSTRING')

def get_db_connection():
    if AZURE_CONN_STR:
        try:
            print("Connecting to Azure SQL...")
            # Remove quotes if they exist at the start/end
            conn_str = AZURE_CONN_STR.strip('"')
            conn = pyodbc.connect(conn_str)
            return conn, True
        except Exception as e:
            print(f"Azure connection failed (likely firewall or password).")
    
    print("Connecting to SQLite...")
    conn = sqlite3.connect(DB_FILE)
    return conn, False

def create_admin(username, password):
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    
    hashed_password = generate_password_hash(password)
    
    try:
        # First ensure table exists
        if is_azure:
            print("Creating users table in Azure...")
            c.execute('''
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
                CREATE TABLE users (
                    id INT PRIMARY KEY IDENTITY(1,1),
                    username NVARCHAR(100) UNIQUE NOT NULL,
                    password NVARCHAR(255) NOT NULL
                )
            ''')
        else:
            print("Creating users table in SQLite...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
        
        # Check if user already exists
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        if c.fetchone():
            print(f"Foydalanuvchi '{username}' allaqachon mavjud.")
            # Update password just in case
            c.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_password, username))
            print("Parol yangilandi.")
        else:
            # Insert user
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            print(f"Foydalanuvchi muvaffaqiyatli yaratildi: {username}")
        
        conn.commit()
    except Exception as e:
        print(f"Xatolik yuz berdi.")
    finally:
        conn.close()

if __name__ == "__main__":
    user = "admin"
    pwd = "123" 
    print(f"Yangi foydalanuvchi qo'shilmoqda: {user} / {pwd}")
    create_admin(user, pwd)
