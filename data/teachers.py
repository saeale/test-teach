import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase

teachers_students = sqlalchemy.Table('teachers_students', SqlAlchemyBase.metadata,
                                     sqlalchemy.Column('teacher_id', sqlalchemy.Integer,
                                                       sqlalchemy.ForeignKey('teachers.id')),
                                     sqlalchemy.Column('student_id', sqlalchemy.Integer,
                                                       sqlalchemy.ForeignKey('students.id'))
                                     )


class Teacher(SqlAlchemyBase, UserMixin):
    __tablename__ = 'teachers'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    login = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    work = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    work_address = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    students = orm.relationship("Student", secondary='teachers_students', back_populates='teachers')

    tests = orm.relationship('Test', back_populates='teacher')

    user = orm.relationship("User", back_populates='teacher')

    def __repr__(self):
        return f'<User> {self.id} {self.name} {self.email}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
