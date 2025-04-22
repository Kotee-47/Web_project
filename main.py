from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, send
import os
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
socketio = SocketIO(app)

DATABASE = 'chat.db'

USER_DATABASE = 'users.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_user_db_connection():
    conn = sqlite3.connect(USER_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def migrate_timestamp_column():
    conn = get_db_connection()
    if conn is None:
        print("Failed to get database connection. Migration aborted.")
        return

    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        timestamp_exists = False
        for column in columns:
            if column['name'] == 'timestamp':
                timestamp_exists = True
                break

        if not timestamp_exists:
            print("Column 'timestamp' does not exist. Creating it...")
            cursor.execute("ALTER TABLE messages ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP")
            print("Column 'timestamp' added successfully.")
        else:
            print("Column 'timestamp' already exists.")

        conn.commit()
        print("Migration completed successfully.")

    except sqlite3.OperationalError as e:
        # Если таблицы не существует(чтобы был except)
        if "no such table: messages" in str(e):
            print(
                "Table 'messages' does not exist.  Please create the table manually or adjust the code to create it.")
        else:
            print(f"An unexpected error occurred: {e}")

    finally:
        if conn:
            conn.close()



migrate_timestamp_column()

# Словарь для хранения комнат и пользователей в них.
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

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user:
        if user['password'] == password:
            emit('auth_success', {'username': username})
            print(f'User "{username}" authenticated successfully.')
        else:
            emit('auth_error', {'message': 'Неверный пароль.'})
            print(f'Authentication failed for user "{username}".')
    else:
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
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
            message_data = {'username': message['username'], 'message': message['message']}
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
        # Сохранение в базу данных
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (room_name, username, message) VALUES (?, ?, ?)",
                       (room_name, username, message))
        conn.commit()
        conn.close()

        emit('receive_message', {'username': username, 'message': message}, room=room_name)
        print(f'Message sent in room "{room_name}": {username}: {message}')
    else:
        emit('room_not_found', {'room': room_name})


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)