import discord
import logging
import json
import random
import sys
import os
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exc

# Logging boilerplate
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Globals
DEFAULT_VOLUME = 15

# Load config (dev)
if len(sys.argv) == 1:
    with open('config.json') as json_data_file:
        load = json.load(json_data_file)
        config = load['Token']
        db_string = load['DATABASE_URL']
# Load config (prod)
elif len(sys.argv) > 1 and str(sys.argv[1]) == 'PROD':
    config = os.environ['TOKEN']
    # Bit of a hack below, Heroku database_url is unsuitable for sqlalchemy and cannot be altered afaik
    uri = os.environ['DATABASE_URL']
    db_string= uri[:8]+'ql' + uri[8:]
    db_string = os.environ['DATABASE_URL']
# Config not understood, exit
else:
    print('Configuration not understood.')
    sys.exit(1)

# Instantiate database connection
try:
    db = create_engine(db_string)
except exc.ArgumentException:
    print('Database string incorrect or not supplied.')
    sys.exit(1)

# Table definitions
base = declarative_base()
class User(base):
    __tablename__ = 'users'

    id       = Column(Integer, autoincrement=True, primary_key=True)
    uid      = Column(String, nullable = False, unique=True)
    username = Column(String, nullable = False)
    insanity = Column(Integer, default = 0)

Session = sessionmaker(db)
session = Session()

# NOTE:  The below is required to make changes to the table after the first metadata creation.  This WILL drop the table.
#base.metadata.drop_all(db)
base.metadata.create_all(db)

# Instantiate bot
client = commands.Bot(command_prefix = '.')
client.remove_command('help')

# Event definitions
@client.event
async def on_ready():
    print('Cthulhu Himself has arrived.')

# Emergency command, if the bot gets stuck in the VC somehow
@client.command()
async def leave(ctx):
    try:
        await ctx.voice_client.disconnect()
        ctx.voice_client.cleanup()
    except AttributeError:
        print('Bot is not in a voice channel, ignoring leave command.')
        pass

# Command definitions
@client.command(pass_context=True)
async def help(ctx):
    """
    Send help message to user.
    """
    author = ctx.message.author

    embed = discord.Embed(
        colour = discord.Colour.dark_green()
    )

    embed.set_author(name='Help')
    embed.add_field(name='.roll [start] [end]', value='Returns a random integer between start and end.', inline=False)
    embed.add_field(name='.judge', value='Be judged by Cthulhu.', inline=False)
    embed.add_field(name='.confound @[target] [insanity]', value='Confound a targeted user and increase their insanity!  Insanity is an integer between 1 and 100.', inline=False)
    
    await author.send(embed=embed)

@client.command()
async def roll(ctx, start, end):
    """
    Returns a random integer between a and b.
    """
    await ctx.send(random.randint(int(start),int(end)))

@client.command()
async def judge(ctx):
    """
    Judges the user.
    """
    judgement_value = random.randint(1,10)
    judgement_text = None
    if judgement_value == 1:
        judgement_text = "Cthulhu has judged, and found you wanting."
    elif judgement_value == 2:
        judgement_text = "Cthulhu has judged, and found you limited."
    elif judgement_value == 9:
        judgement_text = "Cthulhu has judged, and found you exceptional."
    elif judgement_value == 10:
        judgement_text = "Cthulhu has judged, and found you unequaled."
    else:
        judgement_text = "Cthulhu has judged, and is indifferent."
    await ctx.send(judgement_text)

# TODO:  Add error checking...prevent insanity overflow and underflow.
@client.command()
async def confound(ctx, user : discord.User, insanity : int):
    """
    Adds / subtracts to a user's insanity.
    Insanity can range from -100 to 100.
    """
    if insanity < 1 or insanity > 100:
        await ctx.send('Insanity must be between 1 and 100 per confound.')
        return
    if user.id == ctx.message.author.id:
        await ctx.send('You cannot confound yourself, mortal.')
        return
    sql_user = session.query(User).filter_by(uid = str(user.id)).first()
    if not sql_user:
        sql_user = User(uid=user.id, username=user.name, insanity=insanity)
        session.add(sql_user)
    else:
        sql_user.insanity += insanity
    await ctx.send('Adding ' + str(insanity) + ' insanity to ' + user.name + '...')
    await ctx.send(user.name + ' has ' + str(sql_user.insanity) + ' total insanity.')
    session.commit()

# TODO:  Create devtools suite of commands, like the below
#@client.command()
#async def whois(ctx, user : discord.User):
#    await ctx.send(user.id)

client.run(config)
