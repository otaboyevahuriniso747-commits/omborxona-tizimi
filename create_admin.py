import sqlite3
import pyodbc
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

AZURE_CONN_STR = os.getenv('AZURE_SQL_CONNECTIONSTRING')

def get_db_connection():
    if AZURE_CONN_STR:
        try:
            conn_str = AZURE_CONN_STR.strip('"')
            conn = pyodbc.connect(conn_str)
            return conn, True
        except: pass
    return sqlite3.connect('database.db'), False

def update_user():
    user = "omborxona"
    pwd = "Omborxona2026!"
    
    conn, is_azure = get_db_connection()
    c = conn.cursor()
    hashed = generate_password_hash(pwd)
    
    try:
        c.execute('DELETE FROM users')
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (user, hashed))
        conn.commit()
        print(f"Baza yangilandi! \nLogin: {user}\nParol: {pwd}")
    except Exception as e:
        print(f"Xato: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_user()
