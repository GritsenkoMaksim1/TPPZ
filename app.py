import os
import sqlite3
import logging
from math import ceil
import uuid  # Для генерації унікальних ID помилок
import cProfile  # Для CPU-профілювання
import pstats  # Для читання звітів cProfile
import io  # Для перенаправлення виводу cProfile

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, abort
)
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime  # Для додавання часу в лог при кожній помилці

# --- НАЛАШТУВАННЯ ЛОГУВАННЯ ---
logger = logging.getLogger(__name__)

# Визначення рівня логування з змінної оточення або за замовчуванням
# Приклад: export LOG_LEVEL=DEBUG або set LOG_LEVEL=DEBUG
log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
log_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
# Перевіряємо, чи отриманий рядок рівня логування є коректним
# Якщо ні, встановлюємо INFO як рівень за замовчуванням
actual_log_level = log_level_map.get(log_level_str, logging.INFO)
logger.setLevel(actual_log_level)

# Створення обробників
console_handler = logging.StreamHandler()
# Консоль може мати вищий поріг, щоб не засмічувати вивід деталями
console_handler.setLevel(log_level_map.get(os.environ.get('CONSOLE_LOG_LEVEL', 'INFO').upper(), logging.INFO))

file_handler = logging.FileHandler('app.log')
# Файл логуємо все, що дозволено на рівні логера
file_handler.setLevel(actual_log_level)

# Визначення формату логів
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)

# Застосування форматера до обробників
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Додавання обробників до логера
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# --- НАЛАШТУВАННЯ ДОДАТКУ ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_for_diploma_project'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Додамо конфігурацію для Flask-DebugToolbar (якщо планується використовувати)
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
# app.config['DEBUG_TB_PROFILER_ENABLED'] = True
# from flask_debugtoolbar import DebugToolbarExtension
# toolbar = DebugToolbarExtension(app)


# --- НАЛАШТУВАННЯ АВТЕНТИФІКАЦІЇ ---
login_manager = LoginManager()
login_manager.init_app(app)
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
        """
        Повертає ID користувача, який використовується Flask-Login.
        """
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
            logger.debug(f"Користувача ID:{user_id} завантажено.")
            return User(user_id=user_data['id'], username=user_data['username'],
                        password_hash=user_data['password_hash'])
        logger.warning(f"Спроба завантажити неіснуючого користувача з ID: {user_id}. IP: {request.remote_addr}")
    except sqlite3.Error as e:
        error_id = str(uuid.uuid4())
        logger.error(f"Помилка БД ({error_id}) при завантаженні користувача ID:{user_id}. Error: {e}", exc_info=True)
        flash(f"Виникла технічна проблема (код: {error_id}). Будь ласка, спробуйте пізніше.", 'danger')
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.critical(f"Непередбачена помилка ({error_id}) при завантаженні користувача ID:{user_id}. Error: {e}", exc_info=True)
        flash(f"Виникла непередбачена помилка (код: {error_id}). Зверніться до адміністратора.", 'danger')
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
        error_id = str(uuid.uuid4())
        logger.critical(f"Критична помилка ({error_id}) з'єднання з базою даних 'shelter.db'. Error: {e}", exc_info=True)
        flash(f"Не вдалося підключитися до бази даних (код: {error_id}). Будь ласка, спробуйте пізніше.", 'danger')
        # У випадку критичної помилки з'єднання, додаток може бути нефункціональним
        abort(500)  # Повертаємо 500 Internal Server Error


# --- ГЛОБАЛЬНІ ОБРОБНИКИ ПОМИЛОК FLASK ---
@app.errorhandler(404)
def page_not_found(e):
    """
    Обробник помилок 404 (Сторінка не знайдена).
    """
    error_id = str(uuid.uuid4())
    logger.warning(f"Сторінка не знайдена (404) ({error_id}). URL: {request.url}. IP: {request.remote_addr}")
    return render_template('404.html', error_id=error_id), 404

@app.errorhandler(500)
def internal_server_error(e):
    """
    Обробник помилок 500 (Внутрішня помилка сервера).
    """
    error_id = str(uuid.uuid4())
    # Включити exc_info=True лише якщо це не помилка, згенерована abort(500)
    # Flask самостійно обробляє винятки і передає їх до errorhandler
    logger.critical(f"Внутрішня помилка сервера (500) ({error_id}). URL: {request.url}. IP: {request.remote_addr}. Error: {e}", exc_info=True)
    return render_template('500.html', error_id=error_id), 500


