from discord import Message, Embed, Client

from common.utils import get_or_create_user, guesses, update_word
from database.models import User, UserGuessData, Word
from database.word import get_all_words, get_word_today, get_word_history
from database.guess_data import get_user_guess_data, update_user_guess_data
from database.guess_history import add_new_user_guess
from database.guess_history import get_user_guess_history
from common.consts import OWNER_ID


async def handle_correct_guess(
    message: Message, user: User, guess_data: UserGuessData, word: Word, bot: Client
) -> None:
    guess_data.answered = True
    guess_data.streak += 1
    description = ""
    word_history = get_word_history(word.id)
    for history in get_user_guess_history(user.id, word_history.id):
        guess = history.guess
        emoji_word = ""
        emoji_answer = ""
        marked = list(word.word)
        for i in range(0, 5):
            found = False
            emoji_word += f":regional_indicator_{guess[i]}:"
            if guess[i] == word.word[i]:
                emoji_answer += "🟩"
            else:
                for j in range(0, 5):
                    if guess[i] == word.word[j] and guess[j] != word.word[j]:
                        if word.word[j] in marked:
                            emoji_answer += "🟨"
                            found = True
                            marked.remove(word.word[j])
                            break
                if not found:
                    emoji_answer += "🟥"
        description = f"{description}\n{emoji_word}\n{emoji_answer}"
    embed = Embed(
        title=user.language.wordle_title,
        description=description,
    )
    embed.set_footer(
        text=f"Damit hast du an {guesses(guess_data.streak, "Tag")} in Folge das Wort erraten."
    )
    await message.reply(embed=embed)
    update_user_guess_data(guess_data)
    owner = bot.get_user(OWNER_ID)
    if owner is None:
        return
    await owner.send(
        f"{user.username} hat das {user.language.wordle_title} in {guesses(guess_data.guesses, "Versuch")} erraten."
    )


async def handle_incorrect_guess(
    message: Message,
    user: User,
    guess_data: UserGuessData,
    word: Word,
    bot: Client,
) -> None:
    description = ""
    word_history = get_word_history(word.id)
    for history in get_user_guess_history(user.id, word_history.id):
        guess = history.guess
        emoji_word = ""
        emoji_answer = ""
        marked = list(word.word)
        for i in range(0, 5):
            found = False
            emoji_word += f":regional_indicator_{guess[i]}:"
            if guess[i] == word.word[i]:
                emoji_answer += "🟩"
            else:
                for j in range(0, 5):
                    if guess[i] == word.word[j] and guess[j] != word.word[j]:
                        if word.word[j] in marked:
                            emoji_answer += "🟨"
                            found = True
                            marked.remove(word.word[j])
                            break
                if not found:
                    emoji_answer += "🟥"
        description = f"{description}\n{emoji_word}\n{emoji_answer}"
    embed = Embed(
        title=user.language.wordle_title,
        description=description,
    )
    if guess_data.guesses < 6:
        embed.set_footer(
            text=f"Du hast noch {guesses(6 - guess_data.guesses, "Versuch", False)} übrig."
        )
    else:
        embed.set_footer(text=f"Das Wort war {word.word}, viel Glück morgen!")
        owner = bot.get_user(OWNER_ID)
        if owner is not None:
            await owner.send(
                f"{user.username} hat das {user.language.wordle_title} nicht erraten."
            )
    await message.reply(embed=embed)
    update_user_guess_data(guess_data)


async def analyze_answer(message: Message, bot: Client):
    await update_word(bot)
    user = get_or_create_user(message.author.id, message.author.name)
    if user is None:
        return
    guess = message.content.lower()
    guess_data = get_user_guess_data(user.id, user.language)
    word = get_word_today(user.language)
    if guess_data.answered:
        await message.reply("Du hast das Wort für heute bereits erraten.")
        return
    if guess_data.guesses == 6:
        await message.reply("Du hattest heute bereits 6 Versuche, das Wort zu erraten.")
        return
    if guess not in get_all_words(user.language):
        await message.reply("Dieses Wort ist kein valider Wordle-Guess.")
        return
    guess_data.guesses += 1
    word_history = get_word_history(word.id)
    add_new_user_guess(user.id, word_history.id, guess)
    if guess == word.word:
        await handle_correct_guess(message, user, guess_data, word, bot)
    else:
        await handle_incorrect_guess(message, user, guess_data, word, bot)
