import discord
import random
from psycopg2 import sql
from orvyt_misc import ORVYT_TOKEN,GM,conn
from orvyt_masterlist import MasterList
from orvyt_view import ViewCmnds
from orvyt_weapons import WeaponCmnds
from orvyt_credits import CreditCmnds 

# DATABASE_URL=environ['DATABASE_URL']
intents = discord.Intents.default()
intents.members = True
client=discord.Bot(intents=intents)
client.add_cog(MasterList(client))
client.add_cog(ViewCmnds(client))
client.add_cog(WeaponCmnds(client))
client.add_cog(CreditCmnds(client))

SCAVENGE_TABLES={
    'Standard':['M'],
    'Overseer':['M','R'],
    'Monarch':['C','F','R'],
    'Weapon':['M','C','C'],
    'Item':['M','C']
}

@client.event
async def on_ready():
    for guild in client.guilds:
        for role in guild.roles:
            if role.name=='Game Master': GM[guild.id]=role.id
        cursor=conn.cursor()
        query=sql.SQL('SELECT memberid FROM {guildID};').format(guildID=sql.Identifier(str(guild.id)))
        cursor.execute(query)
        result=[i[0] for i in cursor.fetchall()]
        for member in guild.members:
            if member.id not in result:
                query=sql.SQL('INSERT INTO {guildID} (MemberID) VALUES (%s)').format(guildID=sql.Identifier(str(guild.id)))
                cursor.execute(query,(member.id,))
                conn.commit()

    print('Orvyt_Online!')

@client.event
async def on_guild_join(guild):
    cursor=conn.cursor()
    query=sql.SQL('CREATE TABLE {guildID} (MemberID BIGINT PRIMARY KEY, Credits INT DEFAULT 0, Items VARCHAR(25)[] DEFAULT ARRAY[]::VARCHAR(25)[], Schematics integer[] DEFAULT ARRAY[]::integer[])').format(guildID=sql.Identifier(str(guild.id)))
    cursor.execute(query)
    for member in guild.members:
        query=sql.SQL('INSERT INTO {guildID} (MemberID) VALUES (%s)').format(guildID=sql.Identifier(str(guild.id)))
        cursor.execute(query,(member.id,))
    for role in guild.roles:
            if role.name=='Game Master': GM[guild.id]=role.id
    conn.commit()

@client.event
async def on_member_join(member):
    cursor=conn.cursor()
    query=sql.SQL('INSERT INTO {guildID} (MemberID) VALUES (%s)').format(guildID=sql.Identifier(str(member.guild.id)))
    cursor.execute(query,(member.id,))
    conn.commit()

@client.slash_command()
async def help(ctx, display:discord.Option(bool,"display command result to others")=True):
    longmsg="""My Commands! 
    dten: returns a number between 1 and 10. 
    give: allows you to trade or be given items for your inventory! 
    remove\*: removed the stated item from a player. 
    scavenge\*: for rolling on random tables to give players items. 
    masterlist\*: the GM can add or remove possible items
    view: see player\'s inventories and schematics!
    credit: exhange credits!
    weapon: create, edit and view weapons!
       \*: GM only
    """
    await ctx.respond(longmsg, ephemeral=(not display))

@client.slash_command(description="DO NOT TOUCH")
async def commmitdb(ctx):
    if ctx.interaction.user.id==693848229896388669:
        cursor=conn.cursor()
        for guild in client.guilds:
            query=sql.SQL('CREATE TABLE {guildID} (MemberID BIGINT PRIMARY KEY, Credits INT DEFAULT 0, Items VARCHAR(25)[] DEFAULT ARRAY[]::VARCHAR(25)[], Schematics integer[] DEFAULT ARRAY[]::integer[])').format(guildID=sql.Identifier(str(guild.id)))
            cursor.execute(query)
            query=sql.SQL('CREATE TABLE {guildId} (name TEXT PRIMARY KEY, range SMALLINT, damage SMALLINT, charge_time SMALLINT, trait TEXT, type VARCHAR(10), grade CHAR(1), index SERIAL)')
            for member in guild.members:
                query=sql.SQL('INSERT INTO {guildID} (MemberID) VALUES (%s)').format(guildID=sql.Identifier(str(guild.id)))
                cursor.execute(query,(member.id,))
        conn.commit()
        await ctx.respond("Database has been commited, or duplicated if you're stupid")
    else:
        await ctx.respond('you do not have permission to do that.', ephemeral=True)


@client.slash_command(description="responds with a random number between 1 and 10")
async def dten(ctx, display:discord.Option(bool,"display command result to others")=True):
    await ctx.respond(str(random.randint(1,10)), ephemeral=(not display))

@client.user_command(name="dten")
async def die(ctx,member: discord.Member):
    await ctx.respond(str(random.randint(1,10)))
    

