import os
import discord
import random
import datetime
from discord.ext import commands, tasks
from dotenv import load_dotenv
from database import (
    add_user,
    get_users,
    get_user,
    update_user
)

load_dotenv()

bot = commands.Bot(command_prefix="",
                   intents=discord.Intents.all(), help_command=None)
wordlist, guessesL = [], []
with open("wordlist.txt", encoding="utf8") as f:
    for line in f:
        wordlist.append(line.strip())

with open("possible_guesses.txt", encoding="utf8") as f:
    for line in f:
        guessesL.append(line.strip())

guesses = set(guessesL)
word = random.choice(wordlist)


@bot.event
async def on_ready():
    sync_clock.start
    await bot.tree.sync()
    # spam.start()


async def analyze_answer(message: discord.Message):
    user = get_user(message.author.id)
    if user is not None:
        if user.answered:
            await message.reply("Du hast das Wort für heute bereits erraten.")
            return
        guess = message.content.lower()
        if user.guesses == 0:
            await message.reply("Du hattest heute bereits 5 Versuche, das Wort zu erraten.")
            return
        if len(guess) != 5:
            await message.reply("Das Wort hat genau 5 Buchstaben.")
            return
        if not guess.isalpha():
            await message.reply("Das Wort enthält nur Buchstaben.")
            return
        if guess == word:
            user.guesses -= 1
            await message.reply(f"Du hast das Wort in {5-user.guesses} Versuchen erraten!")
            user.answered = True
            user.streak += 1
            update_user(user)
            return
        if not guess in guesses:
            await message.reply("Dieses Wort ist kein valider Wordle-Guess.")
            return
        characters = [a for a in word]
        correct, wrong_place, not_in_word = [], [], []
        for a in range(0, 5):
            if guess[a] == word[a]:
                correct.append(word[a])
                characters.remove(word[a])
            elif guess[a] in characters:
                wrong_place.append(guess[a])
                characters.remove(guess[a])
            else:
                not_in_word.append(guess[a])
        user.guesses -= 1
        output = "Korrekte Buchstaben: "+', '.join(correct)
        output += "\nBuchstaben an der falschen Stelle: " + \
            ', '.join(wrong_place)
        output += "\nBuchstaben, die nicht im Wort enthalten sind: " + \
            ', '.join(not_in_word)
        if user.guesses > 0:
            output += "\nDu hast noch "+str(user.guesses)+" Versuche übrig."
        else:
            output += "\nDu hast das Wort nicht in 5 Versuchen erraten."
        await message.reply(str(output))
        update_user(user)


@bot.event
async def on_message(message: discord.Message):
    if message.author != bot.user and type(message.channel) is discord.DMChannel:
        if message.author.id not in [a.id for a in get_users()]:
            add_user(message.author.id, message.author.name)
        await analyze_answer(message)


@bot.tree.command(name="test", description="test command")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Test Command is working.", ephemeral=True)


@bot.tree.command(name="info", description="Erhalte Infos über die Funktionalität des Bots.")
async def info(interaction: discord.Interaction):
    await interaction.response.send_message("Einfach dem Bot eine PN schreiben um zu beginnen. Jede PN wird als Guess gewertet. Jeder User hat pro Tag 5 Guesses. Um 0 Uhr wird ein neues Wort gewählt.", ephemeral=True)


@tasks.loop(hours=5)
async def sync_clock():
    berlin_time = datetime.now(tz=ZoneInfo("Europe/Berlin"))
    time_delta = berlin_time.utcoffset()

    dummy_date = datetime.combine(datetime.now(), datetime.time(0, 0, 0))
    adjusted_date = dummy_date - time_delta
    adjusted_time = adjusted_date.time()

    choose_new_word.change_interval(time=adjusted_time)

    if not choose_new_word.is_running():
        choose_new_word.start()


@tasks.loop(hours=2000)
async def choose_new_word():
    global word
    word = random.choice(wordlist)
    for user in get_users():
        if not user.answered and user.streak > 0:
            user.streak = 0
        user.guesses = 5
        user.answered = False
        update_user(user)


bot.run(os.getenv("TOKEN", "no token set"))
