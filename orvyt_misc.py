import random
import json
from psycopg2 import connect
from dotenv import load_dotenv
from os import environ
load_dotenv()

WEAPON_TABLES=json.load(open('WeaponTables.json'))
ORVYT_TOKEN=environ["ORVYT_TOKEN"]
GM={}
conn=connect(environ['DATABASE_INFO'])

TRAITS=json.load(open("OrvytTraits.json"))


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