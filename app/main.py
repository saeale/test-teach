from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from forms.news import NewsForm
from forms.user import RegisterForm, LoginForm
from forms.test_create import TestCreateForm
from data.news import News
from data.students import Student
from data.teachers import Teacher
from data.tests import Test
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


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html', title='Редактирование теста', form=form)


@app.route('/test/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_test(id):
    form = TestCreateForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        test = db_sess.query(Test).filter(Test.id == id, Test.teacher == current_user).first()
        if test:
            form.title.data = test.title
            for question in test.questions:
                form.questions.append_entry(question)
            form.is_private.data = test.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        test = db_sess.query(Test).filter(Test.id == id, Test.teacher == current_user).first()
        if test:
            if form.add_question.data:
                form.questions.append_entry()
            test.title = form.title.data
            test.questions = form.questions.data
            test.is_private = form.is_private.data
            db_sess.commit()
            if form.add_question.data:
                return redirect(f'/test/{id}')
            return redirect('/')
        else:
            abort(404)
    return render_template('test_edit.html', title='Редактирование теста', form=form)


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
