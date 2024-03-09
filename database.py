import threading

import sqlalchemy
from sqlalchemy.orm import (Session, declarative_base, scoped_session,
                            sessionmaker)

from cfg import cnf


class Dbase:
    engines_dict = {}
    base = declarative_base()

    @staticmethod
    def create_engine() -> sqlalchemy.Engine:
        print("create engine", threading.currentThread())
        return sqlalchemy.create_engine(
            "sqlite:////" + cnf.db_file,
            connect_args={"check_same_thread": False},
            echo=False
        )

    @staticmethod
    def cleanup_engine() -> None:
        current_thread_name = threading.current_thread().name

        if current_thread_name in Dbase.engines_dict:
            Dbase.engines_dict[current_thread_name].dispose()
            del Dbase.engines_dict[current_thread_name]

    @staticmethod
    def get_engine() -> sqlalchemy.Engine:
        current_thread_name = threading.current_thread().name

        if current_thread_name not in Dbase.engines_dict:
            Dbase.engines_dict[current_thread_name] = Dbase.create_engine()

        return Dbase.engines_dict[current_thread_name]

    @staticmethod
    def get_session() -> Session:
        Session = sessionmaker(bind=Dbase.get_engine())
        return scoped_session(Session)


class Queries:
    @staticmethod
    def bulk_insert(table, values):
        session = Dbase.get_session()
        try:
            insert_stmt = sqlalchemy.insert(table).values(values)
            session.execute(insert_stmt)
            session.commit()
        except Exception as e:
            print(f"Error occurred: {e}")
            session.rollback()
        finally:
            session.close()

    @staticmethod
    def bulk_queries(queries: list):
        session = Dbase.get_session()
        try:
            for q in queries:
                session.execute(q)
            session.commit()
        except Exception as e:
            print(f"Error occurred: {e}")
            session.rollback()
        finally:
            session.close()

    @staticmethod
    def get_query(query):
        session = Dbase.get_session()
        try:
            return session.execute(query)
        finally:
            session.close()

    @staticmethod
    def post_single_query(query):
        session = Dbase.get_session()
        try:
            session.execute(query)
            session.commit()
        finally:
            session.close()

    @staticmethod
    def vacuum():
        session = Dbase.get_session()
        try:
            session.execute(sqlalchemy.text("VACUUM"))
            session.commit()
        finally:
            session.close()


class ThumbsMd(Dbase.base):
    __tablename__ = "thumbs"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    img150 = sqlalchemy.Column(sqlalchemy.LargeBinary)
    src = sqlalchemy.Column(sqlalchemy.Text)
    size = sqlalchemy.Column(sqlalchemy.Integer)
    created = sqlalchemy.Column(sqlalchemy.Integer)
    modified = sqlalchemy.Column(sqlalchemy.Integer)
    collection = sqlalchemy.Column(sqlalchemy.Text)