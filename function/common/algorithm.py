from discord import Message, Embed, Client

from common.utils import get_or_create_user, guesses, update_word, wordle_language
from database.models import User, UserGuessData
from database.word import get_all_words, get_word_today
from database.guess_data import get_user_guess_data, update_user_guess_data
from function.common.consts import OWNER_ID


async def handle_correct_guess(
    message: Message, user: User, guess_data: UserGuessData, word: str, bot: Client
) -> None:
    emoji_word = ""
    emoji_answer = ""
    guess_data.answered = True
    guess_data.streak += 1
    for charackter in word:
        emoji_word += f":regional_indicator_{charackter}:"
        emoji_answer += "🟩"
    embed = Embed(
        title=wordle_language(user.language),
        description=f"{emoji_word}\n{emoji_answer}",
    )
    embed.set_footer(
        text=f"Damit hast du an {guesses(guess_data.streak, "Tag")} in Folge das Wort erraten."
    )
    await message.reply(embed=embed)
    update_user_guess_data(guess_data)
    await bot.get_user(OWNER_ID).send(
        f"{user.username} hat das {user.language}e Wort in {guesses(guess_data.guesses, "Versuch")} erraten."
    )


async def handle_incorrect_guess(
    message: Message,
    user: User,
    guess_data: UserGuessData,
    word: str,
    guess: str,
    bot: Client,
) -> None:
    emoji_word = ""
    emoji_answer = ""
    marked = list(word)
    for i in range(0, 5):
        found = False
        emoji_word += f":regional_indicator_{guess[i]}:"
        if guess[i] == word[i]:
            emoji_answer += "🟩"
        else:
            for j in range(0, 5):
                if guess[i] == word[j] and guess[j] != word[j]:
                    if word[j] in marked:
                        emoji_answer += "🟨"
                        found = True
                        marked.remove(word[j])
                        break
            if not found:
                emoji_answer += "🟥"
    embed = Embed(
        title=wordle_language(user.language),
        description=f"{emoji_word}\n{emoji_answer}",
    )
    if guess_data.guesses < 6:
        embed.set_footer(
            text=f"Du hast noch {guesses(6 - guess_data.guesses, "Versuch", False)} übrig."
        )
    else:
        embed.set_footer(text=f"Das Wort war {word}, viel Glück morgen!")
        await bot.get_user(OWNER_ID).send(
            f"{user.username} hat das Wort nicht erraten."
        )
    await message.reply(embed=embed)
    update_user_guess_data(guess_data)


async def analyze_answer(message: Message, bot: Client):
    await update_word(bot)
    user = get_or_create_user(message.author.id, message.author.name)
    guess = message.content.lower()
    guess_data = get_user_guess_data(user, user.language)
    word = get_word_today(user.language)
    if user is None:
        return
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
    if guess == word:
        await handle_correct_guess(message, user, guess_data, word, bot)
    else:
        await handle_incorrect_guess(message, user, guess_data, word, guess, bot)
