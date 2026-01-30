from datetime import datetime, time

import discord
from discord import app_commands, DMChannel
from discord.ext import commands, tasks

from common.consts import TOKEN
from common.algorithm import analyze_answer
from common.utils import get_or_create_user, update_word
from database.models import Language, NotificationState
from database.user import get_users, reset_users, update_user

bot = commands.Bot(command_prefix="",
                   intents=discord.Intents.all(), help_command=None)


@bot.event
async def on_ready() -> None:
    sync_clock.start()
    await bot.tree.sync()


@bot.event
async def on_message(message: discord.Message):
    if message.author != bot.user and type(message.channel) is DMChannel:
        await analyze_answer(message, bot)


@bot.tree.command(
    name="info",
    description="Erhalte Infos über die Funktionalität des Bots.",
)
async def info(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Einfach dem Bot eine PN schreiben um zu beginnen.\nJede PN wird als Versuch gewertet. Jeder User hat täglich 6 Versuche pro Sprache.\nUm 0 Uhr werden neue Wörter ausgelost.",
        ephemeral=True,
    )


@bot.tree.command(
    name="sprachauswahl",
    description="Ändere die Sprache in der Guesses gewertet werden.",
)
@app_commands.describe(sprache="Die Sprache vom Wordle.")
async def sprachauswahl(interaction: discord.Interaction, sprache: Language):
    user = get_or_create_user(interaction.user.id, interaction.user.name)
    user.language = sprache
    update_user(user)
    await interaction.response.send_message(
        f"Die Sprache wurde zu {sprache} geändert.", ephemeral=True
    )


@bot.tree.command(name="benachrichtigung", description="Ändere die Benachrichtigungseinstellung.")
@app_commands.describe(status="Der Status für die Benachrichtigungen.")
async def benachrichtigung(interaction: discord.Interaction, status: NotificationState):
    user = get_or_create_user(interaction.user.id, interaction.user.name)
    user.notifications = status
    update_user(user)
    await interaction.response.send_message(
        f"Benachrichtigungen wurden zu {status} geändert.", ephemeral=True
    )


@tasks.loop(minutes=1)
async def sync_clock():
    berlin_time = datetime.now().astimezone()
    time_delta = berlin_time.utcoffset()

    dummy_date = datetime.combine(datetime.now(), time(0, 0, 0))
    adjusted_date = dummy_date - time_delta
    adjusted_time = adjusted_date.time()

    daily_loop.change_interval(time=adjusted_time)

    if not daily_loop.is_running():
        daily_loop.start()


@tasks.loop(hours=200000)
async def daily_loop():
    await update_word(bot)
    reset_users()
    for user in get_users():
        discord_user = bot.get_user(user.id)
        if discord_user is None:
            continue
        if user.notifications == NotificationState.Ein:
            await discord_user.send("Die Wörter wurden geupdatet.\nDiese Benachrichtigung kann mit /benachrichtigung deaktiviert werden.")


bot.run(TOKEN)
