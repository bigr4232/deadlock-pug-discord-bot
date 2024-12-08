import discord
from discord import app_commands
import config_loader
import logging
import sys
import datetime
from twelveman import fillTwelveMan
import random
from match import match


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
serverMatch = dict()
simTwelveMan = False

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
    if arg == '-sim12man':
        simTwelveMan = True

# Start team sort
async def startTeamSort(ctx):
    logger.debug('Starting 12 mans')
    await randomizeTeams(twelveManPlayers[ctx.guild.id], ctx)
    msg = await genTeamMessage(ctx)
    await ctx.channel.send(msg, delete_after=200, view=ConfirmOrDenyTeamButtons())

# Generate output message for teams
async def genTeamMessage(ctx):
    message = 'Team 1: '
    for player in serverMatch[ctx.guild.id].team1.players:
        message += player.mention + ', '
    message = message[:-2]
    message += '\nTeam 2: '
    for player in serverMatch[ctx.guild.id].team2.players:
        message += player.mention + ', '
    message = message[:-2]
    return message

# Generate output message for captains
async def genCaptainMessage(ctx):
    message = 'Captain Team 1: '
    message += serverMatch[ctx.guild.id].team1.captain.mention + '\nCaptain Team 2: '
    message += serverMatch[ctx.guild.id].team2.captain.mention
    return message

# Pick two team captains
async def pickTeamCaptains(ctx):
    captain = serverMatch[ctx.guild.id].team1.captain
    while serverMatch[ctx.guild.id].team1.captain == captain:
        capidx = random.randint(0,5)
        serverMatch[ctx.guild.id].team1.captain = serverMatch[ctx.guild.id].team1.players[capidx]
    captain = serverMatch[ctx.guild.id].team2.captain
    while serverMatch[ctx.guild.id].team2.captain == captain:
        capidx = random.randint(0,5)
        serverMatch[ctx.guild.id].team2.captain = serverMatch[ctx.guild.id].team2.players[capidx]

# Start team captain picks
async def startCaptainPick(ctx):
    logger.debug('Starting captain pick')
    await pickTeamCaptains(ctx)
    msg = await genCaptainMessage(ctx)
    await ctx.channel.send(msg, delete_after=200, view=ConfirmOrDenyCaptainButtons())

# Final output and cleanup
async def displayTeamInfo(ctx):
    logger.debug('Displaying team info')
    output = 'Team Info:\n\n'
    output += 'Team 1 members:\n'
    for player in serverMatch[ctx.guild.id].team1.players:
        output += player.mention + '\n'
    output += '\nTeam 1 heroes:\n'
    for hero in serverMatch[ctx.guild.id].team1.heroes:
        output += hero + '\n'
    output += '\n\nTeam 2 members:\n'
    for player in serverMatch[ctx.guild.id].team2.players:
        output += player.mention + '\n'
    output += '\nTeam 2 heroes:\n'
    for hero in serverMatch[ctx.guild.id].team2.heroes:
        output += hero + '\n'
    await ctx.response.edit_message(content=output)
    del serverMatch[ctx.guild.id]

# Selection menu for cs servers
class teamOneBanSelect(discord.ui.Select):
    def __init__(self, ctx: discord.Interaction):
        options = [discord.SelectOption(label=hero, value=hero) for hero in sorted(serverMatch[ctx.guild.id].unselectedHeroes)]
        super().__init__(placeholder='Heroes', max_values=1, min_values=1, options=options)
    async def callback(self, ctx: discord.Interaction):
        if ctx.user.id == serverMatch[ctx.guild.id].team1.captain.id:
            logger.debug(f'Team 1 banned hero {self.values[0]}')
            serverMatch[ctx.guild.id].pickBanCount += 1
            serverMatch[ctx.guild.id].unselectedHeroes.remove(self.values[0])
            await ctx.response.edit_message(content=f'Team 1 banned hero {self.values[0]}\n\nTeam 2 select ban {serverMatch[ctx.guild.id].team2.captain.mention}', view=TeamTwoBanView(ctx=ctx))     
        else:
            await ctx.response.edit_message(content=f'Picks must be made by captain\n\nTeam 1 select ban {serverMatch[ctx.guild.id].team1.captain.mention}', view=TeamOneBanView(ctx=ctx))

class TeamOneBanView(discord.ui.View):
    def __init__(self, *, timeout = 200, ctx:discord.Interaction):
        super().__init__(timeout=timeout)
        self.add_item(teamOneBanSelect(ctx=ctx))

