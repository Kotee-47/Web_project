from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, send
import os  # Import the os module

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')  # Get SECRET_KEY from environment
socketio = SocketIO(app)

# Словарь для хранения комнат и пользователей в них.
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('create_room')
def handle_create_room(data):
    room_name = data['room']
    rooms[room_name] = {'users': []}  # Создаем комнату

    join_room(room_name)
    emit('room_created', {'room': room_name})
    print(f'Room "{room_name}" created')

@socketio.on('join_room')
def handle_join_room(data):
    room_name = data['room']
    username = data['username']
    if room_name in rooms:
        join_room(room_name)
        rooms[room_name]['users'].append(username)  # Добавляем пользователя в комнату
        emit('room_joined', {'room': room_name, 'username': username}, room=room_name)  # Оповещаем о присоединении.
        print(f'User "{username}" joined room "{room_name}"')
    else:
        emit('room_not_found', {'room': room_name})  # Обработка, если комнаты нет.

@socketio.on('send_message')
def handle_send_message(data):
    room_name = data['room']
    username = data['username']
    message = data['message']
    if room_name in rooms:
        emit('receive_message', {'username': username, 'message': message}, room=room_name)  # Отправляем сообщение всем в комнате
        print(f'Message sent in room "{room_name}": {username}: {message}')
    else:
        emit('room_not_found', {'room': room_name})

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)