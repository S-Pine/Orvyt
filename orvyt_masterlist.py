import discord
from discord.ext import commands
from psycopg2 import sql
from orvyt_misc import GM,conn

class MasterList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_member=None
    
    masterlist=discord.SlashCommandGroup(name="master-list",description="edit the Mast list of items")

    @masterlist.command(description="add possible material to master list")
    async def add(self, ctx, category:discord.Option(str, choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I)']),name:discord.Option(str, 'name of object')):
        if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None or ctx.interaction.user.id==693848229896388669:
            cursor=conn.cursor()
            category=category[-2]
            query=sql.SQL('SELECT array_length(Items,1) FROM MASTER_LIST WHERE Category=%s')
            cursor.execute(query,(category,))
            newSerial=cursor.fetchone()[0]+1
            query=sql.SQL('UPDATE MASTER_LIST SET Items=array_append(Items,%s) WHERE Category=%s')
            cursor.execute(query,(name,category))
            conn.commit()
            await ctx.respond(f'{name}({category}{newSerial:03}) was added to the list')
        else:
            await ctx.respond('you do not have permission to edit the master list',ephemeral=True)

    @masterlist.command(description="remove last material from master list")
    async def remove(self, ctx, category:discord.Option(str, choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I),'])):
        if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
            cursor=conn.cursor()
            category=category[-2]
            query=sql.SQL('SELECT Items FROM MASTER_LIST WHERE Category=%s')
            cursor.execute(query,(category,))
            pastArray=cursor.fetchone()[0]
            query=sql.SQL('UPDATE MASTER_LIST SET Items=trim_array(Items,1) WHERE Category=%s')
            cursor.execute(query,(category,))
            conn.commit()
            await ctx.respond(f'{pastArray[len(pastArray)-1]}({category}{len(pastArray):03}) was removed')
        else:
            await ctx.respond('you do not have permission to edit the master list',ephemeral=True)
