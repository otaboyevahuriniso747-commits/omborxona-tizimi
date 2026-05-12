import sqlite3
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB = 'database.db'
AZURE_CONN_STR = os.getenv('AZURE_SQL_CONNECTIONSTRING')

def migrate():
    log_file = "migration_log.txt"
    with open(log_file, "w", encoding="utf-8") as log:
        if not AZURE_CONN_STR:
            log.write("Error: AZURE_SQL_CONNECTIONSTRING not found in .env\n")
            return

        log.write("Starting migration...\n")
        
        sqlite_conn = None
        azure_conn = None
        
        try:
            sqlite_conn = sqlite3.connect(SQLITE_DB)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_conn.cursor()
            
            log.write(f"Connecting to Azure SQL...\n")
            azure_conn = pyodbc.connect(AZURE_CONN_STR)
            azure_cursor = azure_conn.cursor()
            
            # 1. Create tables if not exist
            log.write("Creating tables in Azure SQL if they don't exist...\n")
            azure_cursor.execute('''
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
            azure_cursor.execute('''
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
            azure_conn.commit()
            
            # 2. Migrate Products
            log.write("Migrating products...\n")
            sqlite_cursor.execute("SELECT * FROM products")
            products = sqlite_cursor.fetchall()
            
            azure_cursor.execute("SET IDENTITY_INSERT products ON")
            for p in products:
                azure_cursor.execute("""
                    INSERT INTO products (id, name, category, quantity, unit, min_quantity, price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (p['id'], p['name'], p['category'], p['quantity'], p['unit'], p['min_quantity'], p['price']))
            azure_cursor.execute("SET IDENTITY_INSERT products OFF")
            log.write(f"Migrated {len(products)} products.\n")
            
            # 3. Migrate Transactions
            log.write("Migrating transactions...\n")
            sqlite_cursor.execute("SELECT * FROM transactions")
            transactions = sqlite_cursor.fetchall()
            
            azure_cursor.execute("SET IDENTITY_INSERT transactions ON")
            for t in transactions:
                azure_cursor.execute("""
                    INSERT INTO transactions (id, product_id, type, quantity, price, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (t['id'], t['product_id'], t['type'], t['quantity'], t['price'], t['date']))
            azure_cursor.execute("SET IDENTITY_INSERT transactions OFF")
            log.write(f"Migrated {len(transactions)} transactions.\n")
            
            azure_conn.commit()
            log.write("Migration successful!\n")
            print("Migration successful!")
            
        except Exception as e:
            err_msg = str(e)
            log.write(f"Migration failed: {err_msg}\n")
            print(f"Migration failed: check migration_log.txt")
        finally:
            if sqlite_conn: sqlite_conn.close()
            if azure_conn: azure_conn.close()

if __name__ == "__main__":
    migrate()
