from flask import Blueprint, render_template

# Создаём Blueprint для сайта
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Главная страница сайта"""
    return render_template('index.html')

@main_bp.route('/about')
def about():
    """Страница о проекте"""
    return render_template('about.html')