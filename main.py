from datetime import datetime, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
# from discord import app_commands
from consts import OWNER_ID, TOKEN
from database import (add_user, generate_words_today, get_all_words, get_user,
                      get_users, get_word_today, reset_users, get_current_guess_data,
                      update_user_guess_data)


bot = commands.Bot(command_prefix="",
                   intents=discord.Intents.all(), help_command=None)


def guesses(amount: int, correct=True):
    if amount == 1:
        return "1 Versuch"
    if correct:
        return f"{amount} Versuchen"
    return f"{amount} Versuche"


@bot.event
async def on_ready():
    sync_clock.start()
    await bot.tree.sync()


async def analyze_answer(message: discord.Message):
    user = get_user(message.author.id)
    word = ""
    try:
        word = get_word_today(user.language)
    except ValueError:
        generate_words_today()
        reset_users()
        word = get_word_today(user.language)
    guess = message.content.lower()
    output = ""
    emoji_word = ""
    guess_data = get_current_guess_data(user)
    marked = list(word)
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
        guess_data.answered = True
        guess_data.streak += 1
        await message.reply(
            f"Du hast das Wort in {guesses(guess_data.guesses)} erraten!\n"
            f"Damit hast du an {guess_data.streak} Tagen in Folge das Wort erraten."
        )
        update_user_guess_data(guess_data)
        await bot.get_user(OWNER_ID).send(
            f"{message.author.display_name} hat das Wort in "
            f"{guesses(guess_data.guesses)} erraten."
        )
        return
    for i in range(0, 5):
        found = False
        emoji_word += f":regional_indicator_{guess[i]}:"
        if guess[i] == word[i]:
            output += "🟩"
        else:
            for j in range(0, 5):
                if guess[i] == word[j] and guess[j] != word[j]:
                    if word[j] in marked:
                        output += "🟨"
                        found = True
                        marked.remove(word[j])
                        break
            if not found:
                output += "🟥"
    if guess_data.guesses < 6:
        output += f"\nDu hast noch {guesses(6 - guess_data.guesses, False)} übrig."
    else:
        output += "\nDu hast das Wort nicht in 5 Versuchen erraten.\nDas Wort war"\
            f" {word}"
    await message.reply(f"{emoji_word}\n{output}")
    update_user_guess_data(guess_data)


@bot.event
async def on_message(message: discord.Message):
    if message.author != bot.user and type(message.channel) is discord.DMChannel:
        if message.author.id not in [user.id for user in get_users()]:
            add_user(message.author.id, message.author.name)
        await analyze_answer(message)


@bot.tree.command(name="test", description="test command")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Test Command is working.", ephemeral=True)


@bot.tree.command(
    name="info", description="Erhalte Infos über die Funktionalität des Bots."
)
async def info(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Einfach dem Bot eine PN schreiben um zu beginnen."
        " Jede PN wird als Guess gewertet."
        " Jeder User hat pro Tag 6 Guesses. Um 0 Uhr wird ein neues Wort gewählt.",
        ephemeral=True,
    )


# @bot.tree.command(
#     name="sprachauswahl", description="Ändere die Sprache in der Guesses gewertet"
#     " werden."
# )
# @app_commands.describe(sprache="Die Sprache vom Rätsel")
# async def sprachauswahl(interaction: discord.Interaction, sprache: Languages):
#     change_language(get_user(interaction.user.id), sprache)
#     await interaction.response.send_message(f"Die Sprache wurde zu {sprache}
# geändert.",
#                                             ephemeral=True)


@tasks.loop(minutes=1)
async def sync_clock():
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
    try:
        get_word_today()
    except ValueError:
        generate_words_today()
        reset_users()


bot.run(TOKEN)
