from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField, RadioField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    role = RadioField('Роль', validators=[DataRequired()], choices=[(0, 'Ученик'), (1, 'Учитель')])
    email = EmailField('Почта (необязательно)')
    work = StringField('Место работы/учёбы (необязательно)')
    work_address = StringField('Адрес места работы/учёбы (необязательно)')
    about = TextAreaField("Немного о себе (необязательно)")
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