# Selection for Team Two ban
class teamTwoBanSelect(discord.ui.Select):
    def __init__(self, ctx: discord.Interaction):
        options = [discord.SelectOption(label=hero, value=hero) for hero in sorted(serverMatch[ctx.guild.id].unselectedHeroes)]
        super().__init__(placeholder='Heroes', max_values=1, min_values=1, options=options)
    async def callback(self, ctx: discord.Interaction):
        if ctx.user.id == serverMatch[ctx.guild.id].team2.captain.id:
            logger.debug(f'Team 2 banned hero {self.values[0]}')
            serverMatch[ctx.guild.id].pickBanCount += 1
            serverMatch[ctx.guild.id].unselectedHeroes.remove(self.values[0])
            await ctx.response.edit_message(content=f'Team 2 banned hero {self.values[0]}\n\nTeam 2 pick hero {serverMatch[ctx.guild.id].team2.captain.mention}', view=TeamTwoPickView(ctx=ctx))     
        else:
            await ctx.response.edit_message(content=f'Picks must be made by captain\n\nTeam 2 select ban {serverMatch[ctx.guild.id].team2.captain.mention}', view=TeamTwoBanView(ctx=ctx))

class TeamTwoBanView(discord.ui.View):
    def __init__(self, *, timeout = 200, ctx:discord.Interaction):
        super().__init__(timeout=timeout)
        self.add_item(teamTwoBanSelect(ctx=ctx))

# Selection menu for cs servers
class teamOnePickSelect(discord.ui.Select):
    def __init__(self, ctx: discord.Interaction):
        options = [discord.SelectOption(label=hero, value=hero) for hero in sorted(serverMatch[ctx.guild.id].unselectedHeroes)]
        super().__init__(placeholder='Heroes', max_values=1, min_values=1, options=options)
    async def callback(self, ctx: discord.Interaction):
        if ctx.user.id == serverMatch[ctx.guild.id].team1.captain.id:
            logger.debug(f'Team 1 picked hero {self.values[0]}')
            serverMatch[ctx.guild.id].pickBanCount += 1
            serverMatch[ctx.guild.id].unselectedHeroes.remove(self.values[0])
            serverMatch[ctx.guild.id].team1.heroes.append(self.values[0])
            if serverMatch[ctx.guild.id].pickBanCount == 14:
                await displayTeamInfo(ctx)
            elif serverMatch[ctx.guild.id].pickBanCount % 2 == 0:
                await ctx.response.edit_message(content=f'Team 1 selected hero {self.values[0]}\n\nTeam 1 select hero {serverMatch[ctx.guild.id].team1.captain.mention}', view=TeamOnePickView(ctx=ctx))
            else:
                await ctx.response.edit_message(content=f'Team 1 selected hero {self.values[0]}\n\nTeam 2 select hero {serverMatch[ctx.guild.id].team2.captain.mention}', view=TeamTwoPickView(ctx=ctx))
        else:
            await ctx.response.edit_message(content=f'Picks must be made by captain\n\nTeam 1 select hero {serverMatch[ctx.guild.id].team1.captain.mention}', view=TeamOnePickView(ctx=ctx))

class TeamOnePickView(discord.ui.View):
    def __init__(self, *, timeout = 200, ctx:discord.Interaction):
        super().__init__(timeout=timeout)
        self.add_item(teamOnePickSelect(ctx=ctx))

# Selection for Team Two ban
class teamTwoPickSelect(discord.ui.Select):
    def __init__(self, ctx: discord.Interaction):
        options = [discord.SelectOption(label=hero, value=hero) for hero in sorted(serverMatch[ctx.guild.id].unselectedHeroes)]
        super().__init__(placeholder='Heroes', max_values=1, min_values=1, options=options)
    async def callback(self, ctx: discord.Interaction):
        if ctx.user.id == serverMatch[ctx.guild.id].team2.captain.id:
            logger.debug(f'Team 2 picked hero {self.values[0]}')
            serverMatch[ctx.guild.id].pickBanCount += 1
            serverMatch[ctx.guild.id].unselectedHeroes.remove(self.values[0])
            serverMatch[ctx.guild.id].team2.heroes.append(self.values[0])
            if serverMatch[ctx.guild.id].pickBanCount == 14:
                await displayTeamInfo(ctx)
            elif serverMatch[ctx.guild.id].pickBanCount % 2 == 0:
                await ctx.response.edit_message(content=f'Team 2 picked hero {self.values[0]}\n\nTeam 2 pick hero {serverMatch[ctx.guild.id].team2.captain.mention}', view=TeamTwoPickView(ctx=ctx))
            else:
                await ctx.response.edit_message(content=f'Team 2 picked hero {self.values[0]}\n\nTeam 1 pick hero {serverMatch[ctx.guild.id].team1.captain.mention}', view=TeamOnePickView(ctx=ctx))
        else:
            await ctx.response.edit_message(content=f'Picks must be made by captain\n\nTeam 2 select hero {serverMatch[ctx.guild.id].team2.captain.mention}', view=TeamTwoPickView(ctx=ctx))

class TeamTwoPickView(discord.ui.View):
    def __init__(self, *, timeout = 200, ctx:discord.Interaction):
        super().__init__(timeout=timeout)
        self.add_item(teamTwoPickSelect(ctx=ctx))

