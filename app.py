"""
Основний файл додатку притулку для тварин.

Цей модуль керує роутами веб-додатку, автентифікацією користувачів
за допомогою Flask-Login та взаємодією з базою даних SQLite
для управління інформацією про тварин.
"""

import os
import sqlite3
from math import ceil

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, abort
)
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash


# --- НАЛАШТУВАННЯ ДОДАТКУ ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_for_diploma_project'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# --- НАЛАШТУВАННЯ АВТЕНТИФІКАЦІЇ ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Сторінка, на яку перенаправляє, якщо користувач не увійшов
login_manager.login_message = "Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки."
login_manager.login_message_category = "warning"


# --- МОДЕЛЬ КОРИСТУВАЧА ---
class User(UserMixin):
    """Модель користувача для Flask-Login, що представляє користувача з бази даних."""
    def __init__(self, user_id, username, password_hash):
        """
        Ініціалізує новий об'єкт користувача.

        Args:
            user_id (int): Унікальний ідентифікатор користувача.
            username (str): Ім'я користувача.
            password_hash (str): Хеш пароля користувача.
        """
        self.id = user_id
        self.username = username
        self.password_hash = password_hash


@login_manager.user_loader
def load_user(user_id):
    """
    Завантажує користувача за його ID для Flask-Login.

    Args:
        user_id (str): ID користувача, який потрібно завантажити.

    Returns:
        User: Об'єкт користувача, якщо знайдено, інакше None.
    """
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(user_id=user_data['id'], username=user_data['username'],
                    password_hash=user_data['password_hash'])
    return None


# --- ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ РОБОТИ З БД ---
def get_db_connection():
    """
    Встановлює та повертає з'єднання з базою даних SQLite.

    Налаштовує row_factory на sqlite3.Row для доступу до стовпців за іменами.

    Returns:
        sqlite3.Connection: Об'єкт з'єднання з базою даних.
    """
    conn = sqlite3.connect('shelter.db')
    conn.row_factory = sqlite3.Row
    return conn


