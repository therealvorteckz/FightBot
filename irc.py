from config import config
import time
import ssl
import logging
import logging.handlers
import asyncio
import time
import functions
import sqlite3
import sys
from colors import *
from importlib import reload

conn = sqlite3.connect('data.db')
c = conn.cursor()

def color(msg: str, foreground: str, background: str='') -> str:
    '''
    Color a string with the specified foreground and background colors.
    
    :param msg: The string to color.
    :param foreground: The foreground color to use.
    :param background: The background color to use.
    '''
    return f'\x03{foreground},{background}{msg}{reset}' if background else f'\x03{foreground}{msg}{reset}'


def ssl_ctx():
	ctx = ssl.create_default_context()
	ctx.check_hostname = False
	ctx.verify_mode = ssl.CERT_NONE
	return ctx
class Bot(object):
    def __init__(self):
        self.nickname = config.irc.nickname
        self.username = config.irc.username
        self.realname = config.irc.realname
        self.channel = config.irc.channel
        self.channelkey = config.irc.channelkey
        self.reader   = None
        self.writer   = None			

    #createtable()
    
    async def action(self, chan: str, msg: str):
        '''
        Send an ACTION to the IRC server.

        :param chan: The channel to send the ACTION to.
        :param msg: The message to send to the channel.
        '''
        await self.sendmsg(chan, f'\x01ACTION {msg}\x01')

    async def raw(self, data: str):
        '''
        Send raw data to the IRC server.
		
        :param data: The raw data to send to the IRC server. (512 bytes max including crlf)
        '''
        self.writer.write(data[:510].encode('utf-8') + b'\r\n')

    async def sendmsg(self, target: str, msg: str):
        '''
        Send a PRIVMSG to the IRC server.
        
        :param target: The target to send the PRIVMSG to. (channel or user)
        :param msg: The message to send to the target.
        '''
        try:
            await self.raw(f'PRIVMSG {target} :{msg}')
        
            time.sleep(config.throttle.msg)
        except:
            await bot.sendmsg(config.irc.channel, "Slow down homie!!")
            
    async def connect(self):
        '''Connect to the IRC server.'''
        while True:
            try:
                options = {
                    'host'       : config.irc.server,
                    'port'       : config.irc.port if config.irc.port else 6697 if config.irc.ssl else 6667,
                    'limit'      : 1024, # Buffer size in bytes (don't change this unless you know what you're doing)
                    'ssl'        : ssl_ctx() if config.irc.ssl else None,
                    'family'     : 2, # 10 = AF_INET6 (IPv6), 2 = AF_INET (IPv4)
                    'local_addr' : None # Can we just leave this as args.vhost?
                }
                self.reader, self.writer = await asyncio.wait_for(asyncio.open_connection(**options), 15) # 15 second timeout
                if config.irc.password:
                    await self.raw('PASS ' + config.irc.password) # Rarely used, but IRCds may require this
                await self.raw(f'USER {self.username} 0 * :{self.realname}') # These lines must be sent upon connection
                await self.raw('NICK ' + self.nickname)                      # They are to identify the bot to the server
                while not self.reader.at_eof():
                    data = await asyncio.wait_for(self.reader.readuntil(b'\r\n'), 300) # 5 minute ping timeout
                    await self.handle(data.decode('utf-8').strip()) # Handle the data received from the IRC server
            except Exception as ex:
                logging.error(f'failed to connect to {config.irc.server} ({str(ex)})')
            finally:
                await asyncio.sleep(30) # Wait 30 seconds before reconnecting

    async def handle(self, data: str):
        '''
        Handle the data received from the IRC server.
        
        :param data: The data received from the IRC server.
        '''
        try:
            logging.info(data)
            args = data.split()
            if data.startswith('ERROR :Closing Link:'):
                    raise Exception('Cannot Connect')
            if args[0] == 'PING':
                    await self.raw('PONG ' + args[1]) # Respond to the server's PING request with a PONG to prevent ping timeout
            elif args[1] == '001': # RPL_WELCOME
                    await self.raw(f'MODE {self.nickname} +B') # Set user mode +B (Bot)
                    await asyncio.sleep(10) # Wait 10 seconds before joining the channel (required by some IRCds to wait before JOIN)
                    await self.raw(f'JOIN {self.channel} {self.channelkey}')
            elif args[1] == '433': # ERR_NICKNAMEINUSE
                    self.nickname += '_' # If the nickname is already in use, append an underscore to the end of it
                    await self.raw('NICK ' + self.nickname) # Send the new nickname to the server
            elif args[1] == 'KICK':
                    chan   = args[2]
                    kicked = args[3]
                    if kicked == self.nickname:
                        await asyncio.sleep(3)
                        await self.raw(f'JOIN {chan}')
            elif args[1] == 'PRIVMSG':
                    ident  = args[0][1:]
                    nick   = args[0].split('!')[0][1:].lower()
                    target = args[2]
                    msg  = ' '.join(args[3:])[1:]
                    arguments = msg.split()
                    bandageamount = '0'
                    if target == self.nickname:
                        pass # Handle private messages here
                    if target.startswith('#'): # Channel message
                        if msg.startswith('!'):
                            try:    
                                if time.time() - config.throttle.last < config.throttle.cmd and config.throttle.lastnick == nick:
                                    if not config.throttle.slow:
                                        config.throttle.slow = True
                                        await bot.sendmsg(config.irc.channel, color("Slow down homie!!", red))
                                        
                                else:
                                    config.throttle.slow = False
                                    config.throttle.lastnick = nick
                                    if arguments[0] == '!hug':
                                        await bot.sendmsg(target, f'[XOXO Hugger9000... {nick} hugs {arguments[1]}]')
                                    if arguments[0] == '!admins':
                                        for i in config.irc.admins:
                                            await bot.sendmsg(target, f'[Admins: ' + color(i, red) + ']')
                                    if arguments[0] == '!shop':
                                        await bot.sendmsg(config.irc.channel, f'[Shop Accessories]')
                                        await bot.sendmsg(config.irc.channel, f'[!buy weapon - purchase a 3-round burst gun (note: weapon has a quality of 300 trigger limit)]')
                                        await bot.sendmsg(config.irc.channel, f'[!buy ammo - buy ammunition (+60 rounds) for your weapon]')
                                        await bot.sendmsg(config.irc.channel, f'[!buy bandages <amount>]')
                                        await bot.sendmsg(config.irc.channel, f'[!buy <medkit> - Purchase a Full Health Medkit]')
                                    if arguments[0] == '!buy' and arguments[1] != None:
                                        if arguments[1] == 'weapon':
                                            value = await functions.buyweapon(nick)
                                            await bot.sendmsg(config.irc.channel, f'{value}')
                                            
                                        elif arguments[1] == 'ammo':
                                            await functions.buyammo(nick)
                                        elif arguments[1] == 'bandages':
                                            if len(arguments) <= 2 or int(arguments[2]) == 0:
                                                await bot.sendmsg(config.irc.channel, '[You must specify amount of bandages (greater than 0) to purchase]')
                                            else:
                                                await functions.buybandages(nick, int(arguments[2]))
                                                
                                        elif arguments[1] == 'medkit':
                                            await functions.buymedkit(nick)
                                    if arguments[0] == '!test':
                                        value = await functions.testfunction(nick)
                                        await bot.sendmsg(config.irc.channel, f'{value}')

                                    if arguments[0] == '!shoot':
                                        await functions.shoot(arguments[1].lower(), nick)
                                        #await bot.sendmsg(config.irc.channel, f'{value}')
                                    if arguments[0] == '!reload':
                                        value = await functions.reloadammo(nick)
                                        if value != None:
                                           await bot.sendmsg(config.irc.channel, f'{value}')
                                    if arguments[0] == '!ammo':
                                        await functions.ammo(nick)
                                    if arguments[0] == '!top10':
                                        if len(arguments) <= 1:
                                            await functions.top('kills')
                                        elif arguments[1] == 'kills':
                                            await functions.top('kills') 
                                        elif arguments[1] == 'exp':
                                            await functions.top('exp')
                                                                              
                                    if arguments[0] == '!heal':
                                        if len(arguments) <= 1:
                                            await bot.sendmsg(config.irc.channel, '[You must specify a bandage or a medkit]')
                                        else:
                                            
                                            if arguments[1] == 'bandage' or arguments[1] == 'medkit':
                                                value = await functions.heal(arguments[1], nick)  
                                                await bot.sendmsg(config.irc.channel, f'{value}')    
                                    if arguments[0] == '!revive':
                                        value = await functions.revive(nick)
                                        await bot.sendmsg(config.irc.channel, f'{value}')
                                    if arguments[0] == '!help':
                                        await bot.sendmsg(config.irc.channel, '[Command List]')
                                        await bot.sendmsg(config.irc.channel, '[!help - shows commands]')
                                        await bot.sendmsg(config.irc.channel, '[!register - Register your player]')
                                        await bot.sendmsg(config.irc.channel, '[!profile - Shows Profile Stats [!profile username]')
                                        await bot.sendmsg(config.irc.channel, '[!top10 <kills/exp> - Shows Top 10 by Kills or Experience]')
                                        await bot.sendmsg(config.irc.channel, '[!punch <enemy> - Fight [!punch username]')
                                        await bot.sendmsg(config.irc.channel, '[!shoot <enemy> - Shoot if you own a weapon]')
                                        await bot.sendmsg(config.irc.channel, '[!bank - Returns Bank Balance]')
                                        await bot.sendmsg(config.irc.channel, '[!shop - Shows items that you can !buy]')
                                        await bot.sendmsg(config.irc.channel, '[!buy <item> [weapon, ammo, medkit, bandages <amount>]')
                                        await bot.sendmsg(config.irc.channel, '[!reload - Reloads Weapon]')
                                        await bot.sendmsg(config.irc.channel, '[!ammo - Show Ammunition Amounts]')    
                                        await bot.sendmsg(config.irc.channel, '[!bandages - Shows Bandage Amounts]')
                                        await bot.sendmsg(config.irc.channel, '[!revive - Brings you back to health if dead]')
                                        await bot.sendmsg(config.irc.channel, '[!heal <bandage/medkit> - Use bandages or medkit (100 percent heal) regain health]')
                                        await bot.sendmsg(config.irc.channel, ' ')
                                        await bot.sendmsg(config.irc.channel, '[Admin Command List]')
                                        await bot.sendmsg(config.irc.channel, '[!setlevel - !setlevel username Level (1 to 5)]')
                                        await bot.sendmsg(config.irc.channel, '[!adduser <user> - Force create a user]')
                                        await bot.sendmsg(config.irc.channel, '[!remove <user> - Removes a player]')
                                        await bot.sendmsg(config.irc.channel, '[!removeweapon <user> - Remove user weapon]')
                                    if arguments[0] == '!bank':
                                        await functions.getmoney(nick)
                                    if arguments[0] == '!bandages':
                                        await functions.getbandages(nick)
                                    if nick in config.irc.admins:
                                        #await self.sendmsg(target, f'{nick} is an ' + color('Admin!', red))
                                        if arguments[0] == '!modreload':
                                            reload(functions)
                                        if arguments[0] == '!removeweapon':
                                            value = await functions.removeweapon(nick)
                                            await bot.sendmsg(config.irc.channel, f'{value}')
                                        if arguments[0] == '!adduser':
                                            name = arguments[1].lower()
                                    
                                            c.execute(f"SELECT rowid FROM users WHERE name = (:name)", {'name': name})
        
                                            data=c.fetchone()
                                            if data is None:
                                                await bot.sendmsg(config.irc.channel, '[Registering Player: %s]'%name)
                                                await functions.createuser(name)
                                                await functions.profile(name)
                                            else:
                                                await bot.sendmsg(config.irc.channel, f'{color("[Player already exists!]", red)}')

                                        if arguments[0] == '!remove':
                                            logging.debug('remove user')
                                            name = arguments[1].lower()
                                            c.execute(f"SELECT rowid FROM users WHERE name= (:name)", {'name': name})
                                            
                                            data=c.fetchone()
                                            if data != None:
                                                await bot.sendmsg(config.irc.channel, f'[Removing {color(name, red)} from database]')
                                                await functions.removeuser(name)
                                            else:
                                                await bot.sendmsg(config.irc.channel, f'[User does not exist]')
                                                
                                        if arguments[0] == '!setlevel':
                                               value = await functions.setlevel(arguments[1].lower(), arguments[2])
                                               await bot.sendmsg(config.irc.channel, f'{value}')
                                    if arguments[0] == '!register':
                                        c.execute(f"SELECT rowid FROM users WHERE name = (:name)", {'name': nick})
    
                                        data=c.fetchone()
                                        if data is None:
                                            await bot.sendmsg(config.irc.channel, f'[Registering Player: %s]'%nick)
                                            await functions.createuser(nick)
                                            await functions.profile(nick)
                                        else:
                                           await bot.sendmsg(config.irc.channel, f'{color("[Player already exists!]", red)}')
                                    if arguments[0] == '!profile':
                                        try:
                                            await functions.profile(arguments[1].lower()) 
                                        except:
                                            await functions.profile(nick)
                                    if arguments[0] == '!punch':
                                        await functions.punch(arguments[1].lower(), nick)
                                config.throttle.last = time.time()
                            except Exception as ex:
                                if time.time() - config.throttle.last < config.throttle.cmd:
                                    if not config.throttle.slow:
                                        await bot.sendmsg(config.irc.channel, color('Slow down homie!', red))
                                        config.throttle.slow = True
                                config.throttle.last = time.time()

                            
                #except (UnicodeDecodeError, UnicodeEncodeError):
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass # Some IRCds allow invalid UTF-8 characters, this is a very important exception to catch
        except Exception as ex:
            logging.exception(f'Unknown error has occured! ({ex})')
def setup_logger(log_filename: str, to_file: bool = False):
    '''
    Set up logging to console & optionally to file.

    :param log_filename: The filename of the log file
    '''
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)9s | %(message)s', '%I:%M %p'))
    if to_file:
        fh = logging.handlers.RotatingFileHandler(log_filename+'.log', maxBytes=250000, backupCount=3, encoding='utf-8') # Max size of 250KB, 3 backups
        fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)9s | %(filename)s.%(funcName)s.%(lineno)d | %(message)s', '%Y-%m-%d %I:%M %p')) # We can be more verbose in the log file
        logging.basicConfig(level=logging.NOTSET, handlers=(sh,fh))
    else:
        logging.basicConfig(level=logging.NOTSET, handlers=(sh,))
        
        
bot = Bot()
def run():
    functions.createtable()
    setup_logger('skeleton', to_file=True) # Optionally, you can log to a file, change to_file to False to disable this.
    asyncio.run(bot.connect())       
