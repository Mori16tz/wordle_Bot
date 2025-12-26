from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, default="")
    guesses = Column(Integer, default=5)
    streak = Column(Integer, default=0)
    answered = Column(Boolean, default=False)


engine = create_engine("sqlite:///data.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def add_user(id: int, username: str):
    new_user = User(id=id, username=username)
    session.add(new_user)
    session.commit()


def get_users() -> list[User]:
    return session.query(User).all()


def get_user(id: int) -> User:
    return session.query(User).filter(User.id == id).first()


def update_user(user: User):
    session.add(user)
    session.commit()
