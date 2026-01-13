from discord import Client, Interaction

from database.models import Language
from database.user import add_user, get_user, get_users, reset_users


def get_user(user_id: int, username: str) -> None:
    user = get_user(user_id)
    if user is None:
        add_user(user_id, username)
    user = get_user(user_id)


async def update_word(bot: Client) -> None:
    try:
        get_word_today()
    except ValueError:
        generate_words_today()
        reset_users()
    for user in get_users():
        await bot.get_user(user.id).send("Die Wörter wurden geupdatet.")


def guesses(amount: int, word: str, n=True) -> str:
    if amount == 1:
        return f"1 {word}"
    if n:
        return f"{amount} {word}en"
    return f"{amount} {word}e"


def wordle_language(lang: Language) -> str:
    return lang.value + "es Wordle"
