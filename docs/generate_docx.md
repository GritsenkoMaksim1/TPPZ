# Інструкція з Генерації Документації Проєкту "ShelterApp Documentation"

Цей документ містить покрокові вказівки для встановлення Sphinx та генерації повної HTML-документації для вашого Python-проєкту "ShelterApp Documentation" з його вихідного коду.

## 1. Активація Віртуального Середовища

Перш ніж розпочати будь-які дії, переконайтеся, що ви знаходитесь у кореневому каталозі проєкту (`E:\Users\Егор\PycharmProjects\HrytsenkoMaksym`) і ваше віртуальне середовище активоване.

Відкрийте PowerShell або командний рядок та виконайте:

```powershell
# Перейдіть до кореневого каталогу проекту
...\HrytsenkoMaksym

# Активуйте віртуальне середовище
...\.venv1\Scripts\activate


Після успішної активації, ви повинні побачити (.venv1) на початку вашого командного рядка.
2. Встановлення Sphinx
Якщо Sphinx та необхідна тема оформлення ще не встановлені у вашому віртуальному середовищі, встановіть їх:

PowerShell


pip install sphinx sphinx-rtd-theme


3. Налаштування Sphinx (одноразово)
Якщо Sphinx ініціалізується у проєкті вперше, або якщо потрібно переналаштувати конфігурацію, виконайте наступні кроки.
Перейдіть до каталогу документації:
PowerShell
cd docs


Запустіть майстер швидкого старту Sphinx:
Фрагмент коду
sphinx-quickstart

Відповідайте на запитання майстра наступним чином:
Separate source and build directories (y/n) [n]: y
Project name: ShelterApp Documentation
Author name(s): HrytsenkoMaksym (або Ваше ім'я)
Project release []: (Просто натисніть Enter)
Project language [en]: uk (або en, якщо бажаєте англійський інтерфейс документації)
Відредагуйте файл conf.py:
Відкрийте файл ...\HrytsenkoMaksym\docs\source\conf.py у вашому текстовому редакторі (наприклад, PyCharm) та внесіть наступні зміни:
Додайте шлях до вашого коду Python:
Python
# Додайте ці рядки на початку файлу, після імпортів os та sys
import os
import sys
sys.path.insert(0, os.path.abspath('../../')) # Шлях до кореня вашого проекту HrytsenkoMaksym


Увімкніть необхідні розширення: Знайдіть список extensions = [] та додайте до нього наступні розширення:
Python
extensions = [
    'sphinx.ext.autodoc',   # Дозволяє Sphinx витягувати документацію з Docstrings
    'sphinx.ext.napoleon',  # Підтримує Google Style Docstrings
    # ... інші розширення, якщо вони вже є
]


Встановіть тему оформлення: Знайдіть рядок html_theme = 'alabaster' та змініть його на:
Python
html_theme = 'sphinx_rtd_theme' # Сучасна та зручна тема "Read the Docs"


Створіть файли .rst для автоматичного вилучення Docstrings:
Перебуваючи в каталозі docs/, запустіть команду sphinx-apidoc. Вона просканує ваш проєкт і створить .rst файли для ваших модулів.
PowerShell
sphinx-apidoc -o source ..

Коли вас запитають Do you want to overwrite existing files? (y/n), введіть y і натисніть Enter.
Відредагуйте файл index.rst:
Відкрийте файл ...\HrytsenkoMaksym\docs\source\index.rst та переконайтеся, що він включає посилання на згенеровані модулі (зазвичай modules.rst). Ваш файл index.rst повинен виглядати приблизно так:
Фрагмент коду
.. ShelterApp Documentation documentation master file, created by
   sphinx-quickstart on Tue Jun 10 16:09:26 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ShelterApp Documentation documentation
======================================

Ласкаво просимо до документації проєкту «ShelterApp Documentation»!
Тут ви знайдете детальну інформацію про архітектуру, бізнес-логіку та програмний інтерфейс додатку.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules # Цей рядок включає згенеровану документацію модулів

Зверніть увагу: якщо sphinx-apidoc створив файл app.rst замість modules.rst, вам слід використовувати app замість modules у цьому рядку.
4. Генерація Документації
Після того, як Sphinx повністю налаштований, і всі Docstrings додані до вашого коду, ви можете згенерувати фінальну HTML-документацію.
Перейдіть до каталогу документації:
PowerShell
cd ..\HrytsenkoMaksym\docs


Очистіть попередні збірки (рекомендовано):
Це допомагає уникнути потенційних конфліктів зі старими файлами.
PowerShell
.\make.bat clean


Запустіть команду генерації HTML:
PowerShell
sphinx-build -b html source _build/html

Або, якщо вам зручніше використовувати make.bat:
PowerShell
.\make.bat html

Після успішного виконання цієї команди, згенеровані HTML-файли будуть знаходитись у папці E:\Users\Егор\PycharmProjects\HrytsenkoMaksym\docs\_build\html\.
5. Перегляд Згенерованої Документації
Ви можете відкрити головний файл документації у вашому веб-браузері:

\docs\_build\html\index.html


