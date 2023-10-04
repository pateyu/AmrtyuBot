import sqlite3

def create_connection():
    conn = sqlite3.connect('bot.db')
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            user_id INTEGER,
            task TEXT
        )
    ''')
    conn.commit()
    conn.close()