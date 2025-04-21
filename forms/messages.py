from flask_wtf import FlaskForm
import sqlalchemy
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class MessageForm(FlaskForm):
    content = TextAreaField("Описание", validators=[DataRequired()])
    chat_id = TextAreaField("Чат", validators=[DataRequired()])
    submit = SubmitField('Применить')
