from datetime import datetime, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from discord import app_commands
from consts import OWNER_ID, TOKEN
from database import (User, UserGuessData, add_user, generate_words_today, get_all_words, get_user,
                      get_users, get_word_today, reset_users, get_current_guess_data,
                      update_user_guess_data, change_language, Languages)


bot = commands.Bot(command_prefix="",
                   intents=discord.Intents.all(), help_command=None)


def guesses(amount: int, word: str, n=True) -> str:
    """
    Formats the word based on the pluralization.

    :param amount: The amount.
    :param word: The word.
    :param n: If there is a plural form with 'n'.
    :return: The formated word.
    """
    if amount == 1:
        return f"1 {word}"
    if n:
        return f"{amount} {word}en"
    return f"{amount} {word}e"


def wordle_language(lang: Languages) -> str:
    """
    Formats the wordle language string based on the selected language.

    :param lang: The selected language.
    :return: The formatted wordle language string.
    """
    return lang.value + "es Wordle"


async def handle_correct_guess(message: discord.Message, user: User, guess_data: UserGuessData, word: str) -> None:
    """
    Function that handles a correct guess by a user, sending them a congratulatory message.

    :param message: The discord message object.
    :param user: The user object of the guessing user.
    :param guess_data: The guess data of the user.
    :param word: The correct word.
    """
    emoji_word = ""
    emoji_answer = ""
    guess_data.answered = True
    guess_data.streak += 1
    for charackter in word:
        emoji_word += f":regional_indicator_{charackter}:"
        emoji_answer += "🟩"
    embed = discord.Embed(title=wordle_language(
        user.language), description=f"{emoji_word}\n{emoji_answer}")
    embed.set_footer(
        text=f"Damit hast du an {guesses(guess_data.streak, "Tag")} in Folge das Wort erraten.")
    await message.reply(embed=embed)
    update_user_guess_data(guess_data)
    await bot.get_user(OWNER_ID).send(f"{user.username} hat das {user.language}e Wort in {guesses(guess_data.guesses, "Versuch")} erraten.")


async def handle_incorrect_guess(message: discord.Message, user: User, guess_data: UserGuessData, word: str, guess: str) -> None:
    """
    Function that handles an incorrect guess by a user, sending them feedback on their guess.

    :param message: The discord message object.
    :param user: The user object of the guessing user.
    :param guess_data: The guess data of the user.
    :param word: The correct word.
    :param guess: The guess made by the user.
    """
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
    embed = discord.Embed(title=wordle_language(
        user.language), description=f"{emoji_word}\n{emoji_answer}")
    if guess_data.guesses < 6:
        embed.set_footer(
            text=f"Du hast noch {guesses(6 - guess_data.guesses, "Versuch", False)} übrig.")
    else:
        embed.set_footer(text=f"Das Wort war {word}, viel Glück morgen!")
    await message.reply(embed=embed)
    update_user_guess_data(guess_data)


async def analyze_answer(message: discord.Message):
    """
    Function that analyzes the answer of a user for the selected language and the current word.

    :param message: The discord message object.
    """
    user = get_user(message.author.id)
    guess = message.content.lower()
    guess_data = get_current_guess_data(user)
    word = ""
    try:
        word = get_word_today(user.language)
    except ValueError:
        generate_words_today()
        reset_users()
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
        await handle_correct_guess(message, user, guess_data, word)
    else:
        await handle_incorrect_guess(message, user, guess_data, word, guess)


@bot.event
async def on_ready() -> None:
    """
    Discord event that is called when the bot is ready. Starts the sync_clock task and syncs the command tree.
    """
    sync_clock.start()
    await bot.tree.sync()


@bot.event
async def on_message(message: discord.Message):
    """
    Checks if a user sent a dm to the bot, then analyzes the answer.

    :param message: The discord message object.
    """
    if message.author != bot.user and type(message.channel) is discord.DMChannel:
        if message.author.id not in [user.id for user in get_users()]:
            add_user(message.author.id, message.author.name)
        await analyze_answer(message)


@bot.tree.command(name="info", description="Erhalte Infos über die Funktionalität des Bots.")
async def info(interaction: discord.Interaction):
    """
    Command that sends information about the bot.

    :param interaction: The discord interaction object.
    """
    await interaction.response.send_message("Einfach dem Bot eine PN schreiben um zu beginnen.\nJede PN wird als Versuch gewertet. Jeder User hat täglich 6 Versuche pro Sprache. Um 0 Uhr werden neue Wörter ausgelost.", ephemeral=True, )


@bot.tree.command(name="sprachauswahl", description="Ändere die Sprache in der Guesses gewertet werden.")
@app_commands.describe(sprache="Die Sprache vom Wordle.")
async def sprachauswahl(interaction: discord.Interaction, sprache: Languages):
    """
    Command that changes the language of the user.

    :param interaction: The discord interaction object.
    :param sprache: The selected language.
    """
    change_language(get_user(interaction.user.id), sprache)
    await interaction.response.send_message(f"Die Sprache wurde zu {sprache} geändert.", ephemeral=True)


@tasks.loop(minutes=1)
async def sync_clock():
    """
    Looped function that syncs update_word to run at midnight Berlin time.
    """
    berlin_time = datetime.now(tz=ZoneInfo("Europe/Berlin"))
    time_delta = berlin_time.utcoffset()

    dummy_date = datetime.combine(datetime.now(), time(0, 0, 0))
    adjusted_date = dummy_date - time_delta
    adjusted_time = adjusted_date.time()

    update_word.change_interval(time=adjusted_time)

    if not update_word.is_running():
        update_word.start()


@tasks.loop(hours=200000)
async def update_word():
    """
    Looped function that generats a new word when there is no word for today.
    """
    try:
        get_word_today()
    except ValueError:
        generate_words_today()
        reset_users()


bot.run(TOKEN)
