import random

from discord import date
from database.database import open_session
from database.models import Language, Word, WordHistory


def generate_word_today(language: Language) -> str:
    with open_session() as session:
        potential_words = (
            session.query(Word)
            .filter(Word.language == language, Word.potential_answer)
            .all()
        )
        random_word = random.choice(potential_words)
        new_word_history = WordHistory(word_id=random_word.id, date=date.today())
        session.add(new_word_history)
    return random_word.word


def get_word_today(language: Language) -> str:
    with open_session() as session:
        word_entry = (
            session.query(WordHistory)
            .join(Word)
            .filter(Word.language == language, WordHistory.date == date.today())
            .first()
        )
        if word_entry is None:
            raise ValueError
        return word_entry.word.word


def get_all_words(language: Language) -> list[Word]:
    with open_session() as session:
        return session.query(Word).filter(Word.language == language).all()
