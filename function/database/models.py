import datetime
import enum
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base = declarative_base()

class NotificationState(StrEnum):
    Ein = "Ein"
    Aus = "Aus"

class Language(StrEnum):
    EN = "Englisch"
    DE = "Deutsch"

    @property
    def wordle_title(self) -> str:
        return {Language.EN: "Englisches Wordle", Language.DE: "Deutsches Wordle"}[self]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    language: Mapped[Language] = mapped_column(
        Enum(Language, native_enum=False), default=Language.EN
    )
    notifications: Mapped[Language] = mapped_column(
        Enum(NotificationState, native_enum=False), default=NotificationState.Ein
    )

    # Relationship
    user_guess_data: Mapped[list["UserGuessData"]] = relationship(back_populates="user")


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word: Mapped[str]
    language: Mapped[Language] = mapped_column(
        Enum(Language, native_enum=False), default=Language.EN
    )
    potential_answer: Mapped[bool] = mapped_column(default=False)

    # Relationship
    word_history_entries: Mapped[list["WordHistory"]] = relationship(
        back_populates="word"
    )


class WordHistory(Base):
    __tablename__ = "word_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"))
    date: Mapped[datetime.date]

    # Relationship
    word: Mapped[Word] = relationship(back_populates="word_history_entries")


class UserGuessData(Base):
    __tablename__ = "user_guesses"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    language: Mapped[Language] = mapped_column(
        Enum(Language, native_enum=False), primary_key=True
    )
    guesses: Mapped[int] = mapped_column(default=0)
    streak: Mapped[int] = mapped_column(default=0)
    answered: Mapped[bool] = mapped_column(default=False)

    # Relationship
    user: Mapped[User] = relationship(back_populates="user_guess_data")
