import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase

tests_questions = sqlalchemy.Table('tests_questions', SqlAlchemyBase.metadata,
                                   sqlalchemy.Column('test_id', sqlalchemy.Integer,
                                                     sqlalchemy.ForeignKey('tests.id')),
                                   sqlalchemy.Column('question_id', sqlalchemy.Integer,
                                                     sqlalchemy.ForeignKey('questions.id'))
                                   )


class Test(SqlAlchemyBase):
    __tablename__ = 'tests'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    teacher_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("teachers.id"))
    question_number = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    teacher = orm.relationship('Teacher', back_populates='tests')

    attempts = orm.relationship("Attempt", back_populates='test')

    questions = orm.relationship("Question", secondary='tests_questions', back_populates='tests')