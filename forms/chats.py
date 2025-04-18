from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class ChatForm(FlaskForm):
    title = StringField('Название группы', validators=[DataRequired()])
    content = TextAreaField("Описание")
    # is_private = BooleanField("Личное")
    submit = SubmitField('Применить')
