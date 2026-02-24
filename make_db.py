import sqlite3

connection = sqlite3.connect("my_database.db")
cursor = connection.cursor()

# hello
# Create employees table
query = """
    CREATE TABLE employees (
        id SERIAL PRIMARY KEY,
        first_name varchar(255),
        last_name varchar(255),
        salary numeric(10, 2),
        grade varchar(10)
    )
"""
cursor.execute(query)

# Insert some data
query = """
    INSERT INTO employees (first_name, last_name, salary, grade)
        VALUES
            ('Renaud', 'Lemec', 13000, 'L2'),
            ('Junior', 'Racio', 16000, 'L3');
"""
cursor.execute(query)

connection.commit()
