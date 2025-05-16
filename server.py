import os
from shutil import rmtree
from datetime import datetime
from flask import Flask, render_template, redirect, request, abort, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from yandex_get_address import get_photo
from forms.add_teacher import TeacherAddForm
from forms.user import RegisterForm, LoginForm
from forms.test_create import TestCreateForm, QuestionCreateForm
from forms.test_solve import TestSolveForm
from data.students import Student
from data.teachers import Teacher
from data.tests import Test
from data.users import User
from data.attempts import Attempt
from data.questions import Question
from data import db_session


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = '/static'
UPLOAD_FILES_PATH = 'static/tasks/'
UPLOAD_MAPS_PATH = 'static/maps/'

app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

dirname = os.path.dirname(os.path.abspath(__file__))


# очистка пустых попыток
def clear_empty_attempts():
    db_sess = db_session.create_session()
    attempts = db_sess.query(Attempt).filter(Attempt.complete_time == None)
    if attempts:
        for attempt in attempts:
            db_sess.delete(attempt)
        db_sess.commit()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    if user.role == 0:
        return db_sess.query(Student).filter(Student.id == user.role_id).first()
    else:
        return db_sess.query(Teacher).filter(Teacher.id == user.role_id).first()


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/blogs.db")
    app.run()


# создание теста
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
        test.created_date = datetime.now().strftime('%d/%m/%y %H:%M:%S')
        local_test = db_sess.merge(test)
        db_sess.commit()
        if form.go_to_edit.data:
            return redirect(f'/test/{local_test.id}')
        return redirect('/')
    return render_template('test_create.html', title='Создание теста', form=form)


