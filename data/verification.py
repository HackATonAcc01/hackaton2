import sqlalchemy

from .db_session import SqlAlchemyBase


class Verification(SqlAlchemyBase):
    __tablename__ = 'ver'

    email = sqlalchemy.Column(sqlalchemy.String,
                           primary_key=True)
    code = sqlalchemy.Column(sqlalchemy.String)