# Class for confirm/deny captain buttons
class ConfirmOrDenyCaptainButtons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
    @discord.ui.button(label='Confirm Captains',style=discord.ButtonStyle.green)
    async def green_button(self, ctx:discord.Interaction, button:discord.ui.Button):
        if serverMatch[ctx.guild.id].admin == ctx.user.id:
            logger.debug('Captains confirmed')
            await ctx.response.send_message(f'Captains confirmed. Starting Bans.\n\nTeam 1 select ban: {serverMatch[ctx.guild.id].team1.captain.mention}', view=TeamOneBanView(ctx=ctx))
        else:
            logger.debug(f'Confirm called by {ctx.user.id} without permissions.')
            await ctx.response.send_message('Can only be done by user who started 12 mans.', delete_after=10)
    @discord.ui.button(label='Re-Draw Captains', style=discord.ButtonStyle.red)
    async def red_button(self, ctx:discord.Interaction, button:discord.ui.Button):
        if serverMatch[ctx.guild.id].admin == ctx.user.id:
            logger.debug('Re-picking captains')
            await ctx.response.send_message('Re-picking captains', delete_after=30)
            await startCaptainPick(ctx)
        else:
            logger.debug(f'Re-Scramble called by {ctx.user.id} without permissions.')
            await ctx.response.send_message('Can only be done by user who started 12 mans.', delete_after=10)

# Class for confirm/deny team buttons
class ConfirmOrDenyTeamButtons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
    @discord.ui.button(label='Confirm Teams',style=discord.ButtonStyle.green)
    async def green_button(self, ctx:discord.Interaction, button:discord.ui.Button):
        if serverMatch[ctx.guild.id].admin == ctx.user.id:
            logger.debug('Teams confirmed')
            del twelveManPlayers[ctx.guild.id]
            logger.debug('Picking Captains')
            await ctx.response.send_message('Picking captains', delete_after=200)
            await startCaptainPick(ctx)
        else:
            logger.debug(f'Confirm called by {ctx.user.id} without permissions.')
            await ctx.response.send_message('Can only be done by user who started 12 mans.', delete_after=10)
    @discord.ui.button(label='Re-Scramble', style=discord.ButtonStyle.red)
    async def red_button(self, ctx:discord.Interaction, button:discord.ui.Button):
        if serverMatch[ctx.guild.id].admin == ctx.user.id:
            logger.debug('Re-scrambling teams')
            serverMatch[ctx.guild.id].clearTeams()
            await ctx.response.send_message('Re-Scrambling teams', delete_after=30)
            await startTeamSort(ctx)
        else:
            logger.debug(f'Re-Scramble called by {ctx.user.id} without permissions.')
            await ctx.response.send_message('Can only be done by user who started 12 mans.', delete_after=10)

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
        await ctx.response.edit_message(content = await twelveManStatus(ctx), view=self)
        if len(twelveManPlayers[ctx.guild.id]) == 12 and checkDup:
            await twelveManMessage[ctx.guild.id].delete()
            twelveManMessage.pop(ctx.guild.id)
            await startTeamSort(ctx)
    @discord.ui.button(label='leave', style=discord.ButtonStyle.red)
    async def red_button(self, ctx:discord.Interaction, button:discord.ui.Button):
        logger.debug(f'red button pressed by {ctx.user.id}')
        if ctx.user in twelveManPlayers[ctx.guild.id]:
            twelveManPlayers[ctx.guild.id].remove(ctx.user)
        await ctx.response.edit_message(content = await twelveManStatus(ctx), view=self)

# Randomize teams for 10 mans
async def randomizeTeams(unsortedSet, ctx):
    logger.debug('Randomizing teams')
    sortList = list()
    for discordUser in unsortedSet:
        sortList.append(discordUser)
    for i in range(len(sortList)):
        swapidx = random.randint(0,11)
        tempDiscordUser = sortList[swapidx]
        sortList[swapidx] = sortList[i]
        sortList[i] = tempDiscordUser
    idx = 0
    for i in sortList:
        if idx < 6:
            serverMatch[ctx.guild.id].team1.players.append(i)
        else:
            serverMatch[ctx.guild.id].team2.players.append(i)
        idx+=1

# Make message to send for 10 man status
async def twelveManStatus(ctx):
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
async def twelveMans(ctx: discord.Interaction, option:app_commands.Choice[str]):
    logger.info(f'{ctx.user.name} called deadlock-12man command with option {option.name}')
    if option.name == 'start':
        if ctx.guild.id not in serverMatch or serverMatch[ctx.guild.id] == 0:
            await ctx.response.send_message('Starting 12 mans', delete_after=200)
            message = await ctx.channel.send('0/12 players joined', view=TwelveMansButton())
            twelveManMessage.update({ctx.guild.id : message})
            twelveManPlayers[ctx.guild.id] = set()
            serverMatch[ctx.guild.id] = match()
            serverMatch[ctx.guild.id].admin = ctx.user.id
        else:
            await ctx.response.send_message('12 mans already started. Please cancel before starting again', delete_after=30)
    elif option.name == 'cancel':
        if ctx.guild.id in twelveManMessage:
            await ctx.response.send_message('Ending 12 mans', delete_after=30)
            await twelveManMessage[ctx.guild.id].delete()
            await serverMatch[ctx.guild.id].delete()
            twelveManMessage.pop(ctx.guild.id)
            serverMatch.pop(ctx.guild.id)
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