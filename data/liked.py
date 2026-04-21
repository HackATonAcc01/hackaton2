import sqlalchemy
from .db_session import SqlAlchemyBase


class Liked(SqlAlchemyBase):
    __tablename__ = 'liked'

    login = sqlalchemy.Column(sqlalchemy.String,
                           primary_key=True)
    games = sqlalchemy.Column(sqlalchemy.String)
