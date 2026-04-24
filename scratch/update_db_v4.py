import sqlite3
import os

db_path = r'd:\Facuilty Projects\4th level\Semester 2\Smart Applications\Project\project2\instance\evoting.db'

def add_column(cursor, table, column, type, default=None):
    try:
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {type}"
        if default is not None:
            sql += f" DEFAULT {default}"
        cursor.execute(sql)
        print(f"Column '{column}' added to '{table}'.")
    except sqlite3.OperationalError:
        print(f"Column '{column}' already exists in '{table}'.")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Election columns
    add_column(cursor, "election", "topics", "VARCHAR(255)")
    
    conn.commit()
    conn.close()
else:
    print(f"Database not found at {db_path}")
