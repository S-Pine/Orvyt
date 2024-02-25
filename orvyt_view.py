import discord
from discord.ext import commands
from ast import literal_eval
from psycopg2 import sql
from orvyt_misc import conn

class ViewCmnds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_member=None

    viewCmnds=discord.SlashCommandGroup(name="view",description="view the inventories of players")

    @viewCmnds.command(description="view player's inventory")
    async def inventory(self, ctx, user:discord.Option(discord.Member, "whose invnetory"), display:discord.Option(bool,"display command result to others")=True):
        cursor=conn.cursor()
        query=sql.SQL('SELECT Items FROM {} where MemberID=%s').format(sql.Identifier(str(user.guild.id)))
        cursor.execute(query,(user.id,))
        inventory=cursor.fetchone()[0]
        for i,item in enumerate(inventory):
            if item[0]=='W':
                query=sql.SQL('SELECT name FROM Weapons.{} WHERE Index=%s').format(sql.Identifier(str(user.guild.id)))
                cursor.execute(query,(item[1:],))
                response=cursor.fetchone()
                if response:
                    inventory[i]=response[0]
                else:
                    inventory.remove(item)
                    query=sql.SQL('UPDATE {} SET items=%s WHERE MemberID=%s').format(sql.Identifier(str(user.guild.id)))
                    cursor.execute(query,(inventory,user.id))
                    conn.commit()
        if len(inventory):
            await ctx.respond(f"{user.name} has "+', '.join(inventory), ephemeral=(not display))
        else:
            await ctx.respond('target has no items', ephemeral=(not display))

    @viewCmnds.command(description="view player's schematics")
    async def schematics(self, ctx, user:discord.Option(discord.Member, "whose schemaitcs"), display:discord.Option(bool,"display command result to others")=True):
            cursor=conn.cursor()
            query=sql.SQL('SELECT Schematics FROM {} where MemberID=%s').format(sql.Identifier(str(user.guild.id)))
            cursor.execute(query,(user.id,))
            inventory=cursor.fetchone()[0]
            if len(inventory)>0:
                await ctx.respond(f"{user.name} has"+', '.join(map(lambda a: 'S{:03}'.format(a), inventory)), ephemeral=not display)
            else:
                await ctx.respond('target has no schematics', ephemeral=(not display))

gradeRGB={
    'A':16171112,
    'B':9320183,
    'C':10157135,
    'D':8902392,
    'F':6513507,
    'U':16732751
}