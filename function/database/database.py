from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from database.models import Base


engine = create_engine("mysql+pymysql://root:@localhost:3306/wordle",
                       pool_pre_ping=True, pool_recycle=3600, pool_size=5, max_overflow=10)
Base.metadata.create_all(engine)
SESSION = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def open_session() -> Iterator[Session]:
    """
    Context manager for database session.

    """
    session = SESSION()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
