from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, RadioField, FieldList, FormField, SelectMultipleField, \
    widgets, HiddenField
from wtforms.validators import DataRequired, Optional, ValidationError


class UniqueChoices(object):
    def __call__(self, form, field):
        choices = [v for v in field.data.split(';')]
        if len(choices) != len(set(choices)):
            print('raise')
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
            if not (set(answers) <= set(choices)):
                raise ValidationError('Ответы должны быть среди вариантов')


class QuestionSolveForm(FlaskForm):
    id2 = HiddenField('id')
    answer0 = StringField('Введите ответ:')
    answer1 = RadioField('Выберите ответ:')
    answer2 = SelectMultipleField('User',
                                  widget=widgets.ListWidget(prefix_label=False),
                                  option_widget=widgets.CheckboxInput())


class TestSolveForm(FlaskForm):
    att_id = HiddenField()
    questions = FieldList(FormField(QuestionSolveForm))
    complete = SubmitField('Завершить')
