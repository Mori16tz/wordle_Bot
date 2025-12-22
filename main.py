import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix="",
                   intents=discord.Intents.all(), help_command=None)


@bot.event
async def on_ready():
    await bot.tree.sync()
    # spam.start()


@bot.tree.command(name="test", description="test command")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Test Command is working.", ephemeral=True)


# @tasks.loop(seconds=30)
# async def spam():
#     channel = bot.get_channel(1166460738928394341)
#     if channel:
#         await channel.send("Spam")


bot.run(os.getenv("TOKEN"))
