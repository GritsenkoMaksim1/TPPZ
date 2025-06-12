import os
import sqlite3
import logging # Імпортуємо модуль logging
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

# --- НАЛАШТУВАННЯ ЛОГУВАННЯ ---
# Створюємо логер для додатка
logger = logging.getLogger(__name__)
# Встановлюємо загальний рівень логування для логера
logger.setLevel(logging.DEBUG)

# Створюємо обробник для виведення логів у консоль
console_handler = logging.StreamHandler()
# Встановлюємо рівень для консольного обробника (наприклад, тільки INFO і вище)
console_handler.setLevel(logging.INFO)

# Створюємо обробник для запису логів у файл
file_handler = logging.FileHandler('app.log')
# Встановлюємо рівень для файлового обробника (наприклад, DEBUG і вище)
file_handler.setLevel(logging.DEBUG)

# Визначаємо формат логів: час, рівень, ім'я логера/модуля, повідомлення
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Застосовуємо форматер до обробників
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Додаємо обробники до логера
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# --- НАЛАШТУВАННЯ ДОДАТКУ ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_for_diploma_project'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# --- НАЛАШТУВАННЯ АВТЕНТИФІКАЦІЇ ---
login_manager = LoginManager()
login_manager.init_app(app)
# Сторінка, на яку перенаправляє, якщо користувач не увійшов
login_manager.login_view = 'login'
login_manager.login_message = "Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки."
login_manager.login_message_category = "warning"


# --- МОДЕЛЬ КОРИСТУВАЧА ---
class User(UserMixin):
    """
    Модель користувача для Flask-Login, що представляє користувача з бази даних.
    """
    def __init__(self, user_id: int, username: str, password_hash: str):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash

    def get_id(self) -> str:
        return str(self.id)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """
    Завантажує користувача за його ID для Flask-Login.
    """
    conn = None
    try:
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user_data:
            logger.debug(f"Користувача {user_id} завантажено.")
            return User(user_id=user_data['id'], username=user_data['username'],
                        password_hash=user_data['password_hash'])
        logger.warning(f"Спроба завантажити неіснуючого користувача з ID: {user_id}")
    except sqlite3.Error as e:
        logger.error(f"Помилка при завантаженні користувача з БД (ID: {user_id}): {e}")
    finally:
        if conn:
            conn.close()
    return None


# --- ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ РОБОТИ З БД ---
def get_db_connection() -> sqlite3.Connection:
    """
    Встановлює та повертає з'єднання з базою даних SQLite.
    """
    try:
        conn = sqlite3.connect('shelter.db')
        conn.row_factory = sqlite3.Row
        logger.debug("З'єднання з базою даних 'shelter.db' встановлено.")
        return conn
    except sqlite3.Error as e:
        logger.critical(f"Критична помилка з'єднання з базою даних: {e}")
        # У випадку критичної помилки можна підняти виняток або вийти
        raise