# --- ДОПОМІЖНА ФУНКЦІЯ ДЛЯ КОНТЕКСТУ ЛОГУВАННЯ ---
def get_log_context() -> str:
    """
    Формує рядок з контекстною інформацією для логування.
    """
    user_id = current_user.id if current_user.is_authenticated else "anon"
    username = current_user.username if current_user.is_authenticated else "anonymous"
    return f"User ID: {user_id}, Username: {username}, IP: {request.remote_addr}, URL: {request.url}"

# --- РОУТИ АВТЕНТИФІКАЦІЇ ---
@app.route('/register', methods=['GET', 'POST'])
def register() -> str:
    """
    Обробляє реєстрацію нових користувачів.
    """
    if current_user.is_authenticated:
        logger.info(f"Автентифікований користувач {current_user.username} намагався отримати доступ до сторінки реєстрації. {get_log_context()}")
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
                logger.warning(f"Спроба реєстрації з вже існуючим іменем користувача: '{username}'. {get_log_context()}")
                return redirect(url_for('register'))

            password_hash = generate_password_hash(password)
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                         (username, password_hash))
            conn.commit()
            flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
            logger.info(f"Новий користувач '{username}' успішно зареєстрований. {get_log_context()}")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError as e:  # Специфічна помилка для UNIQUE constraint
            error_id = str(uuid.uuid4())
            flash(f"Помилка: Користувач з таким іменем вже існує. (код: {error_id})", 'danger')
            logger.error(f"Помилка цілісності БД ({error_id}) під час реєстрації '{username}'. Error: {e}. {get_log_context()}", exc_info=True)
        except sqlite3.Error as e:
            error_id = str(uuid.uuid4())
            flash(f"Помилка реєстрації. Спробуйте пізніше. (код: {error_id})", 'danger')
            logger.error(f"Помилка БД ({error_id}) під час реєстрації користувача '{username}'. Error: {e}. {get_log_context()}", exc_info=True)
        except Exception as e:
            error_id = str(uuid.uuid4())
            flash(f"Виникла непередбачена помилка (код: {error_id}). Зверніться до адміністратора.", 'danger')
            logger.critical(f"Непередбачена помилка ({error_id}) під час реєстрації. Error: {e}. {get_log_context()}", exc_info=True)
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
        logger.info(f"Автентифікований користувач {current_user.username} намагався отримати доступ до сторінки входу. {get_log_context()}")
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
                logger.info(f"Користувач '{username}' успішно увійшов. {get_log_context()}")
                return redirect(url_for('index'))
            else:
                flash('Неправильний логін або пароль.', 'danger')
                logger.warning(f"Невдала спроба входу для користувача '{username}'. IP: {request.remote_addr}")
        except sqlite3.Error as e:
            error_id = str(uuid.uuid4())
            flash(f"Помилка входу. Спробуйте пізніше. (код: {error_id})", 'danger')
            logger.error(f"Помилка БД ({error_id}) під час входу користувача '{username}'. Error: {e}. {get_log_context()}", exc_info=True)
        except Exception as e:
            error_id = str(uuid.uuid4())
            flash(f"Виникла непередбачена помилка (код: {error_id}). Зверніться до адміністратора.", 'danger')
            logger.critical(f"Непередбачена помилка ({error_id}) під час входу. Error: {e}. {get_log_context()}", exc_info=True)
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
    username = current_user.username  # Запам'ятовуємо ім'я перед виходом
    logout_user()
    flash('Ви вийшли з системи.', 'info')
    logger.info(f"Користувач '{username}' вийшов із системи. {get_log_context()}")
    return redirect(url_for('index'))


