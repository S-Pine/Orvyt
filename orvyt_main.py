import discord
import random
from os import environ
from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2 import sql
from psycopg2.extensions import AsIs
from psycopg2.extras import RealDictCursor
import string
from ast import literal_eval
load_dotenv()
# DATABASE_URL=environ['DATABASE_URL']
conn=connect(environ['DATABASE_INFO'])
intents = discord.Intents.default()
intents.members = True

client=discord.Bot(intents=intents)

SCAVENGE_TABLES={
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
    weapon: create, edit and view weapons!
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
    await ctx.respond(str(random.randint(1,10)), ephemeral=not display)

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
                query=sql.SQL('UPDATE {} SET Items=%s WHERE MemberID=%s').format(guildID)
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
        await ctx.respond('can\'t scavenge without the GM\'s premission!')

masterlist=client.create_group('masterlist')

@masterlist.command(description="add possible material to master list")
async def add(ctx, category:discord.Option(str, choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I)']),name:discord.Option(str, 'name of object')):
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
async def remove(ctx, category:discord.Option(str, choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)','Item(I),'])):
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

@viewCmnds.command(description="view player's inventory")
async def inventory(ctx, user:discord.Option(discord.Member, "whose invnetory"), display:discord.Option(bool,"display command result to others")=True):
    cursor=conn.cursor()
    query=sql.SQL('SELECT Items FROM {} where MemberID=%s').format(sql.Identifier(str(user.guild.id)))
    cursor.execute(query,(user.id,))
    inventory=cursor.fetchone()[0]
    for i,item in enumerate(inventory):
        print(item)
        if item[0]=='W':
            query=sql.SQL('SELECT name FROM Weapons.{} WHERE Index=%s').format(sql.Identifier(str(user.guild.id)))
            cursor.execute(query,(item[1:],))
            response=cursor.fetchone()[0]
            if response:
                inventory[i]=response
            else:
                inventory.remove(item)
                query=sql.SQL('UPDATE {} SET items=%s WHERE MemberID=%s').format(sql.Identifier(str(user.guild.id)))
                cursor.execute(query,(inventory,user.id))
                conn.commit()
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
            await ctx.respond(', '.join(map(lambda a: 'S{:03}'.format(a), inventory)), ephemeral=not display)
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
            "Charge_Time":(1,2,3),
            "Trait":5,
            "blast_radius":(0,)
        },
        "D":{
            "Range":(1,),
            "Damage":(1,2),
            "Charge_Time":(1,2),
            "Trait":10,
            "blast_radius":(0,)
        },
        "C":{
            "Range":(1,),
            "Damage":(1,2),
            "Charge_Time":(2,),
            "Trait":25,
            "blast_radius":(0,)
        },
        "B":{
            "Range":(1,),
            "Damage":(1,2,3),
            "Charge_Time":(1,),
            "Trait":50,
            "blast_radius":(0,)
        },
        "A":{
            "Range":(1,),
            "Damage":(2,3),
            "Charge_Time":(1,),
            "Trait":90,
            "blast_radius":(0,)
        },
        "U":{
            "Range":(1,),
            "Damage":(1,2,3,4),
            "Charge_Time":(1,2),
            "Trait":50,
            "blast_radius":(0,)
        }
    },
   "Standard":{
        "F":{
            "Range":(1,2,3),
            "Damage":(1,2),
            "Charge_Time":(3,4,5),
            "Trait":5,
            "blast_radius":(0,)
        },
        "D":{
            "Range":(2,3),
            "Damage":(2),
            "Charge_Time":(3,4),
            "Trait":10,
            "blast_radius":(0,)
        },
        "C":{
            "Range":(3,),
            "Damage":(2,3),
            "Charge_Time":(3,),
            "Trait":25,
            "blast_radius":(0,)
        },
        "B":{
            "Range":(3,4),
            "Damage":(3,4),
            "Charge_Time":(2,3),
            "Trait":50,
            "blast_radius":(0,)
        },
        "A":{
            "Range":(4,5),
            "Damage":(4,5),
            "Charge_Time":(2,),
            "Trait":90,
            "blast_radius":(0,)
        },
        "U":{
            "Range":(1,2,3,4,5,6),
            "Damage":(1,2,3,4,5),
            "Charge_Time":(1,2,3,4,5,6),
            "Trait":50,
            "blast_radius":(0,)
        }
    },
    "Strife":{
        "F":{
            "Range":(2,3),
            "Damage":(2,3,4),
            "Charge_Time":(5,6),
            "Trait":5,
            "blast_radius":(1,2)
        },
        "D":{
            "Range":(3,4),
            "Damage":(3,4),
            "Charge_Time":(4,5,6),
            "Trait":10,
            "blast_radius":(1,2,3)
        },
        "C":{
            "Range":(4,5),
            "Damage":(3,4,5),
            "Charge_Time":(4,5),
            "Trait":25,
            "blast_radius":(2,3)
        },
        "B":{
            "Range":(4,5,6),
            "Damage":(4,5),
            "Charge_Time":(3,4,5),
            "Trait":50,
            "blast_radius":(3,4)
        },
        "A":{
            "Range":(5,6,7),
            "Damage":(4,5,6),
            "Charge_Time":(2,3,4),
            "Trait":90,
            "blast_radius":(3,4,5)
        },
        "U":{
            "Range":(2,3,4,5,6,7),
            "Damage":(1,2,3,4,5,6,7),
            "Charge_Time":(2,3,4,5,6),
            "Trait":50,
            "blast_radius":(1,2,3,4,5)
        }
    },
    "Long":{
        "F":{
            "Range":(5,6,7,8),
            "Damage":(3,4,5),
            "Charge_Time":(5,6,7,8),
            "Trait":5,
            "blast_radius":(0,)
        },
        "D":{
            "Range":(5,6,7,8,9),
            "Damage":(4,5,6),
            "Charge_Time":(5,6,7),
            "Trait":10,
            "blast_radius":(0,)
        },
        "C":{
            "Range":(6,7,8,9),
            "Damage":(4,5,6,7),
            "Charge_Time":(4,5,6),
            "Trait":25,
            "blast_radius":(0,)
        },
        "B":{
            "Range":(7,8,9,10),
            "Damage":(6,7,8,9),
            "Charge_Time":(4,5),
            "Trait":50,
            "blast_radius":(0,)
        },
        "A":{
            "Range":(7,8,9,10,11),
            "Damage":(7,8,9,10),
            "Charge_Time":(3,4,5),
            "Trait":90,
            "blast_radius":(0,)
        },
        "U":{
            "Range":(5,6,7,8,9,10,11,12),
            "Damage":(3,4,5,6,7,8,9,10),
            "Charge_Time":(3,4,5,6,7,8),
            "Trait":50,
            "blast_radius":(0,)
        }
    }
}

