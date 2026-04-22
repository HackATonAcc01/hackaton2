import sqlalchemy
from .db_session import SqlAlchemyBase


class Liked(SqlAlchemyBase):
    __tablename__ = 'liked'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)
    route_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    checkpoint_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=sqlalchemy.func.now())