@client.slash_command(description='gives item to player\'s inventory')
async def give(ctx, user:discord.Option(discord.Member, "who to give to."), category:discord.Option(str,choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I)', 'Schematic(S)']), number:discord.Option(int, "what serial number of item", min_value=1)):
    guildID=sql.Identifier(str(user.guild.id))
    cursor=conn.cursor()
    if category=='Schematic(S)':
        query=sql.SQL('SELECT Schematics FROM {} WHERE MemberID=%s').format(guildID)
        cursor.execute(query,(user.id,))
        schemArray=cursor.fetchone()[0] 
        if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
            query=sql.SQL('UPDATE {} SET Schematics=Schematics || %s WHERE MemberID=%s').format(guildID)
            cursor.execute(query,(number,user.id))
            conn.commit()
            await ctx.respond(f'{user.name} was given S{number:03}')
        elif number in schemArray:
            query=sql.SQL('UPDATE {} SET Schematics=Schematics || %s WHERE MemberID=%s').format(guildID)
            cursor.execute(query,(number,user.id))
            schemArray.remove(number)
            query=sql.SQL('UPDATE {} SET Schematics=%s WHERE MemberID=%s').format(guildID)
            cursor.execute(query,(schemArray,user.id))
            conn.commit()
            await ctx.respond(f'you gave {user.name} S{number:03}') 
        else:
            await ctx.respond('you cannot give what you don\'t have', ephemeral=True)
    else:
        number-=1
        query=sql.SQL('SELECT Items FROM MASTER_LIST WHERE Category=%s')
        cursor.execute(query,(category[-2]))
        categoryItems=cursor.fetchone()[0]
        query=sql.SQL('SELECT Items FROM {} WHERE MemberID=%s').format(guildID)
        cursor.execute(query, (user.id,))
        itemArray=cursor.fetchone()[0]
        if number>=len(categoryItems) or number<0:
            await ctx.respond('number is wrong, that\'s not a real item', ephemeral=True)
        else:
            choice=categoryItems[number]
            if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
                query=sql.SQL('UPDATE {0} SET Items=array_append(Items,%s) WHERE MemberID=%s').format(guildID)
                cursor.execute(query,(choice, user.id))
                conn.commit()
                await ctx.respond(f'{user.name} was given {choice} ({category[-2]}{number+1:03})')
            elif choice in itemArray:
                query=sql.SQL('UPDATE {} SET Items=Items || %s WHERE MemberID=%s').format(guildID)
                cursor.execute(query,(choice,user.id))
                itemArray.remove(choice)
                query=sql.SQL('UPDATE {} SET Items=%s WHERE MemberID=%s').format(guildID)
                cursor.execute(query,(itemArray,user.id))
                conn.commit()
                await ctx.respond(f'you gave {user.name} {choice}({category[-2]}{number+1:03})')
            else:
                await ctx.respond('you cannot give what you don\'t have', ephemeral=True)

@client.slash_command(description="remove item from player's inventory (GM only)")
async def remove(ctx, user:discord.Option(discord.Member, "who to take from"), category:discord.Option(str,choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I),','Weapon(W)', 'Schematic(S)']),number:discord.Option(int, "what serial number of item", min_value=1)):
    if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
        cursor=conn.cursor()
        guildID=sql.Identifier(str(user.guild.id))
        if category=='Schematic(S)':
            query=sql.SQL('SELECT Schematics FROM {} WHERE MemberID=%s').format(guildID)
            cursor.execute(query, (user.id,))
            schemArray=cursor.fetchone()[0]
            if number in schemArray:
                schemArray.remove(number)
                query=sql.SQL('UPDATE {} SET Schematics=%s WHERE MemberID=%s').format(guildID)
                cursor.execute(query,(schemArray,user.id))
                conn.commit()
                await ctx.respond(f'Schematic S{number:03} was removed from {user.name}')
            else:
                await ctx.respond('Target does not posses that item.', ephemeral=True)
        else:
            query=sql.SQL('SELECT Items FROM MASTER_LIST WHERE Category=%s')
            cursor.execute(query,(category[-2]))
            categoryItems=cursor.fetchone()[0]
            if number>=len(categoryItems) or number<0:
                await ctx.respond('number is wrong, that\'s not a real item', ephemeral=True)
            item=categoryItems[number-1]
            query=sql.SQL('SELECT Items FROM {} WHERE MemberID=%s').format(guildID)
            cursor.execute(query, (user.id,))
            itemArray=cursor.fetchone()[0]
            if item in itemArray:
                itemArray.remove(item)
                query=sql.SQL('UPDATE {} SET Items=%s WHERE MemberID=%s').format(guildID)
                cursor.execute(query,(itemArray,user.id))
                conn.commit()
                await ctx.respond(f'Item {item}({category[-2]}{number:03}) removed from {user.name}')
            else:
                await ctx.respond('Target does not posses that item.', ephemeral=True)
    else:
        await ctx.respond('You do not have permission to rob people.', ephemeral=True)
            
@client.slash_command(description="add materials from random table")
async def scavenge(ctx, user:discord.Option(discord.Member),table:discord.Option(str, choices=['Standard', 'Overseer', 'Monarch', 'Weapon', 'Item'])):
    if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
        cursor=conn.cursor()
        response=''
        for category in SCAVENGE_TABLES[table]:
            query=sql.SQL('SELECT items FROM master_list WHERE category=%s')
            cursor.execute(query,(category,))
            choiceArray=cursor.fetchone()[0]
            choice=random.choice(choiceArray)
            response+=choice+', '
            query=sql.SQL('UPDATE {0} SET Items=array_append(Items,%s) WHERE MemberID=%s').format(sql.Identifier(str(user.guild.id)))
            cursor.execute(query,(choice, user.id))
        conn.commit()
        await ctx.respond(f'{user.name} scavenged {response}')
    else:
        await ctx.respond('can\'t scavenge without the GM\'s premission!', ephemeral=True)

client.run(ORVYT_TOKEN)