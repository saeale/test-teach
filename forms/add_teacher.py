from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class TeacherAddForm(FlaskForm):
    teacher_login = StringField("Введите логин учителя", validators=[DataRequired()])
    add = SubmitField('Добавить')

