import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    role = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    role_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    student = orm.relationship("Student", back_populates='user')
    teacher = orm.relationship("Teacher", back_populates='user')

    def __repr__(self):
        return f'<User> {self.id} {self.name} {self.email}'
