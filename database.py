import aiosqlite

async def create_connection():
    conn = await aiosqlite.connect('bot.db')
    return conn

async def create_table():
    conn = await create_connection()
    cursor = await conn.cursor()
    await cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            user_id INTEGER,
            task TEXT
        )
    ''')
    await conn.commit()
    await conn.close()
