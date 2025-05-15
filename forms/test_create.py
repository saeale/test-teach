from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (StringField, TextAreaField, BooleanField, SubmitField, RadioField, FieldList, FormField,
                     HiddenField, IntegerField)
from wtforms.validators import DataRequired, Optional, ValidationError, NumberRange, Regexp


class UniqueChoices(object):
    def __call__(self, form, field):
        choices = [v for v in field.data.split(';')]
        if len(choices) > 10:
            raise ValidationError('Вариантов должно быть не более 10')
        if len(choices) != len(set(choices)):
            raise ValidationError('Варианты должны быть уникальны')


class AnswerCorrect(object):
    def __call__(self, form, field):
        if not form.answer.data:
            raise ValidationError('Введите ответ')
        if int(form.question_type.data) == 1:
            choices = [v for v in form.choices.data.split(';')]
            if str(form.answer.data) not in choices:
                raise ValidationError('Ответ должен быть среди вариантов')
        if int(form.question_type.data) == 2:
            answers = [v for v in form.answer.data.split(';')]
            if len(answers) != len(set(answers)):
                raise ValidationError('Ответы должны быть разными')
            choices = [v for v in form.choices.data.split(';')]
            if not(set(answers) <= set(choices)):
                raise ValidationError('Ответы должны быть среди вариантов')


class QuestionCreateForm(FlaskForm):
    id = HiddenField('id')
    image_name = HiddenField()
    points = IntegerField('Баллы', validators=[NumberRange(min=1, message='Число должно быть положительным')])
    content = TextAreaField("Условие", validators=[Optional()])
    image = FileField('Выберите изображение (необязательно)')
    question_type = RadioField('Роль', validators=[Optional()], choices=[(0, 'Без вариантов'),
                                                                         (1, 'С вариантами, 1 ответ'),
                                                                         (2, 'С вариантами, несколько ответов')])
    choices = StringField('Варианты', validators=[UniqueChoices()])
    answer = StringField('Ответ', validators=[AnswerCorrect()])
    delete = SubmitField('Удалить', default=False)


class TestCreateForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    questions = FieldList(FormField(QuestionCreateForm))  # , render_kw={'data-prefix': 'question'})
    is_private = BooleanField("Личное")
    save_and_exit = SubmitField('Сохранить и выйти')
    go_to_edit = SubmitField('Перейти к редактированию')
    add_question = SubmitField('Добавить вопрос')  # , render_kw={'formnovalidate': True})
