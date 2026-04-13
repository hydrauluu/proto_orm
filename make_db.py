import os
import sqlite3

DB_PATH = os.getenv("ORM_DB_PATH", "my_database.db")

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("DROP TABLE IF EXISTS employees")

cursor.execute("""
    CREATE TABLE employees (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name VARCHAR(255),
        last_name  VARCHAR(255),
        salary     NUMERIC(10, 2),
        grade      VARCHAR(10)
    )
""")

cursor.execute("""
    INSERT INTO employees (first_name, last_name, salary, grade)
    VALUES
        ('Renaud', 'Lemec', 13000, 'L2'),
        ('Junior', 'Racio', 16000, 'L3')
""")

connection.commit()
connection.close()

print("База данных создана: my_database.db")
