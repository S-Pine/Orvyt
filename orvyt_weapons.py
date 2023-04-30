import discord
from discord.ext.commands import Cog
import random
import string
from ast import literal_eval
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import AsIs
from orvyt_misc import conn,WEAPON_TABLES,GM,TRAITS

class WeaponCmnds(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_member=None

    weaponCmnds=discord.SlashCommandGroup(name="weapon",description="edit, view and create weapons")

    @weaponCmnds.command(description="generate a weapon")
    async def compose(self, ctx, type:discord.Option(str, choices=['Fray','Standard','Strife','Long']),grade:discord.Option(str,choices=['F','D','C','B','A','U']), owner:discord.Option(discord.Member,"Whom to give the weapon")=None):
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
            if owner==None:
                await ctx.respond('Weapon Created', embed=weapon_embed(weapon))
            else:
                query=sql.SQL('SELECT index FROM Weapons.{0} WHERE name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
                cursor.execute(query,(weapon["name"],))
                weaponSerial=cursor.fetchone()[0]
                query=sql.SQL('UPDATE {0} SET Items=array_append(Items,%s) WHERE MemberID=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
                cursor.execute(query,("W"+str(weaponSerial),owner.id))
                conn.commit()
                await ctx.respond(f'Weapon created and given to {owner.name}', embed=weapon_embed(weapon))
        else:
            await ctx.respond('You do not have permission to do that', ephemeral=True)

    @weaponCmnds.command( description='rename a weapon')
    async def rename(self, ctx, weapon:discord.Option(str), newname:discord.Option(str)):
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
    async def display(self, ctx, weapon:discord.Option(str), display:discord.Option(bool)=True):
        cursor=conn.cursor(cursor_factory=RealDictCursor)
        query=sql.SQL('SELECT * FROM Weapons.{0} WHERE Name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query,(weapon,))
        response=cursor.fetchone()
        if response:
            await ctx.respond('here it is!',embed=weapon_embed(response), ephemeral=(not display))
        else:
            await ctx.respond('weapon does not exist', ephemeral=(not display))

    @weaponCmnds.command(description='rework a weapon')
    async def rework(self, ctx, weapon:discord.Option(str)):
        cursor=conn.cursor(cursor_factory=RealDictCursor)
        query=sql.SQL('SELECT * FROM Weapons.{0} WHERE Name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query,(weapon,))
        try:
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
        except:
            ctx.respond('weapon not found', ephemeral=True)

    @weaponCmnds.command()
    async def give(self, ctx, user:discord.Option(discord.Member,'whom to give'),weapon:discord.Option(str, 'name of weapon to give')):
        cursor=conn.cursor()
        query=sql.SQL('SELECT Index FROM Weapons.{} WHERE name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
        cursor.execute(query,(weapon,))
        try:
            weaponSerial=cursor.fetchone()[0]
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
        except:
            await ctx.respond('weapon not found', ephemeral=True)

    @weaponCmnds.command(description='for debugging')
    async def delete(self, ctx, weapon:discord.Option(str)):
        if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
            cursor=conn.cursor()
            query=sql.SQL('SELECT index FROM Weapons.{} WHERE name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
            cursor.execute(query,(weapon,))
            try:
                weaponIndex=cursor.fetchone()[0]
                query=sql.SQL('DELETE FROM Weapons.{} WHERE name=%s').format(sql.Identifier(str(ctx.interaction.guild.id)))
                cursor.execute(query,(weapon,))
                query=sql.SQL('UPDATE {} SET Items=array_remove(Items,%s)').format(sql.Identifier(str(ctx.interaction.guild.id)))
                cursor.execute(query,("W"+str(weaponIndex),))
                conn.commit()
                await ctx.respond(f'{weapon} has been removed')
            except:
                await ctx.respond(f'No weapon called {weapon} found', ephermeral=True)
        else:
            await ctx.respond('You do not have permission to do that.', ephemeral=True)

    @weaponCmnds.command(description="custom Weapon")
    async def design(self, ctx, name:discord.Option(str),type:discord.Option(str, choices=['Fray','Standard','Strife','Long']),grade:discord.Option(str,choices=['F','D','C','B','A','U']),range:discord.Option(int),damage:discord.Option(int),chargetime:discord.Option(int),blastradius:discord.Option(int),trait:discord.Option(str)="none", traitchoice1:discord.Option(int)=None,traitchoice2:discord.Option(int)=None):
        if ctx.interaction.user.get_role(GM[ctx.interaction.guild.id])!= None:
            response=f"{name} created!"
            cursor=conn.cursor()
            query=sql.SQL("SELECT Name FROM Weapons.{0}").format(sql.Identifier(str(ctx.interaction.guild.id)))
            cursor.execute(query)
            takenNames=cursor.fetchall()
            if ((name,) in takenNames):
                await ctx.respond('that name is taken.', ephemeral=True)
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
                    await ctx.respond(response,embed=weapon_embed(weapon))
                except: 
                    await ctx.respond('something went wrong! check if you put in the right trait parameters, or if you spelled the trait right, (capitalisation doesn\'t matter).', ephemeral=True)

def trait_selector():
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


gradeRGB={
    'A':16171112,
    'B':9320183,
    'C':10157135,
    'D':8902392,
    'F':6513507,
    'U':16732751
}


