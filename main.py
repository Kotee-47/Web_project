from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from forms.user import RegisterForm, LoginForm
from data.users import User
from data import db_session
from flask import make_response

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'neurosamaararar'


# Функция для записи сообщений в файл
def save_message_to_file(chat_id, msg):
    with open(f'db/messages/messages_{chat_id}.txt', 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

# Функция для чтения сообщений из файла
def load_messages_from_file(chat_id):
    try:
        with open(f'db/messages/messages_{chat_id}.txt', 'r', encoding='utf-8') as f:
            return f.readlines()
    except FileNotFoundError:
        return []


def main():
    db_session.global_init("db/main.db")
    app.run()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


# 7. И, наконец, сделаем обработчик адреса /login:
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/', methods=['GET', 'POST'])
def index():
    chat_id = request.args.get('chat_id', 'default')  # Получаем идентификатор чата из параметров URL
    if request.method == 'POST':
        if 'message' in request.form:
            message = request.form['message']
            save_message_to_file(chat_id, message)  # Сохраняем сообщение в файл
            return redirect(url_for('index', chat_id=chat_id))  # Перенаправляем на ту же страницу
        elif 'chat_id' in request.form:
            new_chat_id = request.form['chat_id']
            return redirect(url_for('index', chat_id=new_chat_id))  # Перенаправляем на новый чат

    messages = load_messages_from_file(chat_id)
    return render_template('index.html', messages=messages, chat_id=chat_id)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


if __name__ == '__main__':
    main()
