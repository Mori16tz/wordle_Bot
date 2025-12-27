import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from database import (add_user, generate_words_today, get_all_words, get_user,
                      get_users, get_word_today, reset_users, update_user)

load_dotenv()

bot = commands.Bot(command_prefix="",
                   intents=discord.Intents.all(), help_command=None)


@bot.event
async def on_ready():
    sync_clock.start()
    await bot.tree.sync()


async def analyze_answer(message: discord.Message):
    user = get_user(message.author.id)
    word = get_word_today()
    guess = message.content.lower()
    output = ""
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
        return
    for i in range(0, 5):
        found = False
        if guess[i] == word[i]:
            output += "\U0001F7E9"
        else:
            for j in range(i, 5):
                if guess[i] == word[j] and guess[j] != word[j]:
                    output += "\U0001F7E8"
                    found = True
                    break
            if not found:
                output += "\U0001F7E5"
    if user.guesses > 0:
        output += "\nDu hast noch " + \
            str(5 - user.guesses) + " Versuche übrig."
    else:
        output += "\nDu hast das Wort nicht in 5 Versuchen erraten."
    await message.reply(str(output))
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
    generate_words_today()
    reset_users()


bot.run(os.getenv("TOKEN", "no token set"))
