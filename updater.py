import sys
import os
import logging
import shutil
from file_exceptions import *
from BotMain.config_loader import setYaml

logger = logging.getLogger('logs')
logger.setLevel(logging.INFO)

def updateYaml():
    discordbottoken = input('Enter the token for the discord bot to use: ')
    discordchannel = input('Enter the id for the default cs channel for the bot: ')
    discordguildid = input('Enter the id of the server/guild that the bot will be in: ')
    discordownerid = input('Enter the discord id of the bot owner for admin commands: ')
    discordadminrole = input('Enter the role id for the deadlock server admin role: ')
    setYaml(discordbottoken, discordchannel, discordadminrole, discordguildid, discordownerid)

def updateFiles(dst):
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(ROOT_DIR, dst)
    botPath = os.path.join(dst, 'BotMain')
    if not os.path.exists(botPath):
        os.makedirs(botPath)
    shutil.copy(os.path.abspath('BotMain/bot_main.py'), os.path.join(botPath, 'bot_main.py'))
    shutil.copy('BotMain/heroes.py', os.path.join(botPath, 'heroes.py'))
    shutil.copy('BotMain/match.py', os.path.join(botPath, 'match.py'))
    shutil.copy('BotMain/team.py', os.path.join(botPath, 'team.py'))
    shutil.copy('BotMain/twelveman.py', os.path.join(botPath, 'twelveman.py'))
    shutil.copy('BotMain/config_loader.py', os.path.join(botPath, 'config_loader.py'))
    shutil.copy('requirements.txt', os.path.join(dst, 'requirements.txt'))
    shutil.copy('docker-compose.yml', os.path.join(dst, 'docker-compose.yml'))
    shutil.copy('Dockerfile', os.path.join(dst, 'Dockerfile'))
    if not os.path.exists(dst + '/config.yaml'):
        updateYaml()
        shutil.copy('config.yaml', os.path.join(dst, 'config.yaml'))
    if not os.path.exists(dst + '/bot-main/accounts.yaml'):
        shutil.copy('BotMain/accounts.yaml', os.path.join(dst, 'accounts.yaml'))

def main():
    logger.info('Updating files to version in this folder')

    # Error checker
    directoryFlagIsPresent = False
    directoryIsPresent = False
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-dir':
            directoryFlagIsPresent = True
            if len(sys.argv) > i + 1 and sys.argv[i+1][0] != '-':
                directoryIsPresent = True
    if not directoryFlagIsPresent:
        raise MissingDirArg()
    if not directoryIsPresent:
        raise NoPathException()
    
    # Run updater
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-dir' and len(sys.argv) >= i+1:
            dst = sys.argv[i+1]
    if dst[:0] == '/' or dst[:0] == '\\':
        dst = dst[:-1]
    updateFiles(dst)
    logger.info('Update complete')

if __name__ == "__main__":
    main()