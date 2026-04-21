import sqlalchemy

from .db_session import SqlAlchemyBase


class Prices(SqlAlchemyBase):
    __tablename__ = 'prices'

    app_id = sqlalchemy.Column(sqlalchemy.INT,
                           primary_key=True)
    all_paths = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    last_modification = sqlalchemy.Column(sqlalchemy.String)