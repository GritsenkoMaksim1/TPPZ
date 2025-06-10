import sqlite3
import os

# Цей рядок перевіряє, чи існує файл бази даних, і видаляє його.
# Це гарантує, що ми завжди створюємо базу з чистого аркуша
# з правильною структурою.
if os.path.exists('shelter.db'):
    os.remove('shelter.db')

# Встановлюємо з'єднання з базою даних (це створить новий файл shelter.db)
connection = sqlite3.connect('shelter.db')
cursor = connection.cursor()

# 1. Створюємо таблицю 'users' для автентифікації працівників
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
''')

# 2. Створюємо таблицю 'animals' з усіма новими полями
cursor.execute('''
CREATE TABLE IF NOT EXISTS animals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT, 
    health_status TEXT,
    description TEXT NOT NULL,
    image_filename TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Зберігаємо зміни та закриваємо з'єднання
connection.commit()
connection.close()

print("✅ Базу даних та таблиці 'users' і 'animals' успішно створено.")