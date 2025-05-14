import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Attempt(SqlAlchemyBase, UserMixin):
    __tablename__ = 'attempts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    student_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("students.id"))
    test_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tests.id"))
    start_date = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    complete_time = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    answers = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    score = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    student = orm.relationship("Student", back_populates='attempts')

    test = orm.relationship("Test", back_populates='attempts')
