from datetime import datetime, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from consts import OWNER_ID, TOKEN
from database import (add_user, generate_words_today, get_all_words, get_user,
                      get_users, get_word_today, reset_users, update_user)


bot = commands.Bot(command_prefix="",
                   intents=discord.Intents.all(), help_command=None)


@bot.event
async def on_ready():
    sync_clock.start()
    await bot.tree.sync()


async def analyze_answer(message: discord.Message):
    user = get_user(message.author.id)
    word = ""
    try:
        word = get_word_today()
    except ValueError:
        generate_words_today()
        reset_users()
        word = get_word_today()
    guess = message.content.lower()
    output = ""
    emoji_word = ""
    if user is None:
        return
    if user.answered:
        await message.reply("Du hast das Wort für heute bereits erraten.")
        return
    if user.guesses == 5:
        await message.reply("Du hattest heute bereits 5 Versuche, das Wort zu erraten.")
        return
    if guess not in get_all_words():
        await message.reply("Dieses Wort ist kein valider Wordle-Guess.")
        return
    user.guesses += 1
    if guess == word:
        user.answered = True
        user.streak += 1
        await message.reply(
            f"Du hast das Wort in {user.guesses} Versuchen erraten!\n"
            f"Damit hast du an {user.streak} Tagen in Folge das Wort erraten."
        )
        update_user(user)
        await bot.get_user(OWNER_ID).send(
            f"{message.author.display_name} hat das Wort in {user.guesses}"
            "erraten."
        )
        return
    for index, charackter in enumerate(guess):
        emoji_word += f":regional_indicator_{charackter}:"
        if charackter not in word:
            output += "🟥"
            continue
        if word[index] == charackter:
            output += "🟩"
            continue
        output += "🟨"
    if user.guesses < 5:
        output += "\nDu hast noch " + \
            str(5 - user.guesses) + " Versuche übrig."
    else:
        output += "\nDu hast das Wort nicht in 5 Versuchen erraten.\nDas" \
            "Wort war "+word
    await message.reply(emoji_word + "\n" + output)
    update_user(user)


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
        " Jeder User hat pro Tag 5 Guesses. Um 0 Uhr wird ein neues Wort gewählt.",
        ephemeral=True,
    )


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