# --- РОУТИ АВТЕНТИФІКАЦІЇ ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Обробляє реєстрацію нових користувачів.

    Якщо користувач вже автентифікований, перенаправляє його на головну сторінку.
    При POST-запиті перевіряє унікальність імені користувача,
    хешує пароль та зберігає дані нового користувача в БД.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user_exists = conn.execute('SELECT id FROM users WHERE username = ?',
                                   (username,)).fetchone()

        if user_exists:
            flash('Користувач з таким іменем вже існує.', 'danger')
            conn.close()
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                     (username, password_hash))
        conn.commit()
        conn.close()

        flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Обробляє вхід користувачів у систему.

    Якщо користувач вже автентифікований, перенаправляє його на головну сторінку.
    При POST-запиті перевіряє логін та пароль, використовуючи хешування.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE username = ?',
                                 (username,)).fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_id=user_data['id'], username=user_data['username'],
                        password_hash=user_data['password_hash'])
            login_user(user)
            flash('Вхід виконано успішно!', 'success')
            return redirect(url_for('index'))
        flash('Неправильний логін або пароль.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """
    Вихід користувача із системи.

    Потребує автентифікації. Перенаправляє на головну сторінку після виходу.
    """
    logout_user()
    flash('Ви вийшли з системи.', 'info')
    return redirect(url_for('index'))


# --- ОСНОВНІ РОУТИ ДОДАТКУ ---
@app.route('/')
def index():
    """
    Відображає головну сторінку зі списком тварин.

    Підтримує пагінацію, пошук за іменем та фільтрацію за типом тварини.
    """
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str).strip()
    type_filter = request.args.get('type', '', type=str)

    per_page = 9  # Кількість тварин на сторінці
    offset = (page - 1) * per_page

    conn = get_db_connection()

    # Формуємо запит до БД з урахуванням пошуку та фільтрації
    query_base = 'FROM animals WHERE 1=1'
    params = []
    if search_query:
        query_base += ' AND name LIKE ?'
        params.append(f'%{search_query}%')
    if type_filter:
        query_base += ' AND type = ?'
        params.append(type_filter)

    # Отримуємо загальну кількість тварин для пагінації
    total_animals = conn.execute(f'SELECT COUNT(id) {query_base}',
                                 params).fetchone()[0]
    total_pages = ceil(total_animals / per_page)

    # Отримуємо тварин для поточної сторінки
    animals_query = f'SELECT * {query_base} ORDER BY date_added DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    animals = conn.execute(animals_query, params).fetchall()

    # Отримуємо унікальні види тварин для фільтра
    animal_types = conn.execute('SELECT DISTINCT type FROM animals ORDER BY type').fetchall()

    conn.close()

    return render_template('index.html',
                           animals=animals,
                           animal_types=animal_types,
                           page=page,
                           total_pages=total_pages,
                           search_query=search_query,
                           type_filter=type_filter)


@app.route('/animal/<int:animal_id>')
def animal_details(animal_id):
    """
    Відображає деталі конкретної тварини за її ID.

    Args:
        animal_id (int): Ідентифікатор тварини.

    Returns:
        render_template: Сторінка з деталями тварини.
        abort: 404 помилка, якщо тварину не знайдено.
    """
    conn = get_db_connection()
    animal = conn.execute('SELECT * FROM animals WHERE id = ?', (animal_id,)).fetchone()
    conn.close()
    if animal is None:
        abort(404)  # Якщо тварини з таким ID немає
    return render_template('animal_details.html', animal=animal)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_animal():
    """
    Додає нову тварину до бази даних.

    Потребує автентифікації. Обробляє завантаження зображення та зберігає
    всі дані про тварину.
    """
    if request.method == 'POST':
        name = request.form['name']
        animal_type = request.form['type']
        age = request.form['age']
        gender = request.form['gender']
        health_status = request.form['health_status']
        description = request.form['description']
        image_file = request.files.get('image')

        image_filename = None
        if image_file and image_file.filename != '':
            image_filename = image_file.filename
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'],
                                         image_filename))

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO animals (name, type, age, gender, health_status, '
            'description, image_filename) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (name, animal_type, age, gender, health_status, description,
             image_filename)
        )
        conn.commit()
        conn.close()

        flash(f'Тварину "{name}" успішно додано!', 'success')
        return redirect(url_for('index'))

    return render_template('add_animal.html')


@app.route('/edit/<int:animal_id>', methods=['GET', 'POST'])
@login_required
def edit_animal(animal_id):
    """
    Редагує дані про тварину за її ID.

    Потребує автентифікації. Завантажує дані тварини для редагування
    та оновлює їх при POST-запиті.

    Args:
        animal_id (int): Ідентифікатор тварини, яку потрібно відредагувати.
    """
    conn = get_db_connection()
    animal = conn.execute('SELECT * FROM animals WHERE id = ?', (animal_id,)).fetchone()
    conn.close()
    if animal is None:
        abort(404)

    if request.method == 'POST':
        name = request.form['name']
        animal_type = request.form['type']
        age = request.form['age']
        gender = request.form['gender']
        health_status = request.form['health_status']
        description = request.form['description']

        conn = get_db_connection()
        conn.execute(
            'UPDATE animals SET name = ?, type = ?, age = ?, gender = ?, '
            'health_status = ?, description = ? WHERE id = ?',
            (name, animal_type, age, gender, health_status, description,
             animal_id)
        )
        conn.commit()
        conn.close()

        flash(f'Дані про "{name}" успішно оновлено!', 'success')
        return redirect(url_for('animal_details', animal_id=animal_id))

    return render_template('edit_animal.html', animal=animal)


@app.route('/delete/<int:animal_id>', methods=['POST'])
@login_required
def delete_animal(animal_id):
    """
    Видаляє запис про тварину з бази даних.

    Потребує автентифікації. Також видаляє пов'язане зображення, якщо воно існує.

    Args:
        animal_id (int): Ідентифікатор тварини, яку потрібно видалити.
    """
    conn = get_db_connection()
    animal = conn.execute('SELECT * FROM animals WHERE id = ?', (animal_id,)).fetchone()

    if animal is None:
        conn.close()
        abort(404)

    animal_name = animal['name']

    if animal['image_filename']:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], animal['image_filename'])
        if os.path.exists(image_path):
            os.remove(image_path)

    conn.execute('DELETE FROM animals WHERE id = ?', (animal_id,))
    conn.commit()
    conn.close()

    flash(f'Запис про "{animal_name}" було видалено.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
