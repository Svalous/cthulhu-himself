import discord
import logging
import json
import random
import sys
import os
import re
from discord.ext import commands

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
        config = json.load(json_data_file)['Token']
# Load config (prod)
if len(sys.argv) > 1 and str(sys.argv[1]) == 'PROD':
    config = os.environ['TOKEN']

# Instantiate bot
client = commands.Bot(command_prefix = '.')
client.remove_command('help')

# Event definitions
@client.event
async def on_ready():
    print('Cthulhu Himself has arrived.')

@client.event
async def on_message(message):
    """
    Provides auto-volume functionality that botify lacks.
    """
    match = re.search('^\s*\$play[\s$]+.*', message.content)
    if match:
        await message.channel.send('$volume ' + str(DEFAULT_VOLUME))
    await client.process_commands(message)

# Command definitions
@client.command(pass_context=True)
async def help(ctx):
    """
    Send help message to user.
    """
    author = ctx.message.author

    embed = discord.Embed(
        colour = discord.Colour.orange()
    )

    embed.set_author(name='Help')
    embed.add_field(name='.roll [a] [b]', value='Returns a random integer between a and b.', inline=False)
    embed.add_field(name='.judge', value='Be judged by Cthulhu.', inline=False)
    
    await author.send(embed=embed)

@client.command()
async def roll(ctx, a, b):
    """
    Returns a random integer between a and b.
    """
    await ctx.send(random.randint(int(a),int(b)))

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

client.run(config)
