from flask import Flask, request, send_from_directory, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'  # Секретный ключ для сессий
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # База данных для хранения пользователей
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Папка для хранения загруженных файлов
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Создаем папку, если ее нет

# Максимальный размер блока для чтения файла (1 МБ)
CHUNK_SIZE = 1024 * 1024  # 1 МБ

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Создание таблиц
with app.app_context():
    db.create_all()

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Хэширование пароля
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Проверка, если пользователь уже существует
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({"error": "User already exists"}), 400

        # Создание нового пользователя
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login', message="User registered successfully"))

    return render_template('register.html')

# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            # Сохраняем информацию о пользователе в сессии
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    return render_template('login.html')

# Главная страница: выбор между регистрацией и входом
@app.route('/')
def home():
    if 'user_id' in session and 'username' in session:
        return redirect(url_for('index'))  # Если пользователь залогинен, перенаправляем на функциональную страницу
    return render_template('home.html')  # Если не залогинен, показываем выбор входа/регистрации

# Основная страница приложения с функционалом
@app.route('/index')
def index():
    # Проверка, залогинен ли пользователь
    if 'user_id' not in session or 'username' not in session:
        return redirect(url_for('home'))  # Если не залогинен, возвращаем на главную страницу

    # Проверка на корректное значение username
    username = session.get('username')
    if not username:
        return redirect(url_for('logout'))  # Если имя пользователя не указано, выходим из аккаунта

    files = os.listdir(UPLOAD_FOLDER)
    message = request.args.get('message')
    return render_template('index.html', files=files, message=message, username=username)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Проверка, залогинен ли пользователь
    if 'user_id' not in session:
        return redirect(url_for('home'))

    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file part in the request"}), 400

    file_name = file.filename
    if not file_name:
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file_name)

    with open(file_path, 'wb') as f:
        while True:
            chunk = file.read(CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)

    return redirect(url_for('index', message=f"File {file_name} uploaded successfully"))

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    # Проверка, залогинен ли пользователь
    if 'user_id' not in session:
        return redirect(url_for('home'))

    if not os.path.isfile(os.path.join(UPLOAD_FOLDER, filename)):
        return jsonify({"error": "File not found"}), 404

    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/files', methods=['GET'])
def list_files():
    # Проверка, залогинен ли пользователь
    if 'user_id' not in session:
        return redirect(url_for('home'))

    files = os.listdir(UPLOAD_FOLDER)
    return jsonify({"files": files})

# Выход из системы
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
