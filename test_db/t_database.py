import threading

import sqlalchemy
from sqlalchemy.orm import Session, scoped_session, sessionmaker, declarative_base
import os

class Dbase:
    engines_dict = {}
    base = declarative_base()


    @staticmethod
    def create_engine() -> sqlalchemy.Engine:
        db_path = os.path.dirname(__file__) + "/test_db.db"
        return sqlalchemy.create_engine(
            "sqlite:////" + db_path,
            connect_args={"check_same_thread": False},
            echo=False)


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
    def post_bulk_insert(table, values):
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
    def post_bulk_queries(queries: list):
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
    def post_single_query(query):
        session = Dbase.get_session()
        try:
            session.execute(query)
            session.commit()
        finally:
            session.close()

    @staticmethod
    def get_query(query):
        session = Dbase.get_session()
        try:
            return session.execute(query)
        finally:
            session.close()


class TestMd(Dbase.base):
    __tablename__ = "test"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    src = sqlalchemy.Column(sqlalchemy.Text)
    size = sqlalchemy.Column(sqlalchemy.Integer)
    created = sqlalchemy.Column(sqlalchemy.Integer)


Dbase.base.metadata.create_all(Dbase.get_engine())