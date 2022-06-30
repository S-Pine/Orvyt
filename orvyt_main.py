import discord
import random
from dotenv import load_dotenv
from os import getenv
load_dotenv()

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
    'Ionic Thruster', 'Cobustive Thruster', 'Irradiated thruster', 'Pressure chamber', 'Spark fuse', 'Wiring', 'Black box']
}
TABLES={
    'Standard':['M'],
    'Overseer':['M','R'],
    'Monarch':['C','F','R'],
    'Weapon':['M','C','C'],
    'Item':['M','C']
}
SHORT_FORM={
    'Metal(M)':'M',
    'Fluid(F)':'F', 
    'Irradiated(R)':'R', 
    'Component(C)':'C', 
    'Schematic(S)':'S'
}

@client.event
async def on_ready():
    print('Orvyt_Online!')
    for guild in client.guilds:
        PLAYERS[guild.id]={}
        for role in guild.roles:
            if role.name=='Game Master': PLAYERS[guild.id]['GM']=role.id
        for member in guild.members:
            PLAYERS[guild.id][member.id]={'Credits':0, 'Inventory':[], 'Schematics':[]}

@client.event
async def on_guild_join(guild):
    PLAYERS[guild.id]={}
    for member in guild.members:
        PLAYERS[guild.id][member.id]={'Credits':0, 'Inventory':[], 'Schematics':[]}
    for role in guild.roles:
            if role.name=='Game Master': PLAYERS[guild.id]['GM']=role.id

@client.event
async def on_member_join(member):
    PLAYERS[member.guild.id][member.id]={'Credits':0, 'Inventory':[], 'Schematics':[]}

@client.slash_command()
async def help(ctx, display:discord.Option(bool,"display command result to others")=True):
    longmsg='My Commands!\n dten: returns a number between 1 and 10.\n logall\*: logs all the information I have in this guild, necessary for when I need to be edited. \n give\*\*: allows you to trade or be given items for you inventory!\n'
    longmsg+='remove\*: removed the stated item from a player.\n scavenge\*: for rolling on random tables to give players items\n masterlist\*: the GM can add or remove possible items\n'
    longmsg+='view\*: see player\'s inventories and schematics!\n credit\*\*: exhange credits!\n \*: gm only\n \*\*: different for gm.'
    await ctx.respond(longmsg, ephemeral=not display)

@client.slash_command(description="responds with a random number between 1 and 10")
async def dten(ctx, display:discord.Option(bool,"display command result to others")=True):
    await ctx.respond(str(random.randint(1,10)), ephemeral=not display)
    
@client.slash_command(description='logs all guild information (GM only)')
async def logall(ctx, display:discord.Option(bool,"display command result to others")=True):
    if ctx.interaction.user.get_role(PLAYERS[ctx.interaction.guild.id]['GM'] !=None) or ctx.interaction.user.id==693848229896388669:
        await ctx.respond(str(PLAYERS[ctx.interaction.guild.id]), ephemeral=not display)
    else:
        await ctx.respond('classified', ephemperal=True)