TRAITS=(
    ("Faulty Calibration", "{} Aim when this weapon is in use.",(-1,-2),),
    ("Heavy", "{} Swift when this weapon is equipped.",(-1,-2)),
    ("Assistance", "+{} Aim when this weapon is in use.",(1,2)),
    ("Combustive", "This weapon has a +1 Blast Radius",),
    ("Vampiric Materia", "If a successful strike with this weapon is made, roll a D10, if it rolls above {}, heal {} Health.",(3,4,5,6,7),(1,2)),
    ("Strike Through", "If an entity is successfully struck, and there are other entities directly behind them within range, they are also struck.",),
    ("Faulty Regulator", "After {} uses, this weapon cannot be used for the user’s next full turn.",(2,3,4)),
    ("Harpoon", "If an entity is successfully struck, they are pulled towards the user by {} tiles.",(1,2,3,4)),
    ("Incendiary", "Successfully struck targets take {} Damage Per Turn.",(1,2)),
    ("Irradiated", "Successfully struck targets take {} Damage Per Turn.",(1,2,3)),
    ("Intensive Recoil", "User takes {} damage after use.",(1,2)),
    ("Faulty Scope", "This weapon has a {} Range.",(-1,-2)),
    ("Shiver Shot", "Successfully struck targets take {} Paralysis Per Turn.",(1,2)),
    ("Permafrost", "Successfully struck targets take {} Paralysis Per Turn.",(1,2,3)),
    ("Perfect Calibration", "This weapon has +{} damage.",(1,2)),
    ("Light", "+{} Swift when this weapon is equipped.",(1,2)),
    ("Emergency Protocol", "When user has half or below Health remaining, this weapon has +{} damage.",(1,2,3)),
    ("All or Nothing", "If an entity is successfully struck, roll a D10, if the roll is 6 or above, the damage is doubled. If the roll is 5 or below, the damage is reduced to nothing.",),
    ("Harvester", "If a Drone entity is successfully struck, roll a D10, if the roll is {} or {}, the user gains a Metal Card.",(1,2,3,4,5,6,7,8,9,10),(1,2,3,4,5,6,7,8,9,10)),
    ("Bloodlust", "When using this weapon, the user may take {} Health in damage, if the weapon successfully strikes, deal an extra {} damage.",(1,2,3),(1,2,3)),
    ("High Voltage", "If an entity is successfully struck, and there are other entities within a {} range, those entities take {} damage.",(1,2,3),(1,2)),
    ("Fussy", "If this weapon is used, roll a D10, if the roll is {} or above, you may use it, if the roll is below, the weapon cannot be used for the remainder of the full turn.",(1,2,3,4,5,6,7,8,9)),
    ("Horn Mortar", "This weapon has +{} damage, but also has +{} Charge Time.",(3,4,5),(2,3,4,5,6)),
    ("Sleepy", "This weapon has a +{} additional Charge Time.",(1,2)),
    ("Metal Materia", "This weapon must consume a Metal Card when used, but gives an additional +{}) damage if a successful strike occurs.",(2,3)),
    ("No Questions Asked", "If the user’s Health reaches 0 or below, the weapon will self destruct, dealing {} damage to any entity in a {} range. ",(1,2,3,4,5)),
    ("Energy Efficient", "If this weapon’s default Charge Time is above 2, this weapon has a {} Charge Time bonus.",(-1,-2)),
    ("Materia Shield", "When in equipment, this weapon gives +{} Health to it’s user",(1,2,3)),
    ("Faulty Recoil", "When this weapon is used, user is knocked back {} tiles away from the targeted entity.",(1,2)),
    ("Shamefully Faulty", "When in Equipment, this weapon gives it’s user {} Health, {} Swift, and {} Aim.",(-1,-2),(-1,-2),(-1,-2)),
    ("Inaccurate", "When used, this weapon reduces a user’s D10 Aim roll by half or above.",),
    ("Faulty Guard", "{} Health when this weapon is equipped.",(-1,-2)),
    ("Greedy", "This weapon’s Charge Time is doubled.",),
    ("Combustion Deficiency", "If this weapon has a Blast Radius of 3 or above, {} Blast Radius.",(-1,-2)),
    ("Perfect Aim", "This weapon has a +{} Range.",(1,2)),
    ("Majesty", "When in Equipment, this weapon gives +1 to Aim, Health, and Swift.",),
    ("Banker", "This weapon costs {} Credit(s) per use.",(1,2,3)),
    ("Sturdy", "When in equipment, this weapon gives its user {} Swift, but does an additional {} damage when a strike is successful.",(-1,-2),(1,2) ),
    ("Nursing Materia", "When in equipment, this weapon gives its user a {} Aim, but at the end of the users full turn they may roll a D10, and if it is {} or above, they heal 1 Health.",(-1,-2),(3,4,5,6,7)),
    ("Dampening", "If the user is organic, when in equipment the user has {} Thought.",(-1,-2)),
    ("Willed", "When used, roll for Thought instead of Aim.",),
    ("Cold Steel", "Weapon damage is doubled if the environment is cold, if hot, weapon damage is reduced to half or above.",),
    ("Heat Dependent", "Weapon damage is doubled if the environment is hot, if cold, weapon damage is reduced to half or above.",),
)

