import sqlite3
import os
from faker import Faker
import random
from werkzeug.security import generate_password_hash

# Ініціалізація Faker
fake = Faker('uk_UA') # Використовуємо українську локаль для більш реалістичних імен

DB_NAME = 'shelter.db'
UPLOAD_FOLDER = 'static/uploads'

# Видалення існуючого файлу БД для чистого старту
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)

# Ініціалізація бази даних
connection = sqlite3.connect(DB_NAME)
cursor = connection.cursor()

# Створення таблиць (скопійовано з init_db.py)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
''')

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
connection.commit()

# --- Генерація користувачів ---
print("Генерація користувачів...")
try:
    hashed_password = generate_password_hash("password123")
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", hashed_password))
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("user", hashed_password))
    connection.commit()
    print("Додано користувачів: admin, user")
except sqlite3.IntegrityError:
    print("Користувачі вже існують.")
except Exception as e:
    print(f"Помилка при додаванні користувачів: {e}")

# --- Генерація даних про тварин ---
print("Генерація даних про тварин...")
animal_types = ['Собака', 'Кішка', 'Птах', 'Гризун', 'Рептилія', 'Інше']
health_statuses = ['Здоровий', 'Потребує лікування', 'На реабілітації', 'Вакцинований']
genders = ['Чоловіча', 'Жіноча', 'Невідома']

num_animals = 500 # Збільшимо кількість тварин для кращого профілювання

# Створення папки для завантажень, якщо її немає
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Створимо декілька "фейкових" файлів зображень, щоб імітувати наявність файлів
# Реальні файли не потрібні для профілювання, але імітація наявності шляху до файлу важлива
sample_images = []
for i in range(5):
    img_name = f"sample_image_{i}.jpg"
    with open(os.path.join(UPLOAD_FOLDER, img_name), 'w') as f:
        f.write("dummy content")
    sample_images.append(img_name)
sample_images.append(None) # Додамо None для тварин без зображень

for _ in range(num_animals):
    name = fake.first_name()
    animal_type = random.choice(animal_types)
    age = random.randint(1, 15)
    gender = random.choice(genders)
    health_status = random.choice(health_statuses)
    description = fake.paragraph(nb_sentences=3)
    image_filename = random.choice(sample_images)

    cursor.execute(
        'INSERT INTO animals (name, type, age, gender, health_status, description, image_filename) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        (name, animal_type, age, gender, health_status, description, image_filename)
    )
connection.commit()
print(f"Додано {num_animals} фейкових записів про тварин.")

connection.close()
print("✅ База даних успішно заповнена фейковими даними.")