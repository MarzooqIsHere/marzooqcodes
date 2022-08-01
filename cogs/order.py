from discord.ext import commands
import discord
import datetime
from firebase import db
from variables import guildIDs
from discord.commands import Option

class OrderModal(discord.ui.Modal):

    def __init__(self, product, referral):
        self.product = product
        self.referral = referral
        super().__init__(
            discord.ui.InputText(
                label="Describe your product.",
                style=discord.InputTextStyle.paragraph
            ),
            title="Product Description"
        )

    async def callback(self, interaction: discord.Interaction):

        # Making the channel for the ticket
        
        ticketCategory: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=866027666955042836)
        ticket: discord.TextChannel = await ticketCategory.create_text_channel(name=f"order-for-{interaction.user.display_name}")
        

        # Making the embed for the ticket

        embed = discord.Embed(title=f"Order for {interaction.user.display_name}",colour=0xf1c058, timestamp=datetime.datetime.now())
        embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/866031490927689738/937098058620080148/image.png")
        embed.add_field(name="Product", value=self.product,inline=False)
        embed.add_field(name="Description", value=self.children[0].value, inline=False)
        embed.add_field(name="Referrer", value=self.referral.mention if self.referral != None else "N/A", inline=False)
        embed.set_footer(text="If you would like to add anything else, let us know below. Otherwise, please wait for Marzooq to respond to discuss the features and prices.")

        # Sending the embed to the ticket channel

        ticketmsg = await ticket.send(content=interaction.user.mention, embed=embed)

        # Getting the log channel for the thumbnail

        orderLogs: discord.TextChannel = discord.utils.get(interaction.guild.channels, name="order-logs")

        # Making the log ticket

        embed = discord.Embed(title=f"Order for {interaction.user.display_name}", description="**Status:** Pending",colour=0xf1c058, timestamp=datetime.datetime.now())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/866031490927689738/937098058620080148/image.png")
        embed.add_field(name="Product", value=self.product,inline=False)
        embed.add_field(name="Description", value=self.children[0].value, inline=False)
        embed.add_field(name="Referrer", value=self.referral.mention if self.referral != None else "N/A", inline=False)

        # Sending the embed to log channel

        msg = await orderLogs.send(embed=embed)

        # Responding to the command 

        await interaction.response.send_message(f"Your order has been started in {ticket.mention}")

        # Send all the info to the database

        orderData = {
            "userID": interaction.user.id,
            "channelID": ticket.id,
            "referrer": self.referral.id if self.referral != None else None,
            "product": self.product,
            "description": self.children[0].value,
            "status": "Pending",
            "price": None,
            "eta": None,
            "logMessageID": msg.id,
            "ticketMessageID": ticketmsg.id
        }

        db.collection("Orders").document(str(ticket.id)).set(orderData)
        

