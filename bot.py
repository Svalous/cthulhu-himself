import discord
import logging
import random
import sys
import os
from discord.ext import commands
from discord.http import HTTPException
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exc
from dotenv import load_dotenv
from requests import get

# Logging boilerplate
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Globals
DEFAULT_VOLUME = 15

# Load dotenv
load_dotenv()

# Load config
config = os.environ['TOKEN']
db_string = os.environ['DATABASE_URL']

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
@commands.has_role("blessed")
async def ip(ctx):
    """
    Send the user the IP of my dedicated server, if and only if they are a member of the blessed discord group.
    """
    author = ctx.message.author
    # Call to ipify API
    ip = get('https://api.ipify.org').text
    await author.send(ip)
    
@ip.error
async def ip_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send("You do not have the blessed role. Cthulhu ignores you.")
    else:
        logging.warning('ip_error(): ' + error.text)

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
    embed.add_field(name='.cooks [max]', value='Sets the maximum number of users allowed in your current voice channel.  A max of 0 or not specified will remove the maximum.', inline=False)
    embed.add_field(name='.ip', value='Ask Cthulhu for the server IP. You know the one.', inline=False)
    
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
        judgement_text = "Cthulhu has judged, and found you vacant."
    elif judgement_value == 2:
        judgement_text = "Cthulhu has judged, and found you limited."
    elif judgement_value == 3:
        judgement_text = "Cthulhu has judged, and found you wanting."
    elif judgement_value == 8:
        judgement_text = "Cthulhu has judged, and found you amusing."
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
    Insanity can range from 1 to 100.
    """
    if user.id == ctx.message.author.id:
        await ctx.send('You cannot confound yourself, mortal.')
        return
    if insanity < 1 or insanity > 100:
        await ctx.send('Insanity must be between 1 and 100 per confound.')
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

@client.command(pass_context=True)
async def cooks(ctx, max : int=None):
    """
    Sets the max # of users allowed in their voice channel.
    Can be 0-99.
    0 or no input will turn off the max.
    """
    max = max if max is not None else 0
    channel = ctx.author.voice.channel
    await channel.edit(user_limit=max)
    return

@cooks.error
async def cooks_error(ctx, error):
    if isinstance(error, commands.errors.CommandInvokeError):
        if type(error.original) == AttributeError:
            await ctx.send("You must be in a voice channel to use the cooks command.")
        elif type(error.original) == HTTPException:
            await ctx.send("The max argument must be an integer between 0 and 99.")
    elif isinstance(error, commands.errors.BadArgument):
        await ctx.send("The max argument must be an integer if provided.")
    else:
        logging.warning('cooks_error(): ' + error.text)

# TODO:  Create devtools suite of commands, like the below
# @client.command()
# async def whois(ctx, user : discord.User):
#     await ctx.send(user.id)

client.run(config)