# --- ОСНОВНІ РОУТИ ДОДАТКУ ---
@app.route('/')
def index() -> str:
    """
    Відображає головну сторінку веб-додатку зі списком тварин.
    """
    # Обгортаємо логіку в cProfile для профілювання CPU
    profiler = cProfile.Profile()
    profiler.enable()

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

        total_animals_cursor = conn.execute(f'SELECT COUNT(id) {query_base}', params)
        total_animals = total_animals_cursor.fetchone()[0]
        total_pages = ceil(total_animals / per_page) if total_animals > 0 else 1

        animals_query = f'SELECT * {query_base} ORDER BY date_added DESC LIMIT ? OFFSET ?'
        current_params = list(params)  # Копіюємо params, щоб не змінити оригінальний список для COUNT запиту
        current_params.extend([per_page, offset])
        animals = conn.execute(animals_query, current_params).fetchall()

        animal_types = conn.execute('SELECT DISTINCT type FROM animals ORDER BY type').fetchall()
        logger.debug(f"Головна сторінка завантажена. Параметри: page={page}, search='{search_query}', type='{type_filter}'. {get_log_context()}")

    except sqlite3.Error as e:
        error_id = str(uuid.uuid4())
        logger.error(f"Помилка БД ({error_id}) при завантаженні головної сторінки. Error: {e}. {get_log_context()}", exc_info=True)
        flash(f"Помилка при завантаженні даних про тварин (код: {error_id}).", 'danger')
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.critical(f"Непередбачена помилка ({error_id}) на головній сторінці. Error: {e}. {get_log_context()}", exc_info=True)
        flash(f"Виникла непередбачена помилка (код: {error_id}).", 'danger')
    finally:
        if conn:
            conn.close()

    # Завершення профілювання та вивід результатів
    profiler.disable()
    s = io.StringIO()
    # Сортуємо результати за кумулятивним часом (cumtime)
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    # Виводимо 10 найбільш "гарячих" точок
    ps.print_stats(10)
    logger.info(f"\n--- CPU Профіль для '/':\n{s.getvalue()}")


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
            logger.warning(f"Спроба доступу до неіснуючої тварини з ID: {animal_id}. {get_log_context()}")
            abort(404)
        logger.debug(f"Переглянуто деталі тварини з ID: {animal_id}. {get_log_context()}")
        return render_template('animal_details.html', animal=animal)
    except sqlite3.Error as e:
        error_id = str(uuid.uuid4())
        logger.error(f"Помилка БД ({error_id}) при отриманні деталей тварини ID:{animal_id}. Error: {e}. {get_log_context()}", exc_info=True)
        flash(f"Помилка при завантаженні деталей тварини (код: {error_id}).", 'danger')
        abort(500)
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.critical(f"Непередбачена помилка ({error_id}) при відображенні деталей тварини ID:{animal_id}. Error: {e}. {get_log_context()}", exc_info=True)
        flash(f"Виникла непередбачена помилка (код: {error_id}).", 'danger')
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
                # Перевірка на безпеку назви файлу та розширення
                if not allowed_file(image_file.filename):
                    flash('Дозволені лише зображення (png, jpg, jpeg, gif).', 'warning')
                    logger.warning(f"Спроба завантажити недозволений тип файлу: {image_file.filename}. {get_log_context()}")
                    return render_template('add_animal.html') # Повернутись до форми

                # Додамо унікальний префікс до імені файлу, щоб уникнути конфліктів
                filename_base, file_extension = os.path.splitext(image_file.filename)
                image_filename = f"{uuid.uuid4()}_{filename_base}{file_extension}"

                filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                image_file.save(filepath)
                logger.info(f"Зображення '{image_filename}' успішно збережено для тварини '{name}'. {get_log_context()}")
            except IOError as e:
                error_id = str(uuid.uuid4())
                flash(f"Помилка при завантаженні зображення (код: {error_id}). Спробуйте пізніше.", 'danger')
                logger.error(f"Помилка збереження зображення '{image_file.filename}' для тварини '{name}' ({error_id}). Error: {e}. {get_log_context()}", exc_info=True)
                image_filename = None  # Скидаємо, якщо збереження не вдалось
            except Exception as e:
                error_id = str(uuid.uuid4())
                flash(f"Непередбачена помилка при обробці зображення (код: {error_id}).", 'danger')
                logger.critical(f"Непередбачена помилка ({error_id}) при обробці зображення. Error: {e}. {get_log_context()}", exc_info=True)
                image_filename = None


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
            logger.info(f"Користувач '{current_user.username}' успішно додав тварину '{name}'. {get_log_context()}")
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            error_id = str(uuid.uuid4())
            flash(f"Помилка при додаванні тварини до бази даних (код: {error_id}). Будь ласка, перевірте введені дані.", 'danger')
            logger.error(f"Помилка БД ({error_id}) при додаванні тварини '{name}'. Error: {e}. Дані форми: {request.form}. {get_log_context()}", exc_info=True)
        except Exception as e:
            error_id = str(uuid.uuid4())
            flash(f"Виникла непередбачена помилка при додаванні тварини (код: {error_id}).", 'danger')
            logger.critical(f"Непередбачена помилка ({error_id}) при додаванні тварини '{name}'. Error: {e}. Дані форми: {request.form}. {get_log_context()}", exc_info=True)
        finally:
            if conn:
                conn.close()

    return render_template('add_animal.html')

