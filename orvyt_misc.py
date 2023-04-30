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

TRAITS=json.load(open("WeaponTraits.json"))