from discord import Client

from database.models import Language, User
from database.user import add_user, get_user, get_users, reset_users
from database.word import get_word_today, generate_word_today


def get_or_create_user(user_id: int, username: str) -> User:
    user = get_user(user_id)
    if user is None:
        add_user(user_id, username)
        user = get_user(user_id)
    return user


async def update_word(bot: Client) -> None:
    for language in Language:
        try:
            get_word_today(language)
        except ValueError:
            generate_word_today(language)


def guesses(amount: int, word: str, n=True) -> str:
    if amount == 1:
        return f"1 {word}"
    if n:
        return f"{amount} {word}en"
    return f"{amount} {word}e"