# --- РОУТИ АВТЕНТИФІКАЦІЇ ---
@app.route('/register', methods=['GET', 'POST'])
def register() -> str:
    """
    Обробляє реєстрацію нових користувачів.
    """
    if current_user.is_authenticated:
        logger.info(f"Автентифікований користувач {current_user.username} намагався отримати доступ до сторінки реєстрації.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = None
        try:
            conn = get_db_connection()
            user_exists = conn.execute('SELECT id FROM users WHERE username = ?',
                                       (username,)).fetchone()

            if user_exists:
                flash('Користувач з таким іменем вже існує.', 'danger')
                logger.warning(f"Спроба реєстрації з вже існуючим іменем користувача: {username}")
                return redirect(url_for('register'))

            password_hash = generate_password_hash(password)
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                         (username, password_hash))
            conn.commit()
            flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
            logger.info(f"Новий користувач '{username}' успішно зареєстрований.")
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash('Помилка реєстрації. Спробуйте пізніше.', 'danger')
            logger.error(f"Помилка БД під час реєстрації користувача '{username}': {e}")
        except Exception as e:
            flash('Виникла непередбачена помилка.', 'danger')
            logger.critical(f"Непередбачена помилка під час реєстрації: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login() -> str:
    """
    Обробляє вхід користувачів у систему.
    """
    if current_user.is_authenticated:
        logger.info(f"Автентифікований користувач {current_user.username} намагався отримати доступ до сторінки входу.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = None
        try:
            conn = get_db_connection()
            user_data = conn.execute('SELECT * FROM users WHERE username = ?',
                                     (username,)).fetchone()

            if user_data and check_password_hash(user_data['password_hash'], password):
                user = User(user_id=user_data['id'], username=user_data['username'],
                            password_hash=user_data['password_hash'])
                login_user(user)
                flash('Вхід виконано успішно!', 'success')
                logger.info(f"Користувач '{username}' успішно увійшов.")
                return redirect(url_for('index'))
            else:
                flash('Неправильний логін або пароль.', 'danger')
                logger.warning(f"Невдала спроба входу для користувача '{username}'.")
        except sqlite3.Error as e:
            flash('Помилка входу. Спробуйте пізніше.', 'danger')
            logger.error(f"Помилка БД під час входу користувача '{username}': {e}")
        except Exception as e:
            flash('Виникла непередбачена помилка.', 'danger')
            logger.critical(f"Непередбачена помилка під час входу: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout() -> str:
    """
    Вихід користувача із системи.
    """
    username = current_user.username # Запам'ятовуємо ім'я перед виходом
    logout_user()
    flash('Ви вийшли з системи.', 'info')
    logger.info(f"Користувач '{username}' вийшов із системи.")
    return redirect(url_for('index'))


# --- ОСНОВНІ РОУТИ ДОДАТКУ ---
@app.route('/')
def index() -> str:
    """
    Відображає головну сторінку веб-додатку зі списком тварин.
    """
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str).strip()
    type_filter = request.args.get('type', '', type=str)

    per_page = 9
    offset = (page - 1) * per_page

    conn = None
    animals = []
    animal_types = []
    total_animals = 0
    total_pages = 0

    try:
        conn = get_db_connection()

        query_base = 'FROM animals WHERE 1=1'
        params = []
        if search_query:
            query_base += ' AND name LIKE ?'
            params.append(f'%{search_query}%')
        if type_filter:
            query_base += ' AND type = ?'
            params.append(type_filter)

        total_animals = conn.execute(f'SELECT COUNT(id) {query_base}',
                                     params).fetchone()[0]
        total_pages = ceil(total_animals / per_page) if total_animals > 0 else 1

        animals_query = f'SELECT * {query_base} ORDER BY date_added DESC LIMIT ? OFFSET ?'
        # Копіюємо params, щоб не змінити оригінальний список для COUNT запиту
        current_params = list(params)
        current_params.extend([per_page, offset])
        animals = conn.execute(animals_query, current_params).fetchall()

        animal_types = conn.execute('SELECT DISTINCT type FROM animals ORDER BY type').fetchall()
        logger.debug(f"Головна сторінка завантажена. Параметри: page={page}, search='{search_query}', type='{type_filter}'")

    except sqlite3.Error as e:
        logger.error(f"Помилка БД при завантаженні головної сторінки: {e}")
        flash('Помилка при завантаженні даних про тварин.', 'danger')
    except Exception as e:
        logger.critical(f"Непередбачена помилка на головній сторінці: {e}", exc_info=True)
        flash('Виникла непередбачена помилка.', 'danger')
    finally:
        if conn:
            conn.close()

    return render_template('index.html',
                           animals=animals,
                           animal_types=animal_types,
                           page=page,
                           total_pages=total_pages,
                           search_query=search_query,
                           type_filter=type_filter)


@app.route('/animal/<int:animal_id>')
def animal_details(animal_id: int) -> str:
    """
    Відображає деталі конкретної тварини за її ID.
    """
    conn = None
    try:
        conn = get_db_connection()
        animal = conn.execute('SELECT * FROM animals WHERE id = ?', (animal_id,)).fetchone()
        if animal is None:
            logger.warning(f"Спроба доступу до неіснуючої тварини з ID: {animal_id}")
            abort(404)
        logger.debug(f"Переглянуто деталі тварини з ID: {animal_id}")
        return render_template('animal_details.html', animal=animal)
    except sqlite3.Error as e:
        logger.error(f"Помилка БД при отриманні деталей тварини (ID: {animal_id}): {e}")
        flash('Помилка при завантаженні деталей тварини.', 'danger')
        abort(500) # Можливо, краще 500 помилка, якщо це проблема з БД
    except Exception as e:
        logger.critical(f"Непередбачена помилка при відображенні деталей тварини (ID: {animal_id}): {e}", exc_info=True)
        flash('Виникла непередбачена помилка.', 'danger')
        abort(500)
    finally:
        if conn:
            conn.close()


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_animal() -> str:
    """
    Додає нову тварину до бази даних.
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
            try:
                image_filename = image_file.filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                image_file.save(filepath)
                logger.info(f"Зображення '{image_filename}' успішно збережено для тварини '{name}'.")
            except IOError as e:
                logger.error(f"Помилка збереження зображення '{image_filename}' для тварини '{name}': {e}")
                flash('Помилка при завантаженні зображення.', 'danger')
                image_filename = None # Скидаємо, якщо збереження не вдалось

        conn = None
        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO animals (name, type, age, gender, health_status, '
                'description, image_filename) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (name, animal_type, age, gender, health_status, description,
                 image_filename)
            )
            conn.commit()
            flash(f'Тварину "{name}" успішно додано!', 'success')
            logger.info(f"Користувач '{current_user.username}' успішно додав тварину '{name}'.")
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            flash('Помилка при додаванні тварини до бази даних.', 'danger')
            logger.error(f"Помилка БД при додаванні тварини '{name}': {e}", exc_info=True)
        except Exception as e:
            flash('Виникла непередбачена помилка при додаванні тварини.', 'danger')
            logger.critical(f"Непередбачена помилка при додаванні тварини '{name}': {e}", exc_info=True)
        finally:
            if conn:
                conn.close()

    return render_template('add_animal.html')


@app.route('/edit/<int:animal_id>', methods=['GET', 'POST'])
@login_required
def edit_animal(animal_id: int) -> str:
    """
    Редагує дані про тварину за її ID.
    """
    conn = None
    animal = None
    try:
        conn = get_db_connection()
        animal = conn.execute('SELECT * FROM animals WHERE id = ?', (animal_id,)).fetchone()
        if animal is None:
            logger.warning(f"Спроба редагувати неіснуючу тварину з ID: {animal_id}")
            abort(404)

        if request.method == 'POST':
            name = request.form['name']
            animal_type = request.form['type']
            age = request.form['age']
            gender = request.form['gender']
            health_status = request.form['health_status']
            description = request.form['description']

            conn.execute(
                'UPDATE animals SET name = ?, type = ?, age = ?, gender = ?, '
                'health_status = ?, description = ? WHERE id = ?',
                (name, animal_type, age, gender, health_status, description,
                 animal_id)
            )
            conn.commit()
            flash(f'Дані про "{name}" успішно оновлено!', 'success')
            logger.info(f"Користувач '{current_user.username}' відредагував тварину ID:{animal_id} ('{name}').")
            return redirect(url_for('animal_details', animal_id=animal_id))
    except sqlite3.Error as e:
        flash('Помилка при оновленні даних про тварину.', 'danger')
        logger.error(f"Помилка БД при редагуванні тварини ID:{animal_id}: {e}", exc_info=True)
    except Exception as e:
        flash('Виникла непередбачена помилка при редагуванні тварини.', 'danger')
        logger.critical(f"Непередбачена помилка при редагуванні тварини ID:{animal_id}: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

    return render_template('edit_animal.html', animal=animal)


@app.route('/delete/<int:animal_id>', methods=['POST'])
@login_required
def delete_animal(animal_id: int) -> str:
    """
    Видаляє запис про тварину з бази даних.
    """
    conn = None
    animal_name = "невідома тварина"
    try:
        conn = get_db_connection()
        animal = conn.execute('SELECT * FROM animals WHERE id = ?', (animal_id,)).fetchone()

        if animal is None:
            logger.warning(f"Спроба видалити неіснуючу тварину з ID: {animal_id}")
            abort(404)

        animal_name = animal['name']

        if animal['image_filename']:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], animal['image_filename'])
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    logger.info(f"Зображення '{animal['image_filename']}' для тварини '{animal_name}' успішно видалено.")
                except OSError as e:
                    logger.error(f"Помилка видалення файлу зображення '{image_path}' для тварини '{animal_name}': {e}")
            else:
                logger.warning(f"Файл зображення '{image_path}' для тварини '{animal_name}' не знайдено, але запис в БД є.")

        conn.execute('DELETE FROM animals WHERE id = ?', (animal_id,))
        conn.commit()
        flash(f'Запис про "{animal_name}" було видалено.', 'info')
        logger.info(f"Користувач '{current_user.username}' успішно видалив тварину ID:{animal_id} ('{animal_name}').")
    except sqlite3.Error as e:
        flash('Помилка при видаленні тварини.', 'danger')
        logger.error(f"Помилка БД при видаленні тварини ID:{animal_id} ('{animal_name}'): {e}", exc_info=True)
    except Exception as e:
        flash('Виникла непередбачена помилка при видаленні тварини.', 'danger')
        logger.critical(f"Непередбачена помилка при видаленні тварини ID:{animal_id} ('{animal_name}'): {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    logger.info("Веб-додаток Притулку для тварин запускається...")
    app.run(debug=True)