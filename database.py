import random
from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column()
    guesses: Mapped[int] = mapped_column(default=5)
    streak: Mapped[int] = mapped_column(default=0)
    answered: Mapped[bool] = mapped_column(default=False)


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column()
    language: Mapped[str] = mapped_column(default="en")
    potential_answer: Mapped[bool] = mapped_column(default=False)
    word_history_entries: Mapped[list["WordHistory"]
                                 ] = relationship(back_populates="word")


class WordHistory(Base):
    __tablename__ = "word_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"))
    date: Mapped[datetime.date] = mapped_column(nullable=False)
    word: Mapped[Word] = relationship(back_populates="word_history_entries")


engine = create_engine("sqlite:///data.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def add_user(id: int, username: str) -> None:
    new_user = User(id=id, username=username)
    session.add(new_user)
    session.commit()


def get_users() -> list[User]:
    return session.query(User).all()


def get_user(id: int) -> User:
    return session.query(User).filter(User.id == id).first()


def update_user(user: User) -> None:
    session.add(user)
    session.commit()


def add_word(word: str, potential_answer: bool) -> None:
    new_word = Word(word=word, potential_answer=potential_answer)
    session.add(new_word)
    session.commit()


def get_potentials(language="en") -> list[Word]:
    return session.query(Word).filter(Word.potential_answer == True, Word.language == language).all()


def set_word(word: Word) -> None:
    new_word_history = WordHistory(word_id=word.id, date=datetime.date.today())
    session.add(new_word_history)
    session.commit()


def get_word(language="en") -> str:
    words = session.query(WordHistory).filter(
        WordHistory.date == datetime.date.today()).all()
    for word in words:
        if word.word.language == language:
            return word.word.word
    generate_word()
    return get_word(language)


def generate_word() -> None:
    words = get_potentials()
    word = random.choice(words)
    set_word(word)
    update_users()


def get_words(language="en") -> list[str]:
    words = session.query(Word).filter(Word.language == language).all()
    return [word.word for word in words]


def update_users() -> None:
    for user in get_users():
        if not user.answered and user.streak > 0:
            user.streak = 0
        user.guesses = 5
        user.answered = False
        update_user(user)
