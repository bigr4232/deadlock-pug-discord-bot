import discord
from discord import app_commands
import config_loader
import logging
import sys
import datetime


# Globals
__version__ = 0.0
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
managers = {}
tree = app_commands.CommandTree(client)
config = config_loader.loadYaml()

# Logging
logger = logging.getLogger('logs')
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# get args
for arg in sys.argv:
    if arg == '-log':
        logger.setLevel(logging.DEBUG)
        now = datetime.datetime.now()
        pre = now.strftime("%Y-%m-%d_%H:%M:%S")
        fh = logging.FileHandler(f'bot-{pre}-logs.log')
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)


# Initialization
@client.event
async def on_ready():
    logger.info(f'Starting bot v{__version__}')
    await tree.sync()
    logger.debug("commands synced")

client.run(config['discordBotToken'])