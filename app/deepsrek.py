from flask import Flask, render_template, redirect, request, abort, url_for, session, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from forms.news import NewsForm
from forms.user import RegisterForm, LoginForm
from forms.test_create import TestCreateForm, QuestionCreateForm
from data.news import News
from data.students import Student
from data.teachers import Teacher
from data.tests import Test
from data.questions import Question
from data import db_session


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@login_manager.user_loader
def load_student(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(Student).get(user_id)


@login_manager.user_loader
def load_teacher(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(Teacher).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/blogs.db")
    app.run()


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление теста', form=form)


@app.route('/test', methods=['GET', 'POST'])
@login_required
def new_test():
    form = TestCreateForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        test = Test()
        test.title = form.title.data
        test.is_private = form.is_private.data
        test.teacher = current_user
        local_test = db_sess.merge(test)
        db_sess.commit()
        if form.go_to_edit.data:
            return redirect(f'/test/{local_test.id}')
        return redirect('/')
    return render_template('test_create.html', title='Создание теста', form=form)


@app.route('/test/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_test(id):
    db_sess = db_session.create_session()
    test = db_sess.query(Test).filter(Test.id == id, Test.teacher == current_user).first()

    if not test:
        abort(404)

    form = TestCreateForm()
    session_key = f'test_{id}_form'

    if request.method == "POST":
        if 'delete_question' in request.form:
            try:
                print(request.form)
                # Получаем ID вопроса из значения кнопки
                question_id = request.form[f'questions-{request.form["delete_question"]}-id']
                print('delete id =', question_id)
                if not question_id.isdigit():
                    print("Неверный ID вопроса")
                    return redirect(url_for('edit_test', id=id))

                question = db_sess.get(Question, int(question_id))

                if not question:
                    print("Вопрос не найден", "danger")
                    return redirect(url_for('edit_test', id=id))

                if question in test.questions:
                    test.questions.remove(question)

                if not question.tests:
                    db_sess.delete(question)

                db_sess.commit()
                print("Вопрос успешно удалён", "success")
            except Exception as e:
                db_sess.rollback()
                print(f"Ошибка удаления: {str(e)}", "danger")

            return redirect(url_for('edit_test', id=id))



        # Обработка добавления вопроса
        if form.add_question.data:
            new_question = Question(
                content="Новый вопрос",
                question_type=0,
                answer=""
            )
            db_sess.add(new_question)
            test.questions.append(new_question)
            db_sess.commit()  # Фиксируем сразу
            db_sess.refresh(new_question)

            # Обновляем форму из БД
            return redirect(url_for('edit_test', id=id))

        # Обработка сохранения
        if form.validate_on_submit():
            print("\n=== FORM VALIDATION PASSED ===")
            try:
                test.title = form.title.data
                test.is_private = form.is_private.data

                # Обрабатываем вопросы
                for q_data in form.questions.data:
                    question = db_sess.get(Question, int(q_data['id']))
                    if question:
                        question.content = q_data['content']
                        question.question_type = int(q_data['question_type'])
                        question.choices = q_data['choices']
                        question.answer = q_data['answer']

                db_sess.commit()
                print('Изменения сохранены')

                if form.save_and_exit.data:
                    return redirect('/')
                return redirect(url_for('edit_test', id=id))

            except Exception as e:
                db_sess.rollback()
                print("\n!!! DATABASE ERROR !!!", str(e))
                flash('Ошибка сохранения: ' + str(e), 'danger')

    # GET-запрос или перезагрузка
    if request.method == "GET":
        # if session.get(session_key):
        #     form.process(data=session[session_key])
        #     session.pop(session_key)
        # else:

        # Инициализация формы
        form.title.data = test.title
        form.is_private.data = test.is_private

        # Очистка и заполнение вопросов
        while form.questions:
            form.questions.pop_entry()

        db_sess.refresh(test)

        for q in test.questions:
            q_form = QuestionCreateForm()
            q_form.id.data = q.id  # Ключевая строка!
            q_form.content.data = q.content
            q_form.question_type.data = q.question_type
            q_form.choices.data = q.choices
            q_form.answer.data = q.answer
            q_form.delete.data = False
            form.questions.append_entry(q_form.data)
            print(f"Loaded question ID: {q.id}")

    return render_template('test_edit.html', form=form, test=test)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter((News.user == current_user) | (News.is_private != True))
    else:
        news = db_sess.query(News).filter(News.is_private != True)
    return render_template("index.html", news=news)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm(role=0)
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if (db_sess.query(Student).filter(Student.login == form.login.data).first() or
                db_sess.query(Teacher).filter(Teacher.login == form.login.data).first()):
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        if form.role.data == 0:
            user = Student(
                login=form.login.data,
                name=form.name.data,
                email=form.email.data,
                about=form.about.data
            )
            user.set_password(form.password.data)
            db_sess.add(user)
        else:
            user = Teacher(
                login=form.login.data,
                name=form.name.data,
                email=form.email.data,
                about=form.about.data
            )
            user.set_password(form.password.data)
            db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(Student).filter(Student.login == form.login.data).first()
        if not user:
            user = db_sess.query(Teacher).filter(Teacher.login == form.login.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


if __name__ == '__main__':
    main()
