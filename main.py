from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, send
import os
import sqlite3
import bcrypt  # для хэширования

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
socketio = SocketIO(app)

# Конфигурация базы данных SQLite для чата
DATABASE = 'chat.db'

# Конфигурация базы данных SQLite для пользователей
USER_DATABASE = 'users.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_user_db_connection():
    conn = sqlite3.connect(USER_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

rooms = {}


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('authenticate')
def handle_authentication(data):
    username = data['username']
    password = data['password']

    conn = get_user_db_connection()
    cursor = conn.cursor()

    # существует ли пользователь с таким именем
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user:
        # проверяем пароль
        if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')): # Проверяем хеш пароля
            emit('auth_success', {'username': username})
            print(f'User "{username}" authenticated successfully.')
        else:
            emit('auth_error', {'message': 'Неверный пароль.'})
            print(f'Authentication failed for user "{username}".')
    else:
        # регистрируем
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') # Хешируем пароль
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            emit('auth_success', {'username': username})
            print(f'User "{username}" registered and authenticated successfully.')
        except sqlite3.IntegrityError:
            emit('auth_error', {'message': 'Имя пользователя уже занято.'})
            print(f'Registration failed for user "{username}". Username already exists.')
        except Exception as e:
            emit('auth_error', {'message': f'Ошибка регистрации: {str(e)}'})
            print(f'Registration failed for user "{username}". Error: {str(e)}')

    conn.close()


@socketio.on('create_room')
def handle_create_room(data):
    room_name = data['room']
    rooms[room_name] = {'users': []}

    join_room(room_name)
    emit('room_created', {'room': room_name})
    print(f'Room "{room_name}" created')


@socketio.on('join_room')
def handle_join_room(data):
    room_name = data['room']
    username = data['username']
    if room_name in rooms:
        join_room(room_name)
        rooms[room_name]['users'].append(username)
        emit('room_joined', {'room': room_name, 'username': username}, room=room_name)

        conn = get_db_connection()
        cursor = conn.cursor()
        sql_query = "SELECT username, message, timestamp FROM messages WHERE room_name = ?"
        print(f"SQL Query: {sql_query}, Room Name: {room_name}")
        cursor.execute(sql_query, (room_name,))
        messages = cursor.fetchall()
        print(f"Messages from DB: {messages}")
        conn.close()


        for message in messages:
            message_data = {'username': message['username'], 'message': message['message'],
                            'timestamp': message['timestamp']}
            print(f"Emitting message: {message_data}, Room: {request.sid}")
            emit('receive_message', message_data, room=request.sid)

        print(f'User "{username}" joined room "{room_name}"')
    else:
        emit('room_not_found', {'room': room_name})


@socketio.on('send_message')
def handle_send_message(data):
    room_name = data['room']
    username = data['username']
    message = data['message']
    if room_name in rooms:
        # Сохраняем сообщение
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (room_name, username, message) VALUES (?, ?, ?)",
                       (room_name, username, message))
        conn.commit()

        # Получаем timestamp только что добавленного сообщения
        cursor.execute("SELECT timestamp FROM messages WHERE room_name = ? AND username = ? AND message = ? ORDER BY id DESC LIMIT 1",
                       (room_name, username, message))
        message_data = cursor.fetchone()
        timestamp = message_data['timestamp'] if message_data else None

        conn.close()

        emit('receive_message', {'username': username, 'message': message, 'timestamp': timestamp}, room=room_name)
        print(f'Message sent in room "{room_name}": {username}: {message}')
    else:
        emit('room_not_found', {'room': room_name})

@socketio.on('clear_chat')
def handle_clear_chat(data):
    print("Received clear_chat event for room:", data['room'])
    room_name = data['room']
    if room_name in rooms:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE room_name = ?", (room_name,))
            conn.commit()
            conn.close()

            emit('chat_cleared', room=room_name)
            print(f'Chat cleared in room "{room_name}"')
        except Exception as e:
            print(f"Error clearing chat: {e}")
    else:
        print(f'Room "{room_name}" not found.')

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)