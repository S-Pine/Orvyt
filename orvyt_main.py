import discord
import random
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
load_dotenv()
DATABASE_URL=os.environ['DATABASE_URL']
conn=psycopg2.connect(DATABASE_URL, sslmode='require')
intents = discord.Intents.default()
intents.members = True

client=discord.Bot(intents=intents)

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
    for guild in client.guilds:
        for role in guild.roles:
            if role.name=='Game Master': GM[guild.id]=role.id
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
    logall\*: logs all the information I have in this guild, necessary for when I need to be edited.
    give: allows you to trade or be given items for your inventory! 
    remove\*: removed the stated item from a player. 
    scavenge\*: for rolling on random tables to give players items. 
    masterlist\*: the GM can add or remove possible items
     view: see player\'s inventories and schematics!
      credit: exhange credits!
       \*: GM only
    """
    await ctx.respond(longmsg, ephemeral=not display)

@client.slash_command(description="DO NOT TOUCH")
async def commmitdb(ctx):
    if ctx.interaction.user.id==693848229896388669:
        cursor=conn.cursor()
        for guild in client.guilds:
            query=sql.SQL('CREATE TABLE {guildID} (MemberID BIGINT PRIMARY KEY, Credits INT DEFAULT 0, Items VARCHAR(25)[] DEFAULT ARRAY[]::VARCHAR(25)[], Schematics integer[] DEFAULT ARRAY[]::integer[])').format(guildID=sql.Identifier(str(guild.id)))
            cursor.execute(query)
            for member in guild.members:
                query=sql.SQL('INSERT INTO {guildID} (MemberID) VALUES (%s)').format(guildID=sql.Identifier(str(guild.id)))
                cursor.execute(query,(member.id,))
        conn.commit()
        await ctx.respond("Database has been commited, or duplicated if you're stupid")
    else:
        await ctx.respond('you do not have permission to do that.', ephemeral=True)

@client.slash_command(description="responds with a random number between 1 and 10")
async def dten(ctx, display:discord.Option(bool,"display command result to others")=True):
    await ctx.respond(str(random.randint(1,10)), ephemeral=not display)

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
            await ctx.respond('you cannot give what you don\'t have')
    else:
        number-=1
        query=sql.SQL('SELECT Items FROM MASTER_LIST WHERE Category=%s')
        cursor.execute(query,(category[-2]))
        categoryItems=cursor.fetchone()[0]
        query=sql.SQL('SELECT Items FROM {} WHERE MemberID=%s').format(guildID)
        cursor.execute(query, (user.id,))
        itemArray=cursor.fetchone()[0]
        if number>=len(categoryItems) or number<0:
            await ctx.respond('number is wrong, that\'s not a real item')
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
                query=sql.SQL('UPDATE {} SET Items=%s WHERE MemberID={}').format(guildID)
                cursor.execute(query,(itemArray,user.id))
                conn.commit()
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
                conn.commit()
                await ctx.respond(f'Schematic S{number:03} was removed from {user.name}')
            else:
                await ctx.respond('Target does not posses that item.')
        else:
            query=sql.SQL('SELECT Items FROM MASTER_LIST WHERE Category=%s')
            cursor.execute(query,(category[-2]))
            categoryItems=cursor.fetchone()[0]
            if number>=len(categoryItems) or number<0:
                await ctx.respond('number is wrong, that\'s not a real item')
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
        conn.commit()
        await ctx.respond(f'{user.name} scavenged {response}')
    else:
        await ctx.respond('can\'t scavenge without the GM\'s premission!')

masterlist=client.create_group('masterlist')

@masterlist.command(description="add possible material to master list")
async def add(ctx, category:discord.Option(str, choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I),','Weapon(W)']),name:discord.Option(str, 'name of object')):
    if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
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
async def remove(ctx, category:discord.Option(str, choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I),','Weapon(W)'])):
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

viewCmnds=client.create_group('view')

@viewCmnds.command(description="view player's items")
async def items(ctx, user:discord.Option(discord.Member, "whose items"), display:discord.Option(bool,"display command result to others")=True):
    cursor=conn.cursor()
    query=sql.SQL('SELECT Items FROM {} where MemberID=%s').format(sql.Identifier(str(user.guild.id)))
    cursor.execute(query,(user.id,))
    inventory=cursor.fetchone()[0]
    if len(inventory):
        await ctx.respond(', '.join(inventory), ephemeral=not display)
    else:
        await ctx.respond('target has no items', ephemeral=not display)

@viewCmnds.command(description="view player's schematics")
async def schematics(ctx, user:discord.Option(discord.Member, "whose schemaitcs"), display:discord.Option(bool,"display command result to others")=True):
        cursor=conn.cursor()
        query=sql.SQL('SELECT Schematics FROM {} where MemberID=%s').format(sql.Identifier(str(user.guild.id)))
        cursor.execute(query,(user.id,))
        inventory=cursor.fetchone()[0]
        if len(inventory)>0:
            await ctx.respond(', '.join(inventory), ephemeral=not display)
        else:
            await ctx.respond('target has no schematics', ephemeral=not display)

credit=client.create_group('credit')

@credit.command(description="give money to player")
async def give(ctx, user:discord.Option(discord.Member, "whom to give money to."), wealth:discord.Option(int,"how much money to give", min_value=0)):
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
async def remove(ctx, user:discord.Option(discord.Member, 'who\'s money to take'), wealth:discord.Option(int,"how much money to give", min_value=0)):
    if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
        cursor=conn.cursor()
        query=sql.SQL('UPDATE {} SET Credits=Credits-%s WHERE MemberID=%s').format(sql.Identifier(str(user.guild.id)))
        cursor.execute(query,(wealth,user.id))
        conn.commit()
        await ctx.respond(f'{user.name} lost {wealth} credits')
    else:
        await ctx.respond('You do not have permission to rob people.', ephemeral=True)

@credit.command(description="view player's money")
async def view(ctx, user:discord.Option(discord.Member, 'who\'s money to view'), displayed:discord.Option(bool,"display command result to others")=True):
    cursor=conn.cursor()
    query=sql.SQL('SELECT Credits FROM {} WHERE MemberID=%s').format(sql.Identifier(str(user.guild.id)))
    cursor.execute(query, (user.id,))
    creditNum=cursor.fetchone()[0]
    await ctx.respond(f'{user.name} has {creditNum} Credits', ephemeral= not displayed)
gradeRGB={
    'A':16171112,
    'B':9320183,
    'C':10157135,
    'D':8902392,
    'F':6513507,
    'U':16732751
}

WEAPON_TABLES={
    "Fray":{
        "F":{
            "Range":(1,),
            "Damage":(1,),
            "Charge Time":(1,2,3),
            "Trait":5
        },
        "D":{
            "Range":(1,),
            "Damage":(1,2),
            "Charge Time":(1,2),
            "Trait":10
        },
        "C":{
            "Range":(1,),
            "Damage":(1,2),
            "Charge Time":(2,),
            "Trait":25
        },
        "B":{
            "Range":(1,),
            "Damage":(1,2,3),
            "Charge Time":(1,),
            "Trait":50
        },
        "A":{
            "Range":(1,),
            "Damage":(2,3),
            "Charge Time":(1,),
            "Trait":90
        },
        "U":{
            "Range":(1,),
            "Damage":(1,2,3,4),
            "Charge Time":(1,2),
            "Trait":50
        }
    },
   "Standard":{
        "F":{
            "Range":(1,2,3),
            "Damage":(1,),
            "Charge Time":(3,4,5),
            "Trait":5
        },
        "D":{
            "Range":(2,3),
            "Damage":(1,2),
            "Charge Time":(3,4),
            "Trait":10
        },
        "C":{
            "Range":(3,),
            "Damage":(2,3),
            "Charge Time":(3,),
            "Trait":25
        },
        "B":{
            "Range":(3,4),
            "Damage":(3,4),
            "Charge Time":(2,3),
            "Trait":50
        },
        "A":{
            "Range":(4,5),
            "Damage":(4,5),
            "Charge Time":(2,),
            "Trait":90
        },
        "U":{
            "Range":(1,2,3,4,5,6),
            "Damage":(1,2,3,4,5),
            "Charge Time":(1,2,3,4,5,6),
            "Trait":50
        }
    },
    "Strife":{
        "F":{
            "Range":(2,3),
            "Damage":(2,3,4),
            "Charge Time":(5,6),
            "Trait":5
        },
        "D":{
            "Range":(3,4),
            "Damage":(3,4),
            "Charge Time":(4,5,6),
            "Trait":10
        },
        "C":{
            "Range":(4,5),
            "Damage":(3,4,5),
            "Charge Time":(4,5),
            "Trait":25
        },
        "B":{
            "Range":(4,5,6),
            "Damage":(4,5),
            "Charge Time":(3,4,5),
            "Trait":50
        },
        "A":{
            "Range":(5,6,7),
            "Damage":(4,5,6),
            "Charge Time":(2,3,4),
            "Trait":90
        },
        "U":{
            "Range":(2,3,4,5,6,7),
            "Damage":(1,2,3,4,5,6,7),
            "Charge Time":(2,3,4,5,6),
            "Trait":50
        }
    },
    "Long":{
        "F":{
            "Range":(5,6,7,8),
            "Damage":(3,4,5),
            "Charge Time":(5,6,7,8),
            "Trait":5
        },
        "D":{
            "Range":(5,6,7,8,9),
            "Damage":(4,5,6),
            "Charge Time":(5,6,7),
            "Trait":10
        },
        "C":{
            "Range":(6,7,8,9),
            "Damage":(4,5,6,7),
            "Charge Time":(4,5,6),
            "Trait":25
        },
        "B":{
            "Range":(7,8,9,10),
            "Damage":(6,7,8,9),
            "Charge Time":(4,5),
            "Trait":50
        },
        "A":{
            "Range":(7,8,9,10,11),
            "Damage":(7,8,9,10),
            "Charge Time":(3,4,5),
            "Trait":90
        },
        "U":{
            "Range":(5,6,7,8,9,10,11,12),
            "Damage":(1,2,3,4,5,6,7),
            "Charge Time":(3,4,5,6,7,8),
            "Trait":50
        }
    }
}

@client.slash_command(description="generate a weapon")
async def compose(ctx, type:discord.Option(str, choices=['Fray','Standard','Strife','Long']),grade:discord.Option(str,choices=['F','D','C','B','A','U'])):
    choice=WEAPON_TABLES[type][grade]
    weapon={}
    weapon['Range']=random.choice(choice['Range'])
    weapon['Damage']



gradeRGB={
    'A':16171112,
    'B':9320183,
    'C':10157135,
    'D':8902392,
    'F':6513507,
    'U':16732751
}


client.run(os.environ['ORVYT_TOKEN'])