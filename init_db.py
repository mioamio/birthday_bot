import sqlite3

# Настройки базы данных
DB_NAME = 'birthday_bot.db'

# Создание таблицы users
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birthday TEXT NOT NULL,
            telegram_id TEXT,
            photo_file_id TEXT,
            congratulation_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("База данных успешно создана!")