weaponCmnds=client.create_group('weapon')

@weaponCmnds.command(description="generate a weapon")
async def compose(ctx, type:discord.Option(str, choices=['Fray','Standard','Strife','Long']),grade:discord.Option(str,choices=['F','D','C','B','A','U'])):
    if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
        cursor=conn.cursor()
        choice=WEAPON_TABLES[type][grade]
        weapon={"type":type,"grade":grade}
        weapon['range']=random.choice(choice['Range'])
        weapon['damage']=random.choice(choice['Damage'])
        weapon['charge_time']=random.choice(choice['Charge_Time'])
        weapon['blast_radius']=random.choice(choice['blast_radius'])
        if random.randint(1,100)<=choice['Trait']:
            weapon["trait"]=trait_selector()
        else:
            weapon['trait']='none'
        nameOptions=string.ascii_uppercase+string.digits
        query=sql.SQL("SELECT Name FROM Weapons.{0}").format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query)
        takenNames=cursor.fetchall()
        while True:
            name='W'+"".join(random.choices(nameOptions,k=5))
            if not ((name,) in takenNames):
                weapon['name']=name
                break
        columns=weapon.keys()
        query=sql.SQL("INSERT INTO Weapons.{0} (%s) VALUES %s").format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query, (AsIs(', '.join(columns)), tuple([str(weapon[column]) for column in columns])))
        conn.commit()
        await ctx.respond('Weapon Created', embed=weapon_embed(weapon))
    else:
        await ctx.respond('You do not have permission to do that')

