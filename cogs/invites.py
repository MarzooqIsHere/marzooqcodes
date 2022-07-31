from discord.ext import commands
import discord
import datetime
from firebase import db
from variables import guildIDs, ticketCategoryID
from discord.commands import Option

class Invites(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(guild_ids=guildIDs)
    async def invites(self, ctx:discord.ApplicationContext,
    member: Option(discord.Member, "The member to check invites for.", required=False)):

        """See how many people someone has invited."""

        await ctx.defer()

        if member == None:
            member = ctx.author

        totalInvites = 0
        for i in await ctx.guild.invites():
            if i.inviter == member:
                totalInvites += i.uses

        if member == ctx.author:
            await ctx.respond(f"You have invited {totalInvites} member{'' if totalInvites == 1 else 's'} to the server!") 
        else:
            await ctx.respond(f"{member.mention} has invited {totalInvites} member{'' if totalInvites == 1 else 's'} to the server!") 

def setup(bot):
    bot.add_cog(Invites(bot))