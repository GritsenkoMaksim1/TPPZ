# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
# Якщо розширення (модулі) знаходяться в іншому каталозі,
# додайте ці каталоги до sys.path тут.
#
# Якщо ваш код знаходиться в корені проєкту (батьківській папці від docs/),
# то потрібно додати батьківський каталог до шляху.
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ShelterApp Documentation'
copyright = '2025, HrytsenkoMaksym'
author = 'HrytsenkoMaksym'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',   # <-- ДОДАНО: Для автоматичного вилучення документації з docstrings
    'sphinx.ext.napoleon',  # <-- ДОДАНО: Для підтримки Google Style Docstrings
    # Можливо, вам знадобляться інші розширення в майбутньому:
    # 'sphinx.ext.todo',
    # 'sphinx.ext.coverage',
    # 'sphinx.ext.mathjax',
    # 'sphinx.ext.viewcode', # Дозволяє переглядати вихідний код, якщо натиснути на посилання "View Source"
]

templates_path = ['_templates']
exclude_patterns = []

language = 'uk'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme' # <-- ЗМІНЕНО: Використовуємо красиву тему "Read the Docs"
html_static_path = ['_static']