# удаление теста
@app.route('/test_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def test_delete(id):
    db_sess = db_session.create_session()
    test = db_sess.query(Test).filter(Test.id == id, Test.teacher == current_user).first()
    if test:
        questions = test.questions
        for question in questions:
            db_sess.delete(question)
        attempts = test.attempts
        for attempt in attempts:
            db_sess.delete(attempt)
        db_sess.delete(test)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


# (для ученика) удаление учителя
@app.route('/teacher_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def teacher_delete(id):
    if current_user.__class__.__name__ != 'Student':
        abort(404)
    db_sess = db_session.create_session()
    teacher = db_sess.query(Teacher).filter(Teacher.id == id).first()
    curr = db_sess.query(Student).filter(Student.id == current_user.id).first()
    if teacher and teacher in curr.teachers:
        curr2 = db_sess.merge(curr)
        curr2.teachers.remove(teacher)
        db_sess.commit()
    return redirect('/teachers')


# (для учителя) удаление ученика
@app.route('/student_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def student_delete(id):
    if current_user.__class__.__name__ != 'Teacher':
        abort(404)
    db_sess = db_session.create_session()
    student = db_sess.query(Student).filter(Student.id == id).first()
    curr = db_sess.query(Teacher).filter(Teacher.id == current_user.id).first()
    if student and student in curr.students:
        curr2 = db_sess.merge(curr)
        curr2.students.remove(student)
        db_sess.commit()
    return redirect('/students')


# редактирование теста
@app.route('/test/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_test(id):
    if current_user.__class__.__name__ != 'Teacher':
        abort(404)
    db_sess = db_session.create_session()
    test = db_sess.query(Test).filter(Test.id == id, Test.teacher == current_user).first()
    if not test:
        abort(404)

    form = TestCreateForm()

    if request.method == "POST":
        # обработка сохранения данных из формы в бд
        if form.is_submitted():
            try:
                test.title = form.title.data
                test.is_private = form.is_private.data

                for q_data in form.questions.data:
                    question = db_sess.get(Question, int(q_data['id']))
                    if question:
                        question.content = q_data['content']
                        question.points = q_data['points']
                        question.question_type = int(q_data['question_type'])
                        question.choices = q_data['choices']
                        question.answer = q_data['answer']

                db_sess.commit()

                if form.save_and_exit.data:  # сохранить и выйти
                    if form.validate():
                        return redirect('/')
                elif form.add_question.data:  # добавить вопрос
                    new_question = Question(
                        content="Новый вопрос",
                        points=1,
                        question_type=0,
                        answer=""
                    )
                    db_sess.add(new_question)
                    test.questions.append(new_question)
                    db_sess.commit()
                    db_sess.refresh(new_question)
                elif 'delete_question' in request.form:  # удалить вопрос
                    try:
                        question_id = request.form["delete_question"]
                        if not question_id.isdigit():
                            return redirect(url_for('edit_test', id=id))

                        question = db_sess.get(Question, int(question_id))

                        if not question:
                            return redirect(url_for('edit_test', id=id))

                        if question in test.questions:
                            test.questions.remove(question)

                        if not question.tests:
                            db_sess.delete(question)

                        db_sess.commit()
                    except Exception as e:
                        db_sess.rollback()
                elif 'add_image' in request.form:  # добавить картинку
                    question_id, index0 = eval(request.form["add_image"])
                    question = db_sess.get(Question, int(question_id))
                    q_form = form.questions.entries[index0]
                    if not question:
                        abort(404)

                    f = q_form.image.data
                    if f:
                        filename = secure_filename(f.filename)
                        newpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               f'static/tasks/{question.id}/')
                        if os.path.exists(newpath):
                            rmtree(newpath)
                        os.makedirs(newpath)
                        f.save(os.path.join(newpath, filename))
                        question.image = filename
                        db_sess.commit()

                elif 'delete_image' in request.form:  # удалить картинку
                    question_id = request.form["delete_image"]
                    question = db_sess.get(Question, int(question_id))
                    if not question:
                        abort(404)
                    newpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           f'static/tasks/{question.id}/')
                    if os.path.exists(newpath):
                        rmtree(newpath)
                    question.image = None
                    db_sess.commit()

                return redirect(url_for('edit_test', id=id))

            except Exception as e:
                db_sess.rollback()

    # получение данных из бд в форму
    if request.method == "GET":

        form.title.data = test.title
        form.is_private.data = test.is_private

        # очистка и заполнение вопросов
        while form.questions:
            form.questions.pop_entry()

        db_sess.refresh(test)

        for q in test.questions:
            q_form = QuestionCreateForm()
            q_form.id.data = q.id
            q_form.image_name.data = q.image
            q_form.content.data = q.content
            q_form.points.data = q.points
            q_form.question_type.data = q.question_type
            q_form.choices.data = q.choices
            q_form.answer.data = q.answer
            q_form.delete.data = False
            form.questions.append_entry(q_form.data)

    return render_template('test_edit.html', form=form, test_id=id)


# попытка прохождения учеником
@app.route('/test/<int:id>/attempt', methods=['GET', 'POST'])
@login_required
def test_attempt(id):
    if current_user.__class__.__name__ != 'Student':
        abort(404)
    db_sess = db_session.create_session()
    test = db_sess.query(Test).filter(Test.id == id).first()
    if not test:
        abort(404)
    if test.is_private:
        abort(404)
    if current_user not in test.teacher.students:
        abort(404)

    form = TestSolveForm(request.form)

    if request.method == "GET":
        attempt = Attempt()
        attempt.student = current_user
        attempt.test = test
        attempt.start_date = datetime.now().strftime('%d/%m/%y %H:%M:%S')
        att_merge = db_sess.merge(attempt)
        db_sess.commit()
        db_sess.refresh(att_merge)

        while form.questions:
            form.questions.pop_entry()

        form.att_id.data = att_merge.id

        for q in test.questions:
            form.questions.append_entry()
            form.questions.entries[-1].id2.data = q.id
            if q.question_type == 1:
                form.questions.entries[-1].answer1.choices = [(i, i) for i in q.choices.split(';')]
            if q.question_type == 2:
                form.questions.entries[-1].answer2.choices = [(i, i) for i in q.choices.split(';')]

    if request.method == "POST":
        attempt = db_sess.query(Attempt).filter(Attempt.id == form.att_id.data).first()
        if not attempt:
            abort(404)
        answers = []
        # Обрабатываем вопросы
        for q_data in form.questions.data:
            question = db_sess.get(Question, int(q_data['id2']))
            if question:
                if question.question_type == 0:
                    answers.append(q_data['answer0'] or '')
                elif question.question_type == 1:
                    answers.append(q_data['answer1'] or '')
                elif question.question_type == 2:
                    answers.append(';'.join(q_data['answer2']) or '')
        if len(answers) > 0:
            attempt.answers = '\n'.join(answers)
        else:
            attempt.answers = ''
        attempt.complete_time = datetime.now().strftime('%d/%m/%y %H:%M:%S')
        db_sess.commit()
        return redirect(url_for('attempt_result', id=attempt.id))

    return render_template('attempt.html', form=form, test=test)


# проверка и результаты попытки
@app.route('/attempt/<int:id>/result', methods=['GET', 'POST'])
@login_required
def attempt_result(id):
    db_sess = db_session.create_session()
    attempt = db_sess.query(Attempt).filter(Attempt.id == id).first()
    if not attempt:
        abort(404)
    if current_user.__class__.__name__ == 'Student' and attempt.student != current_user:
        abort(404)
    if current_user.__class__.__name__ == 'Teacher' and attempt.test.teacher != current_user:
        abort(404)

    delta = str(datetime.strptime(attempt.complete_time, '%d/%m/%y %H:%M:%S') -
                datetime.strptime(attempt.start_date, '%d/%m/%y %H:%M:%S'))

    if request.method == "GET":
        answers = attempt.answers.split('\n')
        corr_answers = []
        points = []
        total_points = 0

        count = 0
        for q in attempt.test.questions:
            total_points += q.points
            p = 0
            if q.question_type == 0 or q.question_type == 1:
                if answers[count] == q.answer:
                    p = q.points
            if q.question_type == 2:
                if set(answers[count].split(';')) == set(q.answer.split(';')):
                    p = q.points
            points.append(p)
            corr_answers.append(q.answer)
            count += 1

    return render_template('result.html', delta=delta, attempt=attempt, answers=answers,
                           corr_answers=corr_answers, points=points, total_points=total_points)


# (для ученика) учителя
@app.route("/teachers", methods=['GET', 'POST'])
@login_required
def teachers():
    db_sess = db_session.create_session()
    if current_user.__class__.__name__ == 'Student':
        form = TeacherAddForm()
        curr = db_sess.query(Student).filter(Student.id == current_user.id).first()
        teachers = db_sess.query(Teacher).filter(Teacher.id.in_(teacher.id for teacher in curr.teachers))
        if request.method == "POST":
            if form.validate_on_submit():
                new_teacher_login = form.teacher_login.data
                new_teacher = db_sess.query(Teacher).filter(Teacher.login == new_teacher_login).first()
                if not new_teacher:
                    return render_template("teachers.html", teachers=teachers,
                                           message='Учителя с таким логином не существует', form=form)
                if new_teacher in curr.teachers:
                    return render_template("teachers.html", teachers=teachers,
                                           message='Вы уже добавили этого учителя', form=form)
                current_user2 = db_sess.merge(curr)
                local_teacher = db_sess.merge(new_teacher)
                current_user2.teachers.append(local_teacher)
                db_sess.commit()
                teachers = db_sess.query(Teacher).filter(
                    Teacher.id.in_(teacher.id for teacher in current_user2.teachers))
    else:
        abort(404)
    return render_template("teachers.html", teachers=teachers, message='', form=form)


# (для учителя) ученики
@app.route("/students", methods=['GET', 'POST'])
@login_required
def students():
    db_sess = db_session.create_session()
    if current_user.__class__.__name__ == 'Teacher':
        curr = db_sess.query(Teacher).filter(Teacher.id == current_user.id).first()
        students = db_sess.query(Student).filter(Student.id.in_(student.id for student in curr.students))
    else:
        abort(404)
    return render_template("students.html", students=students, message='')


# страница учителя
@app.route("/teachers/<int:id>", methods=['GET', 'POST'])
def teachers_page(id):
    db_sess = db_session.create_session()
    teacher = db_sess.query(Teacher).filter(Teacher.id == id).first()
    if not teacher:
        abort(404)
    tests = db_sess.query(Test).filter(Test.teacher == teacher)
    return render_template("teacher_page.html", teacher=teacher, tests=tests)


# страница ученика (для его учителя)
@app.route("/students/<int:id>", methods=['GET', 'POST'])
@login_required
def students_page(id):
    if current_user.__class__.__name__ != 'Teacher' and current_user.id != id:
        abort(404)
    db_sess = db_session.create_session()
    student = db_sess.query(Student).filter(Student.id == id).first()
    if not student:
        abort(404)
    clear_empty_attempts()
    if current_user.__class__.__name__ == 'Teacher':
        attempts = db_sess.query(Attempt).join(Test).filter(Attempt.student == student, Test.teacher == current_user)
    else:
        attempts = db_sess.query(Attempt).filter(Attempt.student == student)
    return render_template("student_page.html", student=student, attempts=attempts)


# попытки (учеников или свои)
@app.route("/attempts", methods=['GET', 'POST'])
@login_required
def show_attempts():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        clear_empty_attempts()
        if current_user.__class__.__name__ == 'Teacher':
            attempts = db_sess.query(Attempt).join(Test).filter(Test.teacher == current_user)
        if current_user.__class__.__name__ == 'Student':
            curr = db_sess.query(Student).filter(Student.id == current_user.id).first()
            attempts = db_sess.query(Attempt).join(Test).join(Teacher).filter(Teacher.id.in_(teacher.id for teacher in curr.teachers), Test.is_private != True)
        return render_template("attempts.html", attempts=attempts, message='Все попытки')
    else:
        abort(404)


# попытки для определённого теста
@app.route("/attempts/<int:id>", methods=['GET', 'POST'])
@login_required
def show_attempts_test(id):
    db_sess = db_session.create_session()
    test = db_sess.query(Test).filter(Test.id == id).first()
    if current_user.is_authenticated:
        clear_empty_attempts()
        if current_user.__class__.__name__ == 'Teacher' and current_user == test.teacher:
            attempts = db_sess.query(Attempt).join(Test).filter(Test.id == id)
        elif current_user.__class__.__name__ == 'Student' and current_user in test.teacher.students and not test.is_private:
            attempts = db_sess.query(Attempt).join(Test).filter(Test.id == id, Attempt.student == current_user)
        else:
            abort(404)
        return render_template("attempts.html", attempts=attempts, message=f'Попытки на тест "{test.title}" (id {id})')
    else:
        abort(404)


# главная страгица: доступные тесты для ученика и свои тесты для учителя
@app.route("/", methods=['GET', 'POST'])
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        if current_user.__class__.__name__ == 'Teacher':
            tests = db_sess.query(Test).filter(Test.teacher == current_user)
        if current_user.__class__.__name__ == 'Student':
            curr = db_sess.query(Student).filter(Student.id == current_user.id).first()
            # tests = db_sess.query(Test).filter(Test.teacher.in_(current_user.teachers), News.is_private != True)
            tests = db_sess.query(Test).join(Teacher).filter(Teacher.id.in_(teacher.id for teacher in curr.teachers), Test.is_private != True)
        return render_template("index.html", tests=tests, message='Тесты')
    else:
        return render_template("index.html", message='Зарегистрируйтесь или войдите, чтобы продолжить')


@app.route('/register', methods=['GET', 'POST'])
def register():
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
        if int(form.role.data) == 0:
            student = Student(
                login=form.login.data,
                name=form.name.data,
                email=form.email.data,
                about=form.about.data,
                work=form.work.data,
                work_address=form.work_address.data,
                created_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
            )
            student.set_password(form.password.data)
            db_sess.add(student)
            db_sess.commit()
            user = User(role=0,
                        role_id=db_sess.query(Student).filter(Student.login == form.login.data).first().id)
            student.user = user
            db_sess.add(user)
            if student.work_address:
                newpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       f'static/maps/students/{student.id}/')
                if os.path.exists(newpath):
                    rmtree(newpath)
                os.makedirs(newpath)
                get_photo(student.work_address, os.path.join(newpath, 'map.png'))
        else:
            teacher = Teacher(
                login=form.login.data,
                name=form.name.data,
                email=form.email.data,
                about=form.about.data,
                work=form.work.data,
                work_address=form.work_address.data,
                created_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
            )
            teacher.set_password(form.password.data)
            db_sess.add(teacher)
            db_sess.commit()
            user = User(role=1,
                        role_id=db_sess.query(Teacher).filter(Teacher.login == form.login.data).first().id)
            teacher.user = user
            db_sess.add(user)
            if teacher.work_address:
                newpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       f'static/maps/teachers/{teacher.id}/')
                if os.path.exists(newpath):
                    rmtree(newpath)
                os.makedirs(newpath)
                get_photo(teacher.work_address, os.path.join(newpath, 'map.png'))
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        role = 0
        user = db_sess.query(Student).filter(Student.login == form.login.data).first()
        if not user:
            role = 1
            user = db_sess.query(Teacher).filter(Teacher.login == form.login.data).first()
        if user and user.check_password(form.password.data):
            true_user = db_sess.query(User).filter(User.role == role, User.role_id == user.id).first()
            if not true_user:
                abort(404)
            login_user(true_user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


if __name__ == '__main__':
    main()