@weaponCmnds.command( description='rename a weapon')
async def rename(ctx, weapon:discord.Option(str), newname:discord.Option(str)):
    cursor=conn.cursor()
    query=sql.SQL('SELECT EXISTS( SELECT * FROM Weapons.{0} WHERE Name=%s)').format(sql.Identifier(str(ctx.interaction.guild.id)))
    cursor.execute(query,(newname,))
    nameTaken=cursor.fetchone()[0]
    if nameTaken:
        await ctx.respond(f'{newname} is already taken', ephemeral=True)
    else:
        query=sql.SQL('UPDATE Weapons.{0} SET Name=%s WHERE Name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query, (newname,weapon))
        conn.commit()
        await ctx.respond(f'{weapon} has become {newname}')

@weaponCmnds.command(description='show stats for weapon')
async def display(ctx, weapon:discord.Option(str), display:discord.Option(bool)=True):
    cursor=conn.cursor(cursor_factory=RealDictCursor)
    query=sql.SQL('SELECT * FROM Weapons.{0} WHERE Name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
    cursor.execute(query,(weapon,))
    response=cursor.fetchone()
    if response:
        await ctx.respond('here it is!',embed=weapon_embed(response), ephemeral=not display)
    else:
        await ctx.respond('weapon does not exist', ephemeral=not display)

@weaponCmnds.command(description='rework a weapon')
async def rework(ctx, weapon:discord.Option(str)):
    cursor=conn.cursor(cursor_factory=RealDictCursor)
    query=sql.SQL('SELECT * FROM Weapons.{0} WHERE Name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
    cursor.execute(query,(weapon,))
    chosenWeapon=cursor.fetchone()
    weaponKind=WEAPON_TABLES[chosenWeapon['type']][chosenWeapon['grade']]
    newWeapon=chosenWeapon.copy()
    newWeapon['range']=random.choice(weaponKind['Range'])
    newWeapon['damage']=random.choice(weaponKind['Damage'])
    newWeapon['charge_time']=random.choice(weaponKind['Charge_Time'])
    newWeapon['blast_radius']=random.choice(weaponKind['blast_radius'])
    if random.randint(1,100)<=weaponKind['Trait']:
        newWeapon['trait']=trait_selector()
    else:
        newWeapon['trait']='none'
    for i in ('range','damage','charge_time','trait', 'blast_radius'):
        query=sql.SQL("UPDATE Weapons.{0} SET {1}=%s WHERE name=%s").format(sql.Identifier(str(ctx.interaction.guild.id)),sql.Identifier(i))
        cursor.execute(query, (newWeapon[i],newWeapon['name']))
    conn.commit()
    await ctx.respond('new & improved! (maybe)', embed=weapon_embed(newWeapon))

@weaponCmnds.command()
async def give(ctx, user:discord.Option(discord.Member,'whom to give'),weapon:discord.Option(str, 'name of weapon to give')):
    cursor=conn.cursor()
    query=sql.SQL('SELECT Index FROM Weapons.{} WHERE name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
    cursor.execute(query,(weapon,))
    weaponSerial=cursor.fetchone()[0]
    if weaponSerial==None:
        await ctx.respond('weapon not found')
    else:
        if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])== None:
            query=sql.SQL('SELECT Items FROM {0} WHERE MemberId=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
            cursor.execute(query,(ctx.interaction.guild.id))
            itemArray=cursor.fetchone()[0]
            if itemArray == None:
                await ctx.respond("you cannot give what you don't have", ephemeral=True)
                return
            else:
                itemArray.remove("W"+weaponSerial)
                query=sql.SQL('UPDATE {0} SET Items=%s WHERE MemberId=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
                cursor.execute(query,(itemArray,ctx.interaction.user.id))
        query=sql.SQL('UPDATE {0} SET Items=array_append(Items,%s) WHERE MemberID=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query,("W"+str(weaponSerial),user.id))
        conn.commit()
        await ctx.respond(f'{weapon} was given to {user.name}')

@weaponCmnds.command(description='for debugging')
async def delete(ctx, weapon:discord.Option(str)):
    if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
        cursor=conn.cursor()
        query=sql.SQL('SELECT index FROM Weapons.{} WHERE name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query,(weapon,))
        weaponIndex=cursor.fetchone()[0]
        query=sql.SQL('DELETE FROM Weapons.{} WHERE name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query,(weapon,))
        query=sql.SQL('UPDATE {} SET Items=array_remove(Items,%s)').format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query,("W"+str(weaponIndex),))
        conn.commit()
        await ctx.respond(f'{weapon} has been removed')
    else:
        await ctx.respond('You do not have permission to do that.')

@weaponCmnds.command(description="custom Weapon")
async def design(ctx, name:discord.Option(str),type:discord.Option(str, choices=['Fray','Standard','Strife','Long']),grade:discord.Option(str,choices=['F','D','C','B','A','U']),range:discord.Option(int),damage:discord.Option(int),chargetime:discord.Option(int),blastradius:discord.Option(int),trait:discord.Option(str)="none", traitchoice1:discord.Option(int)=None,traitchoice2:discord.Option(int)=None):
    if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
        response=f"{name} created!"
        cursor=conn.cursor()
        query=sql.SQL("SELECT Name FROM Weapons.{0}").format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query)
        takenNames=cursor.fetchall()
        if ((name,) in takenNames):
            await ctx.respond('that name is taken.')
        else:
            try:
                weapon={
                    "name":name,
                    "Range":range,
                    "type":type,
                    "grade":grade,
                    "Charge_Time":chargetime,
                    "blast_radius":blastradius,
                    "Damage":damage,
                    "trait":"none"
                }
                if trait!="none":
                    for i in TRAITS:
                        if trait.lower()==i[0].lower():
                            trait=list(i[:2])
                            nums=[]
                            for j in i[2:]:
                                nums.append(random.choice(j))
                            if len(nums)!=0:
                                if len(nums)==1:
                                    trait[1]=trait[1].format(traitchoice1)
                                else:
                                    trait[1]=trait[1].format(traitchoice1,traitchoice2)
                            weapon['trait']="('"+"', '".join(trait)+"')"
                            break
                    else:
                        response=response+"trait not found."
                columns=weapon.keys()
                query=sql.SQL("INSERT INTO Weapons.{0} (%s) VALUES %s").format(sql.Identifier(str(ctx.interaction.guild.id)))
                cursor.execute(query, (AsIs(', '.join(columns)), tuple([str(weapon[column]) for column in columns])))
                conn.commit()
                await ctx.respond(response)
            except: 
                await ctx.respond('something went wrong! check if you put in the right trait parameters, or if you spelled the trait right, (capitalisation doesn\'t matter).')


def weapon_embed(weapon):
    trait='No trait'
    if weapon['trait']!="none":
        trait=literal_eval(weapon['trait'])
        trait=f'**{trait[0]}**: {trait[1]}'
    embed=discord.Embed(title=weapon['name'], colour=discord.Colour(gradeRGB[weapon['grade']]), description=trait)
    embed.add_field(name="Range", value=weapon['range'], inline=True)
    embed.add_field(name="Damage", value=weapon['damage'], inline=True)
    embed.add_field(name="Charge Time", value=weapon['charge_time'], inline=True)
    embed.add_field(name="Blast Radius", value=weapon['blast_radius'], inline=True)
    embed.set_footer(text=f"{weapon['type']} {weapon['grade']}")
    return embed   

def trait_selector(traitChoice):
    traitChoice=random.choice(TRAITS)
    trait=list(traitChoice[:2])
    nums=[]
    for i in traitChoice[2:]:
        nums.append(random.choice(i))
    if len(nums)!=0:
        if len(nums)==1:
            trait[1]=trait[1].format(nums[0])
        else:
            trait[1]=trait[1].format(*nums)
    return "('"+"', '".join(trait)+"')"

client.run(environ['ORVYT_TOKEN'])