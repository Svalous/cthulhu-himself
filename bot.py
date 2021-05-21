import discord
import logging
import json
import random
import sys
import os
from discord.ext import commands

# Logging boilerplate
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Load config (dev)
if len(sys.argv) == 1:
    with open('config.json') as json_data_file:
        config = json.load(json_data_file)['Token']
# Load config (prod)
if len(sys.argv) > 1 and str(sys.argv[1]) == 'PROD':
    config = os.environ['TOKEN']


# Client instantiation and prefex definition
client = commands.Bot(command_prefix = '.')
client.remove_command('help')

# Event definitions
@client.event
async def on_ready():
    print('EnderBot has joined the party.')

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
    embed.add_field(name='.roll', value='Returns a random integer between a and b.', inline=False)
    
    await author.send(embed=embed)

@client.command()
async def roll(ctx, a, b):
    """
    Returns a random integer between a and b.
    """
    await ctx.send(random.randint(int(a),int(b)))

client.run(config)
