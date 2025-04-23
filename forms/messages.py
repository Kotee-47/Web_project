from flask_wtf import FlaskForm
import sqlalchemy
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class MessageForm(FlaskForm):
    content = TextAreaField("Сообщение")
    chat_id = TextAreaField("Чат")
    submit = SubmitField('Отправить')
