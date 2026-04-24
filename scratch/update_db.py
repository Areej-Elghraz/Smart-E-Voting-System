import sqlite3
import os

db_path = r'd:\Facuilty Projects\4th level\Semester 2\Smart Applications\Project\project2\instance\evoting.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN has_verified_otp BOOLEAN DEFAULT 0")
        conn.commit()
        print("Column 'has_verified_otp' added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'has_verified_otp' already exists.")
        else:
            print(f"Error adding column: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