@client.slash_command(description='gives item to player\'s inventory')
async def give(ctx, user:discord.Option(discord.Member, "who to give to."), category:discord.Option(str,choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)', 'Schematic(S)']), number:discord.Option(int, "what serial number of item", min_value=1)):
    category=SHORT_FORM[category]
    target=PLAYERS[user.guild.id][user.id]
    sender=PLAYERS[user.guild.id][ctx.interaction.user.id]
    if category=='S':
        if ctx.interaction.user.get_role(PLAYERS[ctx.interaction.guild.id]['GM'])!= None:
            target['Schematics'].append(number)
            await ctx.respond(f'{user.name} was given S{number:03}')
        elif number in sender['Schematics']:
            target['Schematics'].append(number)
            sender['Schematics'].remove(number)
            await ctx.respond(f'you gave {user.name} S{number:03}') 
        else:
            await ctx.respond('you cannot give what you don\'t have')
    else:
        number-=1
        choice=MASTER_LIST[category][number]
        if number>=len(MASTER_LIST[category]) or number<0:
            ctx.respond('number is wrong, that\'s not a real item')
        elif ctx.interaction.user.get_role(PLAYERS[ctx.interaction.guild.id]['GM'])!= None:
            target['Inventory'].append(choice)
            await ctx.respond(f'{user.name} was given {choice} ({category}{number+1:03})')
        elif choice in sender['Inventory']:
            target['Inventory'].append(choice)
            sender['Inventory'].remove(choice)
            await ctx.respond(f'you gave {user.name} {choice}({category}{number+1:03})')
        else:
            await ctx.respond('you cannot give what you don\'t have')

@client.slash_command("remove item from player's inventory (GM only)")
async def remove(ctx, user:discord.Option(discord.Member, "who to take from"), category:discord.Option(str,choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)', 'Schematic(S)']),number:discord.Option(int, "what serial number of item", min_value=1)):
    category=SHORT_FORM[category]
    target=PLAYERS[user.guild.id][user.id]
    if ctx.interaction.user.get_role(PLAYERS[ctx.interaction.guild.id]['GM'])!= None:
        if category=='S':
            if number in target['Schematics']:
                target['Schematics'].remove(item)
                await ctx.respond(f'Schematic S{number:03} was removed from {user.name}')
            else:
                await ctx.respond('Target does not posses that item.')
        else:
            item=MASTER_LIST[category][number-1]
            target['Inventory'].remove(item)
            await ctx.respond(f'Item {item}({category}{number:03}) removed from {user.name}')
    else:
        await ctx.respond('You do not have permission to rob people.', ephemeral=True)
            

@client.slash_command("add materials from random table")
async def scavenge(ctx, user:discord.Option(discord.Member),table:discord.Option(str, choices=['Standard', 'Overseer', 'Monarch', 'Weapon', 'Item'])):
    if ctx.interaction.user.get_role(PLAYERS[ctx.interaction.guild.id]['GM'])!= None:
        inventory=PLAYERS[user.guild.id][user.id]['Inventory']
        response=''
        for category in TABLES[table]:
            choice=random.choice(MASTER_LIST[category])
            response+=choice+', '
            inventory.append(choice)
        await ctx.respond(f'{user.name} scavenged {response}')
    else:
        await ctx.respond('can\'t scavenge without the GM\'s premission!')

masterlist=client.create_group('masterlist')

@masterlist.command("add possible material to master list")
async def add(ctx, category:discord.Option(str, choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)']),name:discord.Option(str, 'name of object')):
    category=SHORT_FORM[category]
    MASTER_LIST[category].append(name)
    await ctx.respond(f'{name}({category}{len(MASTER_LIST[category]):03}) was added to the list')

@masterlist.command("remove last material from master list")
async def remove(ctx, category:discord.Option(str, choices=['Metal(M)','Fluid(F)','Irradiated(R)','Component(C)'])):
    category=SHORT_FORM[category]
    removed=MASTER_LIST[category].pop(len(MASTER_LIST[category])-1)
    await ctx.respond(f'{removed}({category}{len(MASTER_LIST[category])+1:03}) was removed')

viewCmnds=client.create_group('view')

@viewCmnds.command("view player's items")
async def items(ctx, user:discord.Option(discord.Member, "whose items"), display:discord.Option(bool,"display command result to others")=True):
    await ctx.respond(str(PLAYERS[user.guild.id][user.id]['Inventory']), ephemeral=not display)

@viewCmnds.command("view player's schematics")
async def schematics(ctx, user:discord.Option(discord.Member, "whose schemaitcs"), display:discord.Option(bool,"display command result to others")=True):
        await ctx.respond(str(PLAYERS[user.guild.id][user.id]['Schematics']), ephemeral=not display)

credit=client.create_group('credit')

@credit.command("give money to player")
async def give(ctx, user:discord.Option(discord.Member, "whom to give money to."), wealth:discord.Option(int,"how much money to give", min_value=0)):
    PLAYERS[user.guild.id][user.id]['Credits']+=wealth
    if ctx.interaction.user.get_role(PLAYERS[ctx.interaction.guild.id]['GM'])!= None:
        await ctx.respond(f'{user.name} now has {PLAYERS[user.guild.id][user.id]["Credits"]} credits')
    else:
        PLAYERS[ctx.interaction.guild.id][ctx.interaction.user.id]['Credits']-=wealth
        await ctx.respond(f'{ctx.interaction.user.name} gave {user.name} {wealth} credits')

@credit.command()
async def remove(ctx, user:discord.Option(discord.Member, 'who\'s money to take'), wealth:discord.Option(int,"how much money to give", min_value=0)):
    if ctx.interaction.user.get_role(PLAYERS[ctx.interaction.guild.id]['GM'])!= None:
        PLAYERS[user.guild.id][user.id]['Credits']-=wealth
        await ctx.respond(f'{user.name} now has {PLAYERS[user.guild.id][user.id]["Credits"]} credits')
    else:
        await ctx.respond('You do not have permission to rob people.', ephemeral=True)

@credit.command("view player's money")
async def view(ctx, user:discord.Option(discord.Member, 'who\'s money to view'), displayed:discord.Option(bool,"display command result to others")=True):
    await ctx.respond(f'{user.name} has {PLAYERS[user.guild.id][user.id]["Credits"]} Credits', ephemeral= not displayed)


client.run(getenv('TOKEN'))