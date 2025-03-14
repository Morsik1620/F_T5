import secrets

#import flask
import sqlalchemy
import werkzeug.security
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
#from flask_login import LoginManager

app = Flask(__name__) # с помощью этой переменной фреймворк определяет пути к корневому каталогу
menu = ["Домашняя страница", "Дневник программиста", 'Авторизация']     # ----- создаю меню в шапке
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///main_f_t5_dz.db"       # ----- создаю базу данных
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)                                              # используется для миграций
app.config['SECRET_KEY'] = 'synergy'                                    # создаем секретный код
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)

class Notes(db.Model):
    id = db.Column(db.Integer,  primary_key=True)
    title = db.Column(db.String(64), unique=True, nullable = False) # unique - уникальный, nullable - поле не должно быть пустым
    subtitle = db.Column(db.String(60), unique=True, nullable = False) # unique - уникальный, nullable - поле не должно быть пустым
    text = db.Column(db.String(120), unique=True, nullable = False) # unique - уникальный, nullable - поле не должно быть пустым

    def __repr__(self): # способ отображения класса в консоли
        return f'<Notes {self.id}>' # здесь указан формат

class Users(db.Model):
    id = db.Column(db.Integer,  primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable = False) # unique - уникальный, nullable - поле не должно быть пустым
    mail = db.Column(db.String(120), unique=True, nullable = False)
    password = db.Column(db.String(16), nullable = False)               # nullable - поле не должно быть пустым
    token = db.Column(db.String(50)) # это уникальный код, который генерируется для каждого пользователя при регистрации

#    def check_password(self, password):
#        return (password)

    def __repr__(self):
        return f"<users {self.id}>"


@app.before_request
def check_auth():
    global expiration
    if request.endpoint in ['login', 'register']: # Исключаем маршруты, которые не требуют аутентификации
        return  # Не выполнять проверку auth для страницы входа
    token = session.get('token', None)  # получаем токен пользователя из текущей сесии
    if not token or datetime.now() > expiration:
        return render_template('login_f_t5.html')  # Перенаправляем на страницу логина
    else:
        return

@app.route('/', methods=["GET", "POST"])
def index():
    notes2 = Notes.query.all()  # получить все данные из таблицы Notes
    for notes1 in notes2:
         print(notes1.id, notes1.title, notes1.subtitle, notes1.text)
    return render_template ('first_f_t5.html', notes2=notes2)

@app.route('/home')
def home():
    return render_template ('home_f_t5.html')

@app.route("/dp", methods=["GET", "POST"])
def pd():
    if request.method == "POST":
        title = request.form.get("title")
        subtitle = request.form.get('subtitle')
        text = request.form.get("text")
        if title and text:
            notes = Notes(title = title, subtitle = subtitle, text = text) # заносим данные в БД Notes
            db.session.add(notes)
            db.session.commit()
    return render_template("notes_f_t5.html")

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        mail = request.form.get("mail")
        password = request.form.get("password")
        password_hash = werkzeug.security.generate_password_hash(password) # шифрую пароль
        token = secrets.token_hex(16)  # Генерация токена
        if username and mail and password:
            users = Users(username = username, mail = mail, password = password_hash, token=token)  # заносим данные в БД Notes
            db.session.add(users)
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                return 'Такой пользователь уже есть'
            return redirect(url_for('login'))
    return render_template("register_f_t5.html", title='Register', password = 'password')

@app.route('/login', methods=['POST', 'GET'])
def login():
    global expiration
    if request.method == 'POST':

        password = request.form.get('password')
        user = Users.query.filter_by(username = request.form['username']).first() # отсортировали всю нашу почту и нашли подходящий запрос
        if user is not None and werkzeug.security.check_password_hash(user.password, password):
            token = user.token                                                      # берем из БД токен пользователя
            print('token = ', token)
            session['token'] = token
            expiration = datetime.now() + timedelta(minutes=5)                      # задаем продолжительность сессии
            return redirect(url_for('home'))
        else:
            return render_template('login_f_t5.html', error='Неверные учетные данные')
    else:
        return render_template('login_f_t5.html')

@app.route('/logout')
def logout():
    session.pop('token', None)
    return redirect(url_for('login'))

@app.route("/welcome")
def welcome():
    username = request.cookies.get('username', None)
    if username is not None:
        return f"Добро пожаловать, {username}!"
    else:
        return "Пожалуйста, войдите в систему!"

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__': #
    app.run(debug=True)