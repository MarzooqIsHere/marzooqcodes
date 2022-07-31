import discord
from discord.ext import commands, tasks
from discord.commands import Option
from welcomecardcreator import createWelcomeCard
import os
from variables import guildIDs
import random
import dotenv
import os

dotenv.load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_member_join(member: discord.Member):

    welcomeCard = await createWelcomeCard(member.avatar.url, member.display_name)

    await member.add_roles(discord.utils.get(member.guild.roles, name="Member"))

    welcomeChannel: discord.TextChannel = discord.utils.get(member.guild.channels,id=866002529771192360)

    file = discord.File(f"{member.display_name}.png", filename="image.png")
    embed = discord.Embed(title="Welcome to MarzooqCodes!", description="Please read the rules and open a ticket to discuss your next Discord bot or API with Marzooq!")
    embed.set_author(name=member.display_name,icon_url=member.avatar_url)
    embed.set_image(url="attachment://image.png")

    await welcomeChannel.send(content=member.mention,embed=embed,file=file)

    os.remove(f"{member.display_name}.png")

@tasks.loop(seconds=10)
async def updateMembers():

    guild = bot.get_guild(865989467021246526)
    memberCount = guild.member_count

    channel = guild.get_channel(866116434534727740)
    await channel.edit(name=f"Members: {memberCount}")

@updateMembers.before_loop
async def beforeLoop():

    print("Waiting...")
    await bot.wait_until_ready()

updateMembers.start()

bot.load_extension("cogs.order")
bot.load_extension("cogs.review")
bot.load_extension("cogs.invites")

bot.run(BOT_TOKEN)