# Допоміжна функція для перевірки розширення файлу
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            logger.warning(f"Спроба редагувати неіснуючу тварину з ID: {animal_id}. {get_log_context()}")
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
            logger.info(f"Користувач '{current_user.username}' відредагував тварину ID:{animal_id} ('{name}'). {get_log_context()}")
            return redirect(url_for('animal_details', animal_id=animal_id))
    except sqlite3.Error as e:
        error_id = str(uuid.uuid4())
        flash(f"Помилка при оновленні даних про тварину (код: {error_id}). Перевірте введені дані.", 'danger')
        logger.error(f"Помилка БД ({error_id}) при редагуванні тварини ID:{animal_id}. Error: {e}. Дані форми: {request.form}. {get_log_context()}", exc_info=True)
    except Exception as e:
        error_id = str(uuid.uuid4())
        flash(f"Виникла непередбачена помилка при редагуванні тварини (код: {error_id}).", 'danger')
        logger.critical(f"Непередбачена помилка ({error_id}) при редагуванні тварини ID:{animal_id}. Error: {e}. Дані форми: {request.form}. {get_log_context()}", exc_info=True)
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
            logger.warning(f"Спроба видалити неіснуючу тварину з ID: {animal_id}. {get_log_context()}")
            abort(404)

        animal_name = animal['name']

        if animal['image_filename']:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], animal['image_filename'])
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    logger.info(f"Зображення '{animal['image_filename']}' для тварини '{animal_name}' успішно видалено. {get_log_context()}")
                except OSError as e:
                    error_id = str(uuid.uuid4())
                    logger.error(f"Помилка видалення файлу зображення '{image_path}' для тварини '{animal_name}' ({error_id}). Error: {e}. {get_log_context()}", exc_info=True)
                    flash(f"Виникла проблема при видаленні файлу зображення (код: {error_id}).", 'warning')
            else:
                logger.warning(f"Файл зображення '{image_path}' для тварини '{animal_name}' не знайдено, але запис в БД є. {get_log_context()}")

        conn.execute('DELETE FROM animals WHERE id = ?', (animal_id,))
        conn.commit()
        flash(f'Запис про "{animal_name}" було видалено.', 'info')
        logger.info(f"Користувач '{current_user.username}' успішно видалив тварину ID:{animal_id} ('{animal_name}'). {get_log_context()}")
    except sqlite3.Error as e:
        error_id = str(uuid.uuid4())
        flash(f"Помилка при видаленні тварини (код: {error_id}).", 'danger')
        logger.error(f"Помилка БД ({error_id}) при видаленні тварини ID:{animal_id} ('{animal_name}'). Error: {e}. {get_log_context()}", exc_info=True)
    except Exception as e:
        error_id = str(uuid.uuid4())
        flash(f"Виникла непередбачена помилка при видаленні тварини (код: {error_id}).", 'danger')
        logger.critical(f"Непередбачена помилка ({error_id}) при видаленні тварини ID:{animal_id} ('{animal_name}'). Error: {e}. {get_log_context()}", exc_info=True)
    finally:
        if conn:
            conn.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    logger.info("Веб-додаток Притулку для тварин запускається...")
    # Створюємо папку для завантаження, якщо її немає
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        logger.info(f"Створено папку для завантажень: {app.config['UPLOAD_FOLDER']}")

    app.run(debug=True)