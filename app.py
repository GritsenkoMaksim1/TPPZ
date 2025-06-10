import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from math import ceil

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
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'])
    return None


# --- ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ РОБОТИ З БД ---
def get_db_connection():
    conn = sqlite3.connect('shelter.db')
    conn.row_factory = sqlite3.Row
    return conn


# --- РОУТИ АВТЕНТИФІКАЦІЇ ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user_exists = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

        if user_exists:
            flash('Користувач з таким іменем вже існує.', 'danger')
            conn.close()
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        conn.close()

        flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'])
            login_user(user)
            flash('Вхід виконано успішно!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неправильний логін або пароль.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви вийшли з системи.', 'info')
    return redirect(url_for('index'))


# --- ОСНОВНІ РОУТИ ДОДАТКУ ---
@app.route('/')
def index():
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
    total_animals = conn.execute(f'SELECT COUNT(id) {query_base}', params).fetchone()[0]
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
    conn = get_db_connection()
    animal = conn.execute('SELECT * FROM animals WHERE id = ?', (animal_id,)).fetchone()
    conn.close()
    if animal is None:
        abort(404)  # Якщо тварини з таким ID немає
    return render_template('animal_details.html', animal=animal)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_animal():
    if request.method == 'POST':
        # ... (логіка додавання, як і раніше, але з новими полями)
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
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO animals (name, type, age, gender, health_status, description, image_filename) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (name, animal_type, age, gender, health_status, description, image_filename))
        conn.commit()
        conn.close()

        flash(f'Тварину "{name}" успішно додано!', 'success')
        return redirect(url_for('index'))

    return render_template('add_animal.html')


@app.route('/edit/<int:animal_id>', methods=['GET', 'POST'])
@login_required
def edit_animal(animal_id):
    conn = get_db_connection()
    animal = conn.execute('SELECT * FROM animals WHERE id = ?', (animal_id,)).fetchone()
    conn.close()
    if animal is None:
        abort(404)

    if request.method == 'POST':
        # ... (логіка оновлення з новими полями)
        name = request.form['name']
        animal_type = request.form['type']
        age = request.form['age']
        gender = request.form['gender']
        health_status = request.form['health_status']
        description = request.form['description']

        conn = get_db_connection()
        conn.execute(
            'UPDATE animals SET name = ?, type = ?, age = ?, gender = ?, health_status = ?, description = ? WHERE id = ?',
            (name, animal_type, age, gender, health_status, description, animal_id))
        conn.commit()
        conn.close()

        flash(f'Дані про "{name}" успішно оновлено!', 'success')
        return redirect(url_for('animal_details', animal_id=animal_id))

    return render_template('edit_animal.html', animal=animal)


@app.route('/delete/<int:animal_id>', methods=['POST'])
@login_required
def delete_animal(animal_id):
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