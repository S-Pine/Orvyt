import discord
import random
import os
import psycopg2
from psycopg2 import sql

DATABASE_URL=os.environ['DATABASE_URL']
conn=psycopg2.connect(DATABASE_URL, sslmode='require')
intents = discord.Intents.default()
intents.members = True

GUILD_IDS=[842493087905611826, 989761552083197982]
PLAYERS={}

client=discord.Bot(intents=intents, debug_guilds=GUILD_IDS)

MASTER_LIST={
    'M':['Aluminium', 'Cobalt', 'Copper', 'Graphite', 'Gold', 'Iron', 'Niobium', 'Silver', 'Steel','Titanium'],
    'F':['Dihydrogen Oxide', 'Helium', 'Hydrogen', 'Oxygen', 'Tritium', 'Xenon'],
    'R':['Radium', 'Thorium', 'Plutonium', 'Polonium', 'Uranium'],
    'C':['Pneumatic piston', 'Processor', 'Drone ciruit', 'Overseer Circuit', 'Monarch circuit', 'Fluid cell', 'Reactor', 'Battery cell', 
    'Ionic Thruster', 'Cobustive Thruster', 'Irradiated thruster', 'Pressure chamber', 'Spark fuse', 'Wiring', 'Black box'],
    'W':[],
    'I':[]
}
TABLES={
    'Standard':['M'],
    'Overseer':['M','R'],
    'Monarch':['C','F','R'],
    'Weapon':['M','C','C'],
    'Item':['M','C']
}
GM={}

@client.event
async def on_ready():
    print('Orvyt_Online!')
    cursor=conn.cursor()
    for guild in client.guilds:
        query=sql.SQL('CREATE TABLE {guildID} (MemberID BIGINT PRIMARY KEY, Credits INT DEFAULT 0, Items VARCHAR(25)[] DEFAULT ARRAY[]::VARCHAR(25)[], Schematics integer[] DEFAULT ARRAY[]::integer[])').format(guildID=sql.Identifier(str(guild.id)))
        cursor.execute(query)
        for role in guild.roles:
            if role.name=='Game Master': GM[guild.id]=role.id
        for member in guild.members:
            query=sql.SQL('INSERT INTO {guildID} (MemberID) VALUES (%s)').format(guildID=sql.Identifier(str(guild.id)))
            cursor.execute(query,(member.id,))

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

@client.event
async def on_member_join(member):
    cursor=conn.cursor()
    query=sql.SQL('INSERT INTO {guildID} (MemberID) VALUES (%s)').format(guildID=sql.Identifier(str(member.guild.id)))
    cursor.execute(query,(member.id,))

@client.slash_command()
async def help(ctx, display:discord.Option(bool,"display command result to others")=True):
    longmsg='My Commands! \ndten: returns a number between 1 and 10. \nlogall\*: logs all the information I have in this guild, necessary for when I need to be edited. \n'
    longmsg+='give: allows you to trade or be given items for your inventory! \nremove\*: removed the stated item from a player. \nscavenge\*: for rolling on random tables to give players items. \n'
    longmsg+='masterlist\*: the GM can add or remove possible items\n view: see player\'s inventories and schematics!\n credit\*\*: exhange credits!\n \*: GM only'
    await ctx.respond(longmsg, ephemeral=not display)

@client.slash_command(description="responds with a random number between 1 and 10")
async def dten(ctx, display:discord.Option(bool,"display command result to others")=True):
    await ctx.respond(str(random.randint(1,10)), ephemeral=not display)
    
@client.slash_command(description='logs all guild information (GM only)')
async def logall(ctx, display:discord.Option(bool,"display command result to others")=True):
    if ctx.interaction.user.get_role(PLAYERS[ctx.interaction.guild.id]['GM'] !=None) or ctx.interaction.user.id==693848229896388669:
        embed=discord.Embed.from_dict(PLAYERS[ctx.interaction.guild.id])
        await ctx.respond(embed=embed, ephemeral=not display)
    else:
        await ctx.respond('classified', ephemperal=True)

