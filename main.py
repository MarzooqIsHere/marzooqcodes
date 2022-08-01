import discord
from discord.ext import commands, tasks
from discord.commands import Option
from welcomecardcreator import createWelcomeCard
import os
from variables import guildIDs
import random
import dotenv
import os
import platform

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
    embed.set_author(name=member.display_name,icon_url=member.avatar.url)
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

@bot.slash_command(guild_ids=guildIDs)
async def about(ctx: discord.ApplicationContext):

    """View information about the bot."""

    await ctx.defer()

    author = ctx.author
    marzooq = await bot.fetch_user(316288809216245762)

    usercount = len(bot.users)

    embed = discord.Embed(description="MarzooqCodes Bot is an open source bot used to manage the MarzooqCodes Discord Server. The code for it can be found below.")

    embed.set_author(name=f"Bot Statistics", icon_url=bot.user.avatar.url)

    embed.add_field(name="Bot",
    value=f"""
Name: **{bot.user.name}#{bot.user.discriminator}**
ID: `{bot.user.id}`
Bot Developer: {marzooq.mention}
v2 Release Date: `31 July 2021`
Github Repo: https://github.com/MarzooqIsHere/marzooqcodes
    """,
    inline=False)

    embed.add_field(name="Stats",
    value=f"""
Servers: {len(bot.guilds)}
Users: {usercount}
Python Version: `{platform.python_version()}`
Discord.py Version: `{discord.__version__}`
Bot Latency: **{round(bot.latency*1000)}ms**
    """,
    inline=False)

    embed.set_footer(text=f"Requested by {author.display_name}")
    await ctx.respond(embed=embed)


bot.load_extension("cogs.order")
bot.load_extension("cogs.review")
bot.load_extension("cogs.invites")

bot.run(BOT_TOKEN)
