# Притулок для тварин

## Опис

Це веб-додаток для управління інформацією про тварин у притулку. Додаток дозволяє додавати, редагувати, видаляти та переглядати інформацію про тварин, а також забезпечує автентифікацію користувачів.

## Необхідне програмне забезпечення

*   **Python 3.7+:**  Переконайтеся, що у вас встановлено Python 3.7 або новішої версії.  Ви можете завантажити його з [https://www.python.org/downloads/](https://www.python.org/downloads/).
*   **pip:**  Менеджер пакетів Python. Зазвичай встановлюється разом з Python.
*   **Virtualenv (рекомендовано):**  Для створення ізольованого середовища розробки.  Встановіть за допомогою: `pip install virtualenv`
*   **Git:**  Система контролю версій.  Встановіть з [https://git-scm.com/downloads](https://git-scm.com/downloads).

## Налаштування середовища розробки

1.  **Клонування репозиторію:**

    ```bash
    git clone https://github.com/GritsenkoMaksim1/TPPZ.git
    cd TPPZ
    ```

2.  **Створення віртуального середовища (рекомендовано):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate  # Windows
    ```

3.  **Встановлення залежностей:**

    ```bash
    pip install -r requirements.txt
    ```

    (Створи файл `requirements.txt` з залежностями, див. нижче)

4.  **Створення бази даних:**

    ```bash
    python init_db.py
    ```

    Ця команда створить файл `shelter.db` з необхідними таблицями.

## Залежності (requirements.txt)

Створіть файл `requirements.txt` у корені проєкту з наступним вмістом:
Use code with caution.
Markdown
Flask
Flask-Login
Werkzeug
sqlite3
## Запуск проєкту

1.  **Запуск сервера розробки:**

    ```bash
    python app.py
    ```

2.  **Відкрийте браузер та перейдіть за адресою:**  `http://127.0.0.1:5000/`

## Базові команди та операції

*   `python app.py`: Запуск сервера розробки.
*   `python init_db.py`: Створення бази даних.
*   `git pull`: Отримання останніх змін з репозиторію.
*   `git commit -m "Опис змін"`:  Фіксація змін у локальному репозиторії.
*   `git push`:  Завантаження змін у віддалений репозиторій.

## Додаткова інформація

*   Документація Flask: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
*   Документація Flask-Login: [https://flask-login.readthedocs.io/](https://flask-login.readthedocs.io/)
Use code with caution.
Важливо:
Переконайся, що ти створив файл requirements.txt з усіма необхідними залежностями.
Заміни посилання на репозиторій на актуальне, якщо воно зміниться.
Додай будь-які інші інструкції, які можуть бути корисними для нових розробників.