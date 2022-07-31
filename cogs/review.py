from discord.ext import commands
import discord
from firebase import db
from variables import guildIDs, embedColour
from discord.commands import Option

class ReviewModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(
            discord.ui.InputText(
                label="Rate your experience between 1 and 10.",
                style=discord.InputTextStyle.short
            ),
            discord.ui.InputText(
                label="Describe your experience in a few sentences.",
                style=discord.InputTextStyle.paragraph),
            title="Review MarzooqCodes"
        )

    async def callback(self, interaction: discord.Interaction):

        embed = discord.Embed(title=f"Review - {self.children[0].value}/10", description=self.children[1].value, colour=embedColour)
        embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/866031490927689738/937098058620080148/image.png")

        reviewChannel = interaction.guild.get_channel(866290946895249408)
        await reviewChannel.send(embed=embed)

        db.collection("Reviews").document(str(interaction.user.id)).set({
            "rating": self.children[0].value,
            "description": self.children[1].value,
            "userID": interaction.user.id
        })

        await interaction.response.send_message("Your review has been sent!")

class Review(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(guild_ids=guildIDs)
    @commands.has_any_role(868131800176795699)
    async def review(self, ctx:discord.ApplicationContext):

        """Review MarzooqCodes!"""

        if db.collection("Reviews").document(str(ctx.author.id)).get().exists:
            await ctx.respond("You have already submitted a review.")
            return

        await ctx.send_modal(ReviewModal())

def setup(bot):
    bot.add_cog(Review(bot))