@client.slash_command(description='gives item to player\'s inventory')
async def give(ctx, user:discord.Option(discord.Member, "who to give to."), category:discord.Option(str,choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I)', 'Weapon(W)', 'Schematic(S)']), number:discord.Option(int, "what serial number of item", min_value=1)):
    guildID=sql.Identifier(str(user.guild.id))
    cursor=conn.cursor()
    if category=='Schematic(S)':
        query=sql.SQL('SELECT Schematics FROM {} WHERE MemberID=%s').format(guildID)
        cursor.execute(query,(user.id,))
        schemArray=cursor.fetchone()[0] 
        if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
            query=sql.SQL('UPDATE {} SET Schematics=Schematics || %s WHERE MemberID=%s').format(guildID)
            cursor.execute(query,(number,user.id))
            await ctx.respond(f'{user.name} was given S{number:03}')
        elif number in schemArray:
            query=sql.SQL('UPDATE {} SET Schematics=Schematics || %s WHERE MemberID=%s').format(guildID)
            cursor.execute(query,(number,user.id))
            schemArray.remove(number)
            query=sql.SQL('UPDATE {} SET Schematics=%s WHERE MemberID=%s').format(guildID)
            cursor.execute(query,(schemArray,user.id))
            await ctx.respond(f'you gave {user.name} S{number:03}') 
        else:
            await ctx.respond('you cannot give what you don\'t have')
    else:
        number-=1
        choice=MASTER_LIST[category[-2]][number]
        query=sql.SQL('SELECT Items FROM {} WHERE MemberID=%s').format(guildID)
        cursor.execute(query, (user.id,))
        itemArray=cursor.fetchone()[0]
        if number>=len(MASTER_LIST[category[-2]]) or number<0:
            ctx.respond('number is wrong, that\'s not a real item')
        elif ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
            query=sql.SQL('UPDATE {0} SET Items=array_append(Items,%s) WHERE MemberID=%s').format(guildID)
            cursor.execute(query,(choice, user.id))
            await ctx.respond(f'{user.name} was given {choice} ({category[-2]}{number+1:03})')
        elif choice in itemArray:
            query=sql.SQL('UPDATE {} SET Items=Items || %s WHERE MemberID=%s').format(guildID)
            cursor.execute(query,(choice,user.id))
            itemArray.remove(choice)
            query=sql.SQL('UPDATE {} SET Items=%s WHERE MemberID={}').format(guildID)
            cursor.execute(query,(itemArray,user.id))
            await ctx.respond(f'you gave {user.name} {choice}({category[-2]}{number+1:03})')
        else:
            await ctx.respond('you cannot give what you don\'t have')

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
                await ctx.respond(f'Schematic S{number:03} was removed from {user.name}')
            else:
                await ctx.respond('Target does not posses that item.')
        else:
            item=MASTER_LIST[category[-2]][number-1]
            query=sql.SQL('SELECT Items FROM {} WHERE MemberID=%s').format(guildID)
            cursor.execute(query, (user.id,))
            itemArray=cursor.fetchone()[0]
            print(itemArray)
            if item in itemArray:
                itemArray.remove(item)
                query=sql.SQL('UPDATE {} SET Items=%s WHERE MemberID=%s').format(guildID)
                cursor.execute(query,(itemArray,user.id))
                await ctx.respond(f'Item {item}({category[-2]}{number:03}) removed from {user.name}')
            else:
                await ctx.respond('Target does not posses that item.')
    else:
        await ctx.respond('You do not have permission to rob people.', ephemeral=True)
            

@client.slash_command(description="add materials from random table")
async def scavenge(ctx, user:discord.Option(discord.Member),table:discord.Option(str, choices=['Standard', 'Overseer', 'Monarch', 'Weapon', 'Item'])):
    if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
        cursor=conn.cursor()
        response=''
        for category in TABLES[table]:
            choice=random.choice(MASTER_LIST[category])
            response+=choice+', '
            query=sql.SQL('UPDATE {0} SET Items=array_append(Items,%s) WHERE MemberID=%s').format(sql.Identifier(str(user.guild.id)))
            cursor.execute(query,(choice, user.id))
        await ctx.respond(f'{user.name} scavenged {response}')
    else:
        await ctx.respond('can\'t scavenge without the GM\'s premission!')

masterlist=client.create_group('masterlist')

@masterlist.command(description="add possible material to master list")
async def add(ctx, category:discord.Option(str, choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I),','Weapon(W)']),name:discord.Option(str, 'name of object')):
    category=category[-2]
    MASTER_LIST[category].append(name)
    await ctx.respond(f'{name}({category}{len(MASTER_LIST[category]):03}) was added to the list')

@masterlist.command(description="remove last material from master list")
async def remove(ctx, category:discord.Option(str, choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I),','Weapon(W)'])):
    category=category[-2]
    removed=MASTER_LIST[category].pop(len(MASTER_LIST[category])-1)
    await ctx.respond(f'{removed}({category}{len(MASTER_LIST[category])+1:03}) was removed')

viewCmnds=client.create_group('view')

@viewCmnds.command(description="view player's items")
async def items(ctx, user:discord.Option(discord.Member, "whose items"), display:discord.Option(bool,"display command result to others")=True):
    cursor=conn.cursor()
    query=sql.SQL('SELECT Items FROM {guildID} where MemberID=%s').format(guildID=sql.Identifier(str(user.guild.id)))
    cursor.execute(query,(user.id,))
    inventory=cursor.fetchone()[0]
    if len(inventory):
        await ctx.respond(', '.join(inventory), ephemeral=not display)
    else:
        await ctx.respond('target has no items', ephemeral=not display)

@viewCmnds.command(description="view player's schematics")
async def schematics(ctx, user:discord.Option(discord.Member, "whose schemaitcs"), display:discord.Option(bool,"display command result to others")=True):
        cursor=conn.cursor()
        query=sql.SQL('SELECT Schematics FROM {guildID} where MemberID=%s').format(guildID=sql.Identifier(str(user.guild.id)))
        cursor.execute(query,(user.id,))
        inventory=cursor.fetchone()[0]
        if len(inventory)>0:
            await ctx.respond(', '.join(inventory), ephemeral=not display)
        else:
            await ctx.respond('target has no schematics', ephemeral=not display)

credit=client.create_group('credit')

@credit.command(description="give money to player")
async def give(ctx, user:discord.Option(discord.Member, "whom to give money to."), wealth:discord.Option(int,"how much money to give", min_value=0)):
    PLAYERS[user.guild.id][user.id]['Credits']+=wealth
    if ctx.interaction.user.get_role(PLAYERS[ctx.interaction.guild.id]['GM'])!= None:
        await ctx.respond(f'{user.name} now has {PLAYERS[user.guild.id][user.id]["Credits"]} credits')
    else:
        PLAYERS[ctx.interaction.guild.id][ctx.interaction.user.id]['Credits']-=wealth
        await ctx.respond(f'{ctx.interaction.user.name} gave {user.name} {wealth} credits')

@credit.command(description="take player's money (GM only)")
async def remove(ctx, user:discord.Option(discord.Member, 'who\'s money to take'), wealth:discord.Option(int,"how much money to give", min_value=0)):
    if ctx.interaction.user.get_role(PLAYERS[ctx.interaction.guild.id]['GM'])!= None:
        PLAYERS[user.guild.id][user.id]['Credits']-=wealth
        await ctx.respond(f'{user.name} now has {PLAYERS[user.guild.id][user.id]["Credits"]} credits')
    else:
        await ctx.respond('You do not have permission to rob people.', ephemeral=True)

@credit.command(description="view player's money")
async def view(ctx, user:discord.Option(discord.Member, 'who\'s money to view'), displayed:discord.Option(bool,"display command result to others")=True):
    await ctx.respond(f'{user.name} has {PLAYERS[user.guild.id][user.id]["Credits"]} Credits', ephemeral= not displayed)

client.run(os.environ['ORVYT_TOKEN'])