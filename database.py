import sqlalchemy
from sqlalchemy.orm import declarative_base

from cfg import DB_FILE


class Dbase:
    base = declarative_base()
    engine: sqlalchemy.Engine = None

    @classmethod
    def init(cls) -> sqlalchemy.Engine:
        cls.engine = sqlalchemy.create_engine(
            "sqlite:////" + DB_FILE,
            connect_args={"check_same_thread": False},
            echo=False
            )
        
    @classmethod
    def vacuum(cls):
        conn = cls.engine.connect()
        try:
            conn.execute(sqlalchemy.text("VACUUM"))
            conn.commit()
        finally:
            conn.close()


class ThumbsMd(Dbase.base):
    __tablename__ = "thumbs"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    img150 = sqlalchemy.Column(sqlalchemy.LargeBinary)
    src = sqlalchemy.Column(sqlalchemy.Text, unique=True)
    size = sqlalchemy.Column(sqlalchemy.Integer)
    created = sqlalchemy.Column(sqlalchemy.Integer)
    modified = sqlalchemy.Column(sqlalchemy.Integer)
    collection = sqlalchemy.Column(sqlalchemy.Text)