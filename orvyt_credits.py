import discord
from discord.ext import commands
from orvyt_misc import conn,GM
from psycopg2 import sql

class CreditCmnds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_member=None

    credit=discord.SlashCommandGroup(name="credit",description="exchange currency")

    @credit.command(description="give money to player")
    async def give(self, ctx, user:discord.Option(discord.Member, "whom to give money to."), wealth:discord.Option(int,"how much money to give", min_value=0)):
        cursor=conn.cursor()
        query=sql.SQL('UPDATE {} SET Credits=Credits+%s WHERE MemberID=%s').format(sql.Identifier(str(user.guild.id)))
        cursor.execute(query,(wealth,user.id))
        if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
            conn.commit()
            await ctx.respond(f'{user.name} was given {wealth} credits')
        else:
            query=sql.SQL('UPDATE {} SET Credits=Credits+%s WHERE MemberID=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
            cursor.execute(query,(wealth,ctx.interaction.user.id))
            conn.commit()
            await ctx.respond(f'{ctx.interaction.user.name} gave {user.name} {wealth} credits')

    @credit.command(description="take player's money (GM only)")
    async def remove(self, ctx, user:discord.Option(discord.Member, 'who\'s money to take'), wealth:discord.Option(int,"how much money to give", min_value=0)):
        if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
            cursor=conn.cursor()
            query=sql.SQL('UPDATE {} SET Credits=Credits-%s WHERE MemberID=%s').format(sql.Identifier(str(user.guild.id)))
            cursor.execute(query,(wealth,user.id))
            conn.commit()
            await ctx.respond(f'{user.name} lost {wealth} credits')
        else:
            await ctx.respond('You do not have permission to rob people.', ephemeral=True)

    @credit.command(description="view player's money")
    async def view(self, ctx, user:discord.Option(discord.Member, 'who\'s money to view'), displayed:discord.Option(bool,"display command result to others")=True):
        cursor=conn.cursor()
        query=sql.SQL('SELECT Credits FROM {} WHERE MemberID=%s').format(sql.Identifier(str(user.guild.id)))
        cursor.execute(query, (user.id,))
        creditNum=cursor.fetchone()[0]
        await ctx.respond(f'{user.name} has {creditNum} Credits', ephemeral= not displayed)