class Order(commands.Cog):

    def __init__ (self, bot):
        self.bot = bot

    @commands.slash_command(guild_ids=guildIDs)
    async def order(self, ctx: discord.ApplicationContext, 
    product: Option(str, "What product do you want?", choices=["🤖 Discord Bot", "☁️ API", "📈 Data Manipulation", "❓Other"], required=True),
    referral: Option(discord.Member, "The person who referred you to MarzooqCodes if there is one. Cannot be yourself.", required=False)):

        """Order a service."""

        # Pre-conditions

        if referral == ctx.author:
            await ctx.respond("You cannot use yourself for a referral.", ephemeral=True)
            return

        # Sends the description modal

        await ctx.send_modal(OrderModal(product, referral))

    @commands.slash_command(guild_ids=guildIDs)
    @commands.is_owner()
    async def confirm(self, ctx: discord.ApplicationContext,
    price: Option(float, "How much is being charged."),
    eta: Option(int, "An estimate of how long it will take to provide the product in days", default=7, required=False)):

        """Confirm an order."""

        print(eta)

        # Pre-conditions 

        await ctx.defer()

        if ctx.author.id != 316288809216245762:
            return

        # Getting the order data

        doc = db.collection("Orders").document(str(ctx.channel.id)).get()

        if not doc.exists:
            return

        doc = doc.to_dict()

        # Changing the status to confirmed

        doc["status"] = "Confirmed"
        
        # Moving the ticket to confirmed category

        category = ctx.guild.get_channel(1003352359591743498)
        await ctx.channel.move(category=category, beginning=True)

        # Adding the price and ETA

        doc["price"] = price
        doc["eta"] = datetime.datetime.now() + datetime.timedelta(days=eta)

        # Setting the data

        db.collection("Orders").document(str(ctx.channel.id)).set(doc)

        # Getting the associated member

        member: discord.Member = ctx.guild.get_member(doc["userID"])

        # Getting the timestamp

        timestamp = datetime.datetime.now() + datetime.timedelta(days=eta)
        timestamp = timestamp.timestamp()
        timestamp = round(timestamp)

        # Sending confirmation message

        embed = discord.Embed(title="Order has been confirmed", description=f"Your order has been confirmed for the price of **${price}**. It will be done <t:{timestamp}:R>.", colour=0xf1c058)
        await ctx.send(embed=embed, content=member.mention)
        await ctx.respond("Confirmed.", ephemeral=True)
        await member.send(embed=embed)

        # Editing the embed in the order Log

        orderLogs: discord.TextChannel = discord.utils.get(ctx.guild.channels, name="order-logs")

        logMessage: discord.Message = await orderLogs.fetch_message(doc["logMessageID"])
        embed = logMessage.embeds[0]
        embed.add_field(name="Price", value=f"${price}")
        embed.description = "**Status:** Confirmed"
        await logMessage.edit(embed=embed)

        # Giving the client the client role

        await member.add_roles(discord.utils.get(ctx.guild.roles, name="Client"))

        # Edit the commission queue counter

        cqChannel = ctx.guild.get_channel(867164174823849985)
        queueLength = len(category.channels)
        await cqChannel.edit(name=f"Commission Queue: {queueLength}")

    @commands.slash_command(guild_ids=guildIDs)
    @commands.is_owner()
    async def edit(self,ctx: discord.ApplicationContext,
    attribute: Option(str, "Attribute to edit", choices=["Price", "ETA"]),
    new: Option(str, "The new variable for the attribute.")):

        """Edit an order's details."""

        # Pre-requisites

        await ctx.defer()

        if ctx.author.id != 316288809216245762:
            return

        # Getting the order data

        doc = db.collection("Orders").document(str(ctx.channel.id)).get()

        if not doc.exists:
            return

        doc = doc.to_dict()

        # Getting the associated member

        member: discord.Member = ctx.guild.get_member(doc["userID"])

        if attribute == "Price":

            # Making the price an int

            new = int(new)

            # Editing the data

            doc["price"] = new

            # Editing the embed in the order Log

            orderLogs: discord.TextChannel = discord.utils.get(ctx.guild.channels, name="order-logs")

            logMessage: discord.Message = await orderLogs.fetch_message(doc["logMessageID"])
            embed = logMessage.embeds[0]
            embed.remove_field(3)
            embed.add_field(name="Price", value=f"${new}")
            await logMessage.edit(embed=embed)

            # Making an embed to send to client and channel

            embed = discord.Embed(title="Order Update", description=f"Your order's price has been updated to **${new}**.", colour=0xf1c058)
            await ctx.send(content=member.mention, embed=embed)
            await ctx.respond("Updated.", ephemeral=True)
            await member.send(embed=embed)

        elif attribute == "ETA":
            
            # Editing the data
            doc["eta"] = datetime.datetime.now() + datetime.timedelta(days=new)

            # Getting the timestamp

            timestamp = datetime.datetime.now() + datetime.timedelta(days=new)
            timestamp = timestamp.timestamp()
            timestamp = round(timestamp)

            # Making an embed to send to client and channel

            embed = discord.Embed(title="Order Update", description=f"Your order will now be done in <t:{timestamp}:R>.", colour=0xf1c058)
            await ctx.send(content=member.mention, embed=embed)
            await ctx.respond("Updated.", ephemeral=True)
            await member.send(embed=embed)

    @commands.slash_command(guild_ids=guildIDs)
    @commands.is_owner()
    async def complete(self,ctx: discord.ApplicationContext):
        
        """Move an order to the complete phase"""

        # Pre-requisites

        await ctx.defer()

        if ctx.author.id != 316288809216245762:
            return

        # Getting the order data

        doc = db.collection("Orders").document(str(ctx.channel.id)).get()

        if not doc.exists:
            return

        doc = doc.to_dict()

        member = ctx.guild.get_member(int(doc["userID"]))

        # Moving the ticket to the complete category

        category = ctx.guild.get_channel(1003353980325335221)
        await ctx.channel.move(category=category, beginning=True)

        # Editing the embed in the order Log

        orderLogs: discord.TextChannel = discord.utils.get(ctx.guild.channels, name="order-logs")

        logMessage: discord.Message = await orderLogs.fetch_message(doc["logMessageID"])
        embed = logMessage.embeds[0]
        embed.description = "**Status:** Completed"
        await logMessage.edit(embed=embed)

        # Sending confirmation message

        embed = discord.Embed(title="Order has been confirmed", description=f"Your order has been completed. Thank you for buying from MarzooqCodes! ", colour=0xf1c058)
        embed.add_field(name="Review", value="If you wish to, you can submit a review using the /review command.")
        await ctx.send(embed=embed, content=member.mention)
        await ctx.respond("Confirmed.", ephemeral=True)
        await member.send(embed=embed)

        # Edit the commission queue counter

        cqChannel = ctx.guild.get_channel(867164174823849985)
        queueLength = len(category.channels)
        await cqChannel.edit(name=f"Commission Queue: {queueLength}")

    @commands.slash_command(guild_ids=guildIDs)
    async def cancel(self,ctx: discord.ApplicationContext):

        """Cancel an order. (Cannot be done when completed or to be paid.)"""

        await ctx.defer()

        # Getting the order data

        doc = db.collection("Orders").document(str(ctx.channel.id)).get()

        if not doc.exists:
            return

        doc = doc.to_dict()

        # Pre requisites

        if doc["status"] == "Completed":
            await ctx.respond("This order has already been completed.")
            return

        if doc["status"] == "Payment":
            await ctx.respond("You cannot cancel an order that is in the payment phase.")
            return

        member = ctx.guild.get_member(int(doc["userID"]))

        # Ticket deletion

        await ctx.channel.delete()

        # DB deletion

        db.collection("Orders").document(str(ctx.channel.id)).delete()

        # Client role removal 

        role = ctx.guild.get_role(868131800176795699)
        if role in member.roles:
            await member.remove_roles(role)

        # Edit the commission queue counter
        category = ctx.guild.get_channel(1003353980325335221)
        cqChannel = ctx.guild.get_channel(867164174823849985)
        queueLength = len(category.channels)
        await cqChannel.edit(name=f"Commission Queue: {queueLength}")

    @commands.slash_command(guild_ids=guildIDs)
    @commands.is_owner()
    async def payment(self, ctx: discord.ApplicationContext):

        """Move the order to payment phase."""

        await ctx.defer()

        # Getting the order data

        doc = db.collection("Orders").document(str(ctx.channel.id)).get()

        if not doc.exists:
            return

        doc = doc.to_dict()

        member = ctx.guild.get_member(int(doc["userID"]))

        # Setting the status to Payment

        doc["status"] = "Payment"

        # Editing the embed in the order Log

        orderLogs: discord.TextChannel = discord.utils.get(ctx.guild.channels, name="order-logs")

        logMessage: discord.Message = await orderLogs.fetch_message(doc["logMessageID"])
        embed = logMessage.embeds[0]
        embed.description = "**Status:** Payment"
        await logMessage.edit(embed=embed)

        # Sending confirmation message

        embed = discord.Embed(title="The order's payment is due", description=f"You may pay via PayPal with the following [link](https://paypal.me/marzooqcodes) or QR code.", colour=0xf1c058)
        await ctx.send(embed=embed, content=member.mention)
        await ctx.send("https://cdn.discordapp.com/attachments/937428034867314688/1003399539862032455/unknown.png")
        await ctx.respond("Sent.", ephemeral=True)
        await member.send(embed=embed)
        await member.send("https://cdn.discordapp.com/attachments/937428034867314688/1003399539862032455/unknown.png")


def setup(bot):
    bot.add_cog(Order(bot))