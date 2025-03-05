import sqlite3
import os

def ensure_db_dir():
    db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static/database')
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return os.path.join(db_dir, 'serial_settings.db')

def init_db():
    db_path = ensure_db_dir()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS serial_settings (
        id INTEGER PRIMARY KEY,
        settings TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close() 