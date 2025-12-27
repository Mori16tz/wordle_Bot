import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from database import (
    add_user,
    get_users,
    get_user,
    update_user,
    get_word,
    get_words,
)

load_dotenv()

bot = commands.Bot(command_prefix="",
                   intents=discord.Intents.all(), help_command=None)


@bot.event
async def on_ready():
    await bot.tree.sync()


async def analyze_answer(message: discord.Message):
    user = get_user(message.author.id)
    word = get_word()
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
        if not guess in get_words():
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


bot.run(os.getenv("TOKEN", "no token set"))
