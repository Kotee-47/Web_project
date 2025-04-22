from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from forms.chats import ChatForm
from forms.messages import MessageForm
from forms.user import RegisterForm, LoginForm
from data.chats import Chats
from data.messages import Messages
from data.users import User
from data import db_session
from flask import make_response

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'neurosamaararar'


def load_messages_from_db(chat_id):
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        messages = db_sess.query(Messages).filter(Messages.chat_id == chat_id)
        mes_new = []
        for i in messages:
            mes_new.append({'sender':(i.user_id.split('%8%')[1]), 'content':i.content, 'date':(str(i.created_date)[:-7])})
    else:
        mes_new = ['система', 'войдите в аккаунт', '00:00']
    return mes_new


def main():
    db_session.global_init("db/main.db")
    app.run()


@app.route('/create_chat', methods=['GET', 'POST'])
@login_required
def create_chat():
    form = ChatForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        chats = Chats()
        chats.title = form.title.data
        chats.content = form.content.data
        current_user.chats.append(chats)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('chats.html', title='Создание чата', form=form)


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
    form = MessageForm()
    if request.method == 'POST':
        db_sess = db_session.create_session()
        if form.content.data:
            messages = Messages(
                content=form.content.data,
                chat_id=str(chat_id),
                user_id=(str(current_user.get_id()) + '%8%' + str(current_user.get_name()))
            )
            # messages.content = form.content.data
            # messages.chat_id = chat_id
            db_sess.add(messages)
            db_sess.commit()
        messages = load_messages_from_db(chat_id)
        return render_template('index.html', messages=messages, chat_id=chat_id, form=form)
    messages = load_messages_from_db(chat_id)
    return render_template('index.html', messages=messages, chat_id=chat_id, form=form)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


if __name__ == '__main__':
    main()
