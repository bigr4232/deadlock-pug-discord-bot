import discord
from discord import app_commands
import config_loader
import logging
import sys
import datetime
from twelveman import fillTwelveMan
import random


# Globals
__version__ = 0.0
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
managers = {}
tree = app_commands.CommandTree(client)
config = config_loader.loadYaml()
debugMode = False
twelveManPlayers = dict()
twelveManMessage = dict()
simTwelveMan = False
sortedList = dict()
twelveManMessage = dict()

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
    if arg == '-d':
        logger.setLevel(logging.DEBUG)
        debugMode = True

# Class for 10 mans buttons
class TwelveMansButton(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
    @discord.ui.button(label='Join',style=discord.ButtonStyle.green)
    async def green_button(self, ctx:discord.Interaction, button:discord.ui.Button):
        logger.debug(f'green button pressed by {ctx.user.id}')
        checkDup = ctx.user not in twelveManPlayers[ctx.guild.id]
        if simTwelveMan:
            twelveManPlayers[ctx.guild.id] = await fillTwelveMan(client, config)
        if checkDup:
            twelveManPlayers[ctx.guild.id].add(ctx.user)
        await ctx.response.edit_message(content = await tenManStatus(ctx), view=self)
        if len(twelveManPlayers[ctx.guild.id]) == 10 and checkDup:
            logger.debug('Starting 10 mans')
            if ctx.guild.id in sortedList:
                sortedList[ctx.guild.id].clear()
            sortedList[ctx.guild.id] = await randomizeTeams(twelveManPlayers[ctx.guild.id])
            await ctx.channel.send(f'Team 1: {sortedList[ctx.guild.id][0].mention}, {sortedList[ctx.guild.id][1].mention}, {sortedList[ctx.guild.id][2].mention}, {sortedList[ctx.guild.id][3].mention}, {sortedList[ctx.guild.id][4].mention}, {sortedList[ctx.guild.id][5].mention} \nTeam 2: {sortedList[ctx.guild.id][6].mention}, {sortedList[ctx.guild.id][7].mention}, {sortedList[ctx.guild.id][8].mention}, {sortedList[ctx.guild.id][9].mention}, {sortedList[ctx.guild.id][10].mention}, {sortedList[ctx.guild.id][11].mention}', delete_after=600)
            await twelveManMessage[ctx.guild.id].delete()
            twelveManMessage.pop(ctx.guild.id)
    @discord.ui.button(label='leave', style=discord.ButtonStyle.red)
    async def red_button(self, ctx:discord.Interaction, button:discord.ui.Button):
        logger.debug(f'red button pressed by {ctx.user.id}')
        if ctx.user in twelveManPlayers[ctx.guild.id]:
            twelveManPlayers[ctx.guild.id].remove(ctx.user)
        await ctx.response.edit_message(content = await tenManStatus(ctx), view=self)

# Randomize teams for 10 mans
async def randomizeTeams(unsortedSet):
    logger.debug('Randomizing teams')
    sortList = list()
    for discordUser in unsortedSet:
        sortList.append(discordUser)
    for i in range(len(sortList)):
        swapidx = random.randint(0,9)
        tempDiscordUser = sortList[swapidx]
        sortList[swapidx] = sortList[i]
        sortList[i] = tempDiscordUser
    return sortList

# Make message to send for 10 man status
async def tenManStatus(ctx):
    message = f'{len(twelveManPlayers[ctx.guild.id])}/12 players joined:'
    for player in twelveManPlayers[ctx.guild.id]:
        if player.display_name is not None:
            message += f"\n{player.display_name}"
        else:
            message += f"\n{player.name}"
    return message

# Twelve mans discord command
@tree.command(name='deadlock-12man', description='start 12 mans', guild=discord.Object(id=config['discordGuildID']))
@app_commands.choices(option=[app_commands.Choice(name='start', value='start'),
                    app_commands.Choice(name='cancel', value='cancel')])
async def tenMans(ctx: discord.Interaction, option:app_commands.Choice[str]):
    logger.info(f'{ctx.user.name} called deadlock-12man command with option {option.name}')
    if option.name == 'start':
        if ctx.guild.id not in twelveManPlayers or twelveManPlayers[ctx.guild.id] == 0:
            await ctx.response.send_message('Starting 12 mans', delete_after=200)
            message = await ctx.channel.send('0/12 players joined', view=TwelveMansButton())
            twelveManMessage.update({ctx.guild.id : message})
            twelveManPlayers[ctx.guild.id] = set()
        else:
            await ctx.response.send_message('12 mans already started. Please cancel before starting again', delete_after=30)
    elif option.name == 'cancel':
        if ctx.guild.id in twelveManMessage:
            await ctx.response.send_message('Ending 12 mans', delete_after=30)
            await twelveManMessage[ctx.guild.id].delete()
            twelveManMessage.pop(ctx.guild.id)
        else:
            await ctx.response.send_message('No 12 mans running', delete_after=30)


# Initialization
@client.event
async def on_ready():
    logger.info(f'Starting bot v{__version__}')
    if debugMode:
        await tree.sync(guild=discord.Object(id=config['discordGuildID']))
        logger.debug("Starting in debug mode")
    else:
        await tree.sync()
    logger.debug("commands synced")

client.run(config['discordBotToken'])