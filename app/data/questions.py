import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Question(SqlAlchemyBase):
    __tablename__ = 'questions'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True, default='')
    points = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    image = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    question_type = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, default=0)
    choices = sqlalchemy.Column(sqlalchemy.String, nullable=True, default='')
    answer = sqlalchemy.Column(sqlalchemy.String, nullable=True, default='')

    tests = orm.relationship("Test", secondary='tests_questions', back_populates='questions')