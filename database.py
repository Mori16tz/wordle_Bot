import datetime
import random
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, create_engine
from sqlalchemy.orm import (Mapped, declarative_base, mapped_column,
                            relationship, sessionmaker)

Base = declarative_base()


class Languages(StrEnum):
    EN = "en"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column()
    guesses: Mapped[int] = mapped_column(default=0)
    streak: Mapped[int] = mapped_column(default=0)
    answered: Mapped[bool] = mapped_column(default=False)


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column()
    language: Mapped[Languages] = mapped_column(
        Enum(Languages, native_enum=False),
        default=Languages.EN,
        nullable=False,
    )
    potential_answer: Mapped[bool] = mapped_column(default=False)
    word_history_entries: Mapped[list["WordHistory"]] = relationship(
        back_populates="word"
    )


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

""" WORD """


def add_word(word: str, language: str, potential_answer: bool) -> None:
    new_word = Word(word=word, language=language, potential_answer=potential_answer)
    session.add(new_word)
    session.commit()


def get_word_today(language=Languages.EN) -> str:
    words = (
        session.query(WordHistory)
        .filter(WordHistory.date == datetime.date.today())
        .all()
    )
    for word in words:
        if word.word.language == language:
            return word.word.word
    # daily word update failed -> run it manually
    generate_words_today()
    reset_users()
    return get_word_today(language)


def get_all_words(language=Languages.EN) -> list[str]:
    words = session.query(Word).filter(Word.language == language).all()
    return [word.word for word in words]


def get_potentials(language: Languages) -> list[Word]:
    return (
        session.query(Word)
        .filter(Word.potential_answer, Word.language == language)
        .all()
    )


def set_word_today(word: Word) -> None:
    new_word_history = WordHistory(word_id=word.id, date=datetime.date.today())
    session.add(new_word_history)
    session.commit()


def generate_words_today() -> None:
    for lang in Languages:
        words = get_potentials(lang)
        set_word_today(random.choice(words))


""" USER """


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


def reset_users() -> None:
    for user in get_users():
        print(user.__dict__)
        if not user.answered:
            user.streak = 0
        user.guesses = 0
        user.answered = False
        update_user(user)
