from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run()
