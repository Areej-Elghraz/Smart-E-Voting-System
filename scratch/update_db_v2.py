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
    
    # User columns
    add_column(cursor, "user", "last_login_ip", "VARCHAR(50)")
    add_column(cursor, "user", "failed_login_count", "INTEGER", default=0)
    add_column(cursor, "user", "is_locked", "BOOLEAN", default=0)
    
    # Election columns
    add_column(cursor, "election", "start_time", "DATETIME")
    add_column(cursor, "election", "end_time", "DATETIME")
    
    # AuditLog column
    add_column(cursor, "audit_log", "session_id", "VARCHAR(100)")
    
    # New tables
    try:
        cursor.execute("""
            CREATE TABLE user_behavior (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                page_url VARCHAR(255),
                time_spent FLOAT,
                refreshes INTEGER DEFAULT 0,
                multiple_submissions BOOLEAN DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
        """)
        print("Table 'user_behavior' created.")
    except sqlite3.OperationalError:
        print("Table 'user_behavior' already exists.")
        
    try:
        cursor.execute("""
            CREATE TABLE session_risk (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id VARCHAR(100),
                ip_address VARCHAR(50),
                risk_score FLOAT DEFAULT 0.0,
                risk_factors TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
        """)
        print("Table 'session_risk' created.")
    except sqlite3.OperationalError:
        print("Table 'session_risk' already exists.")
    
    conn.commit()
    conn.close()
else:
    print(f"Database not found at {db_path}")
