import sqlite3
import logging
import logging.handlers
import random
from time import sleep
from config import config
from importlib import reload
import irc
import sys
from colors import *
conn = sqlite3.connect("data.db")
c = conn.cursor()
reset       = '\x0f'
def createtable():
    c.execute('''CREATE TABLE if not exists users (
        name text unique,
        level integer,
        experience integer,
        health integer,
        attack integer,
        defense integer,
        money integer,
        healthmax integer,
        kills integer,
        deaths integer
    
)''')
    c.execute('''CREATE TABLE if not exists weapons (
        name text unique,
        weaponheld integer,
        clip integer,
        ammunition integer,
        expire integer
    
)''')    
    c.execute('''CREATE TABLE if not exists items (
        name text unique,
        bandages integer,
        medkits integer
    )''')

def color(msg: str, foreground: str, background: str='') -> str:
    '''
    Color a string with the specified foreground and background colors.
    
    :param msg: The string to color.
    :param foreground: The foreground color to use.
    :param background: The background color to use.
    '''
    return f'\x03{foreground},{background}{msg}{reset}' if background else f'\x03{foreground}{msg}{reset}'


class Users:
    def __init__(self, name, level, experience, health, attack, defense, money, healthmax, kills, deaths):
        self.name = name
        self.level = level
        self.experience =  experience
        self.health = health
        self.attack = attack
        self.defense = defense 
        self.money = money
        self.healthmax = healthmax
        self.kills =  kills
        self.deaths = deaths
        
class Weapons:
    def __init__(self, name, weaponheld, clip, ammunition):
        self.name = name
        self.weaponheld = weaponheld
        self.clip = clip
        self.ammunition = ammunition
        self.expire = 0
class Items:
    def __init__(self, name, bandages):
        self.name = name
        self.bandages = bandages

async def checkexist(player):
    c.execute(f'SELECT rowid FROM users WHERE name=(:name)', {'name': player})
        
    data=c.fetchone()
    
    if data is None:
        return f'Invalid Player: %s'%player
    else:
        return True 
async def addexp(name, amount):
    c.execute(f'SELECT * FROM users WHERE name=(:name)', {'name': name})
    getexp=c.fetchall()
    for grabexp in getexp:
        experience = grabexp[2]
        level = grabexp[1]
        
        exp = experience + amount
        if exp < 1000:
            c.execute(f"UPDATE users SET experience = (:experience) WHERE name=(:name)", {'experience': exp, 'name': name}) 
            conn.commit()
            await irc.bot.sendmsg(config.irc.channel, f'[Player: {name}] [Experience increased: +{amount}/{exp}]')
        elif exp >= 3000:
            await irc.bot.sendmsg(config.irc.channel, f'[Player: {name}] [Experience increased: +{amount}/{exp}]')
            
            if level < 5:
                c.execute(f"UPDATE users SET experience = (:experience) WHERE name=(:name)", {'experience': exp, 'name': name}) 
                conn.commit()
                
                await irc.bot.sendmsg(config.irc.channel, f'[Player: {name}] [Level increase: 5]')
                await setlevel(name, '5')
            else:
                c.execute(f"UPDATE users SET experience = (:experience) WHERE name=(:name)", {'experience': exp, 'name': name}) 
                conn.commit() 
        elif exp >= 1500:
            await irc.bot.sendmsg(config.irc.channel, f'[Player: {name}] [Experience increased: +{amount}/{exp}]')
            
            if level < 3:
                c.execute(f"UPDATE users SET experience = (:experience) WHERE name=(:name)", {'experience': exp, 'name': name}) 
                conn.commit()
                
                await irc.bot.sendmsg(config.irc.channel, f'[Player: {name}] [Level increase: 3]')
                await setlevel(name, '3')
            else:
                c.execute(f"UPDATE users SET experience = (:experience) WHERE name=(:name)", {'experience': exp, 'name': name}) 
                conn.commit()

           
        elif exp >= 1000:
            
            await irc.bot.sendmsg(config.irc.channel, f'[Player: {name}] [Experience increased: +{amount}/{exp}]')
            
            if level < 2:
                c.execute(f"UPDATE users SET experience = (:experience) WHERE name=(:name)", {'experience': exp, 'name': name}) 
                conn.commit()
                
                await irc.bot.sendmsg(config.irc.channel, f'[Player: {name}] [Level increase: 2]')
                await setlevel(name, '2')
            else:
                c.execute(f"UPDATE users SET experience = (:experience) WHERE name=(:name)", {'experience': exp, 'name': name}) 
                conn.commit()
                
            
            
        


        
async def addkillstat(name):
        c.execute(f'SELECT * FROM users WHERE name=(:name)', {'name': name})
        getkills=c.fetchall()
        for retrieve in getkills:
            kills = retrieve[8] + 1
            
        c.execute(f'UPDATE users SET KILLS = (:kills) WHERE name=(:name)', {'kills': kills, 'name': name})
        conn.commit()
    
        await irc.bot.sendmsg(config.irc.channel, f'[Player {color(name, light_green)} has a total of {color(kills, red)} kills!]')

async def adddeathstat(name):
        c.execute(f'SELECT * FROM users WHERE name=(:name)', {'name': name})
        getkills=c.fetchall()
        for retrieve in getkills:
            kills = retrieve[1]
            deaths = retrieve[9] + 1
            
        c.execute(f'UPDATE users SET DEATHS = (:deaths) WHERE name=(:name)', {'deaths': deaths, 'name': name})
        conn.commit()
        await irc.bot.sendmsg(config.irc.channel, f'[Player {color(name, red)} has died {color(deaths, red)} times!]')

async def buymedkit(name):
    c.execute(F'SELECT * FROM items WHERE name=(:name)', {'name': name})
    meds = c.fetchall()
    for havemedkit in meds:
        if havemedkit[2] == 1:
            await irc.bot.sendmsg(config.irc.channel, f'[You already have a medkit!]')
            return
        shopamount = 250
        c.execute(f'SELECT * FROM users WHERE name=(:name)', {'name': name})
        usermoney = c.fetchall()
        for grabmoney in usermoney:
            money = grabmoney[6]
            if money >= shopamount:
                await irc.bot.sendmsg(config.irc.channel, f'[You have purchased a medkit for $250!]')
                testone = 1
                c.execute(f'UPDATE ITEMS set MEDKITS = (:medkits) WHERE NAME = (:name)', {'medkits': testone, 'name': name})
                conn.commit()
                money = money - shopamount
                c.execute(f'UPDATE users set MONEY = (:money) WHERE NAME = (:name)', {'money': money, 'name': name})   
                conn.commit()
            else:
                await irc.bot.sendmsg(config.irc.channel, f'[You do {color("NOT", red)} have enough funds!]')
                return           
async def buybandages(name, amount):
    if amount == 0 or amount == None:
        return f'[Must specify how many bandages you want... !buy bandages <amount>]'
    
    shopamount = amount * 50
    c.execute(f'SELECT * FROM items WHERE name=(:name)', {'name': name})
    look = c.fetchall()
    
    for band in look:
        bandages = band[1]
        
    c.execute(f'SELECT * FROM users WHERE name=(:name)', {'name': name})
    usermoney = c.fetchall()
    for grabmoney in usermoney:
        money = grabmoney[6]
        if money >= shopamount:
            bandages = band[1]
            bandagestotal = bandages + amount


            await irc.bot.sendmsg(config.irc.channel, f'[You have purchased [{amount}] bandages! Cost is ${shopamount:,}]')
            c.execute(f'UPDATE ITEMS set BANDAGES = (:bandages) WHERE NAME = (:name)', {'bandages': bandagestotal, 'name': name})
            conn.commit()
            money = money - shopamount
            c.execute(f'UPDATE users set MONEY = (:money) WHERE NAME = (:name)', {'money': money, 'name': name})   
            conn.commit()
        else:
            await irc.bot.sendmsg(config.irc.channel, f'[You do {color("NOT", red)} have enough funds!]')
            return
        
async def top(type):
    if type == 'kills':
        c.execute("SELECT * FROM users ORDER BY kills DESC LIMIT 10") 
        test =c.fetchall()
        a = 0
        for i in test: 
            a = a + 1
            await irc.bot.sendmsg(config.irc.channel, f'[#{color(a, pink)}] [Player: {color(i[0], red)}] [Kills: {color(i[8], light_green)}] [Deaths: {color(i[9], red)}]')


    elif type == 'exp':
        c.execute("SELECT * FROM users ORDER BY experience DESC LIMIT 10") 
        test =c.fetchall()
        a = 0
        for i in test: 
            a = a + 1
            await irc.bot.sendmsg(config.irc.channel, f'[#{color(a, pink)}] [Player: {color(i[0], red)}] [Experience: {color(i[2], light_blue)}] [Kills: {color(i[8], light_green)}] [Deaths: {color(i[9], red)}]')
           
# display data row by row 

  
async def heal(item, name):
        if item == 'bandage':
            c.execute(f'SELECT * from USERS WHERE name= (:name)', {'name': name})
            newtest=c.fetchall()
            for userinfo in newtest:
                health = userinfo[3]
                if health <= 0:
                    return f'[You are dead... !revive to bring yourself back]'
                                    
                maxhealth = userinfo[7]
                if health == maxhealth:
                    return f'[You already at FULL HEALTH]'
                c.execute(f'SELECT * FROM items WHERE name = (:name)', {'name': name})
                bandaids = c.fetchall()
                for bandages in bandaids:
                    if bandages[1] <= 0:
                        return f'[You do not have any bandages... !buy bandages <amount number>]'

                
                newhealth = health + 25
                if newhealth >= maxhealth:
                    health = maxhealth
                    c.execute(f'UPDATE USERS set HEALTH = (:health) where NAME = (:name)', {'health': health, 'name': name})
                    conn.commit()
                    ihealth = newhealth - maxhealth
                    i2health = 25 - ihealth
                    return f'[Player healed {color(i2health, light_green)} to MAX health {color(health, light_green)}]'
                else:
                    c.execute(f'UPDATE USERS set HEALTH = (:health) where NAME = (:name)', {'health': newhealth, 'name': name})
                    conn.commit()

                
                    c.execute(f'SELECT * FROM items WHERE name=(:name)', {'name': name})
                    bandaids=c.fetchall()        
                    for checkitems in bandaids:
                        bandages = checkitems[1]
                        bandages = bandages - 1
                        c.execute(f'UPDATE ITEMS set BANDAGES = (:bandages) WHERE name = (:name)', {'bandages': bandages, 'name': name})
                        conn.commit()
                        return f'[Player healed {color("+25", light_green)} to health {color(newhealth, light_green)}]'
        if item == 'medkit':
                 c.execute(f'SELECT * FROM items WHERE name=(:name)', {'name': name})
                 meds=c.fetchall()
                 for medkit in meds:
                     havemedkit = medkit[2]
                     if havemedkit <= 0:
                         return f'[You do not have a MedKit... !buy medkit]'
                        
                        
                 c.execute(f'SELECT * from USERS WHERE name= (:name)', {'name': name})
                 newtest=c.fetchall()
                 for userinfo in newtest:
                        health = userinfo[3]
                        if health <= 0:
                            return f'[You are dead... !revive to bring yourself back]'
                        else:
                            maxhealth = userinfo[7]
                            if health == maxhealth:
                                 return f'[You already at FULL HEALTH]'
                    
                        c.execute(f'UPDATE ITEMS set MEDKITS = (:medkits) WHERE name = (:name)', {'medkits': 0, 'name': name})
                        c.execute(f'UPDATE USERS set HEALTH = (:health) where NAME = (:name)', {'health': maxhealth, 'name': name})
                        conn.commit()

                        return f'[You used your MedKit to Regain Full Health]'

async def reloadammo(nick):
    c.execute(f"SELECT rowid FROM users WHERE name=(:name)", {'name': nick})
    if c.fetchone() == None:
        logging.debug('User is trying to reload without having an account')
        await irc.bot.sendmsg(config.irc.channel, f'[User {nick} does not have an account]')
        return
    
    c.execute(f"SELECT * FROM weapons WHERE name=(:name)", {'name': nick})
    data=c.fetchall()
    name = nick
    for check in data:
        hasweapon = check[1]
        if hasweapon == False:
            logging.debug('User does not have weapon')
            await irc.bot.sendmsg(config.irc.channel, f'[You do not currently have a weapon.. !buy weapon]')
            return
    
        maxclip = 30
        clip = check[2]
        ammunition = check[3]
        if ammunition <= 0:
            return f'!buy ammo'
            
        clipadd = 30 - clip
        if ammunition >= clipadd:
            ammunition = ammunition - clipadd
            clip = clip + clipadd
        else:
            clip = clip + ammunition
            ammunition = 0
            
        logging.debug(f'[Current clip ammunition is at {clip} rounds and backup ammunition is at {ammunition} magazine rouunds!]')
        
        await irc.bot.sendmsg(config.irc.channel, f'[Current clip has {clip} rounds out of {maxclip} mag ammo size and {ammunition} in the arsenal!]')
        c.execute(f"UPDATE WEAPONS set CLIP = (:clip) WHERE NAME = (:name)", {'clip': clip, 'name': nick})
        conn.commit()
        c.execute(f"UPDATE WEAPONS set AMMUNITION = (:ammunition) WHERE NAME = (:name)", {'ammunition': ammunition, 'name': name})
        conn.commit()



async def shoot(player, nick):
    check = await checkexist(nick)
    checkplayer = await checkexist(player)
    if check != True:
        await irc.bot.sendmsg(config.irc.channel, f'[{color("Player does not exist.", red)} !register]')
        return
    if checkplayer != True:
        await irc.bot.sendmsg(config.irc.channel, f'[{color("Player does not exist.", red)}]')
        return
    else:  
        if player == nick:
            logging.debug('Player cannot attack oneself')
            await irc.bot.sendmsg(config.irc.channel, f'[Error: {color("Cannot Attack Yourself", red)}]')
            return
        c.execute(f'SELECT rowid FROM weapons WHERE name=(:name)', {'name': nick})
        checkrow=c.fetchone()
        if checkrow == None:
            await irc.bot.sendmsg(config.irc.channel, f'[Error: {color("No Weapons", red)}] - !buy weapon')
            return
        c.execute(f"SELECT * FROM users WHERE name=(:name)", {'name': nick})
        healthcheck = c.fetchall()
        for checkalive in healthcheck:
            alive = checkalive[3]
            if alive <= 0:
                await irc.bot.sendmsg(config.irc.channel, f'[Error: {color("You Are Dead... !revive", red)}]')
                return
        c.execute(f"SELECT * FROM users WHERE name=(:name)", {'name': player})
        playerhealthcheck = c.fetchall()
        for checkalive in playerhealthcheck:
            health = checkalive[3]
            if health <= 0:
                logging.debug('Player targeted is DEAD')
                await irc.bot.sendmsg(config.irc.channel, f'[Player targeted is {color("DEAD", red)}]')
                return
        c.execute(f"SELECT * FROM weapons WHERE name=(:name)", {'name': nick})
        weapons = c.fetchall()
        for reg in weapons:
                
            name = nick
            weaponheld = reg[1]
            expire = reg[4]
            c.execute(f"SELECT rowid FROM weapons WHERE name=(:name)", {'name': name})

            if weaponheld == 0:
                await irc.bot.sendmsg(config.irc.channel, f'You do not own a weapon!')
                return
            clip = reg[2]
            
            ammunition = reg[3]
            
            if clip == 0:
                logging.debug('Weapon out of ammo! !buy ammo and !reload')
                c.execute("INSERT OR REPLACE INTO weapons VALUES (:name, :weaponheld, :clip, :ammunition, :expire)", {'name': nick, 'weaponheld': weaponheld, 'clip': clip, 'ammunition': ammunition, 'expire': expire})

                conn.commit()
                await irc.bot.sendmsg(config.irc.channel, f'{color("OUT OF AMMO - !reload", red)}')
                return
            else:
                c.execute("SELECT * FROM weapons WHERE name=(:name)", {'name': name})
                checkexpire=c.fetchall()
                for expiring in checkexpire:
                    expires = expiring[4]
                    if expires == 300:
                        logging.debug('User weapon has expired Weapon and Ammo Purged. !buy weapon')
                        c.execute('''UPDATE WEAPONS set WEAPONHELD = False,
                                  CLIP = 0,
                                  AMMUNITION = 0,
                                  EXPIRE = 0
                                  WHERE name = (:name)''', {'name': name})
                        conn.commit()
                        await irc.bot.sendmsg(config.irc.channel, f'[Player weapon has expired... purging weapon! <!buy weapon> for a new one]')

                
                clip = clip - 3
                c.execute("INSERT OR REPLACE INTO weapons VALUES (:name, :weaponheld, :clip, :ammunition, :expire)", {'name': nick, 'weaponheld': weaponheld, 'clip': clip, 'ammunition': ammunition, 'expire': expire})

                conn.commit()
                    
                shooter = c.execute("SELECT * FROM users WHERE name=(:name)", {'name': player})
                for reg in shooter:
                    playerhealth = reg[3]
                    if random.random() < 0.10:
                        area = "headshot"
                        damage = random.randint(180, 240)
                    elif random.random() < 0.2:
                        area =  "chest"
                        damage = random.randint(100, 120)
                    elif random.random() < 0.3:
                        area = "arm"
                        damage = random.randint(40, 80)
                    elif random.random() > 0.4:
                        area = "leg"
                        damage = random.randint(60, 100)
                    else:
                        area = "stomach"
                        damage = random.randint(75, 100)
                        
                    damage = min(damage, int(playerhealth))
        
                    playerhealth = int(playerhealth) - int(damage)
                    expire = expire + 1
                    c.execute("UPDATE WEAPONS set EXPIRE = (:expire) where NAME = (:name)", {'expire': expire, 'name': name})
                    conn.commit()
                    if playerhealth <= 0:
                        await addmoney(nick) 

                        playerhealth = 0
                        c.execute('UPDATE USERS set HEALTH = (:health) where NAME = (:name)', {'health': playerhealth, 'name': player})
                        conn.commit()
                        await irc.bot.sendmsg(config.irc.channel, '[Player {1} killed {2} and did {3} damage]'.format(0, color(nick, light_green), color(player, red), color(int(damage), light_green)))
                        await addkillstat(nick) 
                        await adddeathstat(player)
                        await addexp(nick, 5)
                        return
                    c.execute('UPDATE USERS set HEALTH = (:health) where NAME = (:name)', {'health': playerhealth, 'name': player})
                    conn.commit()
                    #return f'[{player} health is now {playerhealth} and took {damage} damage!]')
                    await irc.bot.sendmsg(config.irc.channel, '[Character: {1}] shot at [{2}] with an M16, hitting them in the {4} and did [{3}] damage!]'.format(0, color(nick, light_green), color(player, red), color(int(damage), green), color(area, red)))
 

                await irc.bot.sendmsg(config.irc.channel, f'[Remaining clip magazine rounds: {clip}]')
                return
                 
  #  return f'[!buy bandages - buys bandages for health] {color("* not done yet", red)}')
async def buyammo(nick):
    c.execute(f"SELECT * FROM weapons WHERE name=:name", {'name': nick})
    weapons = c.fetchall()
    c.execute(f"SELECT * FROM users WHERE name=:name", {'name': nick})
    user = c.fetchall() 
    for reg in user:
       name = nick
       money = reg[6]
       newmoney = money - 50
       c.execute("UPDATE USERS set MONEY = (:money) where NAME = (:name)", {'money': newmoney, 'name': name})
       conn.commit()
       await irc.bot.sendmsg(config.irc.channel, f'[Player {name} purchased 60 rounds of ammunition for {color("$50", light_blue)}]')
    for weps in weapons:   
       
       ammunition = weps[3]
       weaponheld = weps[1]
       clip = weps[2]
       ammunition += 60
       expire = weps[4]
       c.execute("INSERT OR REPLACE INTO weapons VALUES (:name, :weaponheld, :clip, :ammunition, :expire)", {'name': nick, 'weaponheld': weaponheld, 'clip': clip, 'ammunition': ammunition, 'expire': expire})
       conn.commit()
       await irc.bot.sendmsg(config.irc.channel, f'[Player {nick} weapon ammunition is now {ammunition}]')
        
async def removeweapon(nick):
    remweapon = Weapons(nick, 0, 0, 0)

    c.execute("UPDATE WEAPONS set WEAPONHELD = (:weaponheld) where NAME = (:name)", {'weaponheld': 0, 'name': nick})
    conn.commit()
    logging.debug('Removed weapon')
    return f'[Player {nick} has been revoked of his/her weapon!]'   
async def buyweapon(nick):
    c.execute(f"SELECT * FROM weapons WHERE name=:name", {'name': nick})
    weapons = c.fetchall()
    c.execute(f"SELECT * FROM users WHERE name=:name", {'name': nick})
    user = c.fetchall()
    for regs in user:
       name = nick
       money = regs[6]
       for weapon in weapons:
         weaponheld = weapon[1]           
         if weaponheld == 1:
           logging.debug('Weapon is already held, returning')
           
           return f'[Weapon is already held, !buy ammo for more ammunition]'
           
    clip = 30
    ammunition = 60
    money = money - 500
       
    c.execute("UPDATE USERS set MONEY = (:money) where NAME = (:name)", {'money': money, 'name': nick})
    conn.commit()
    logging.debug(f'Attempting to buy Weapon for {nick}') 
    weaponheld = True
    logging.debug('Buying weapon')
    expire = 0
    c.execute("INSERT OR REPLACE INTO weapons VALUES (:name, :weaponheld, :clip, :ammunition, :expire)", {'name': nick, 'weaponheld': weaponheld, 'clip': clip, 'ammunition': ammunition, 'expire': expire})
    conn.commit()
    return f'[Player: {nick} has purchased a gun for $500! Loaded clip of {clip} rounds!]'


async def removeuser(nick):
    logging.debug(f'Removing user {nick}')
    name = nick
    c.execute('''DELETE FROM users WHERE name=?''',(name,))
    conn.commit() 
    c.execute('''DELETE FROM items WHERE name=?''',(name,))
    conn.commit() 
    c.execute('''DELETE FROM weapons WHERE name=?''',(name,))
    conn.commit() 
    c.execute('''DELETE FROM stats WHERE name=?''',(name,))
    conn.commit() 
    logging.debug(f'Removed user {nick}')

async def createuser(nick):
    
    logging.debug(f'Attemping to create user {nick}')
    reguser = Users(nick, 1, 500, 500, 100, 100, 5000, 500, 0, 0)
    
    logging.debug(f'User {nick} added to database')
    
    c.execute("INSERT OR REPLACE INTO users VALUES (:name, :level, :experience, :health, :attack, :defense, :money, :healthmax, :kills, :deaths)", {'name': nick, 'level': reguser.level, 'experience': reguser.experience, 'health': reguser.health, 'attack': reguser.attack, 'defense': reguser.defense, 'money': reguser.money, 'healthmax': reguser.healthmax, 'kills': reguser.kills, 'deaths': reguser.deaths})
    conn.commit()
    c.execute("INSERT OR REPLACE INTO items VALUES (:name, :bandages, :medkits)", {'name': nick, 'bandages': 0, 'medkits': 0})
    conn.commit()

    c.execute(f'SELECT rowid FROM stats WHERE name=(:name)', {'name': nick})
    checkrow=c.fetchone()
    if checkrow == None:
        kills = 0
        deaths = 0
        c.execute(f'INSERT OR REPLACE INTO stats VALUES (:name, :kills, :deaths)', {'name': nick, 'kills': kills, 'deaths': deaths})  
        conn.commit()
        #return f'[Player {color(name, light_green)} has a total of {color(kills, red)} kills!]')
async def setlevel(nick, level):
    if level == '1':
        experience = '500'
        health = '500'
        attack = '100'
        defense = '100'
        healthmax = '500'
        c.execute(f'''UPDATE USERS set LEVEL = (:level),
                  EXPERIENCE = (:experience), 
                  HEALTH = (:health), 
                  ATTACK = (:attack), 
                  DEFENSE = (:defense),
                  HEALTHMAX = (:healthmax)
                  where NAME = (:name)''', {'level': level, 'experience': experience, 'health': health, 'attack': attack, 'defense': defense, 'name': nick, 'healthmax': healthmax})
        conn.commit()
        return f"[Player: {nick} is now level {color(level, red)}]"
   
    elif level == '2':
        #experience = '1000'
        health = '1000'
        attack = '200'
        defense = '200'
        healthmax = '1000'
        c.execute(f'''UPDATE USERS set LEVEL = (:level),
                  HEALTH = (:health), 
                  ATTACK = (:attack), 
                  DEFENSE = (:defense),
                  HEALTHMAX = (:healthmax)
                  where NAME = (:name)''', {'level': level, 'health': health, 'attack': attack, 'defense': defense, 'name': nick, 'healthmax': healthmax})
        conn.commit()
        return f"[Player: {nick} is now level {color(level, red)}]"

     
    elif level == '3':
        #experience = '1500'
        health = '1500'
        attack = '300'
        defense = '300'
        healthmax = '1500'
        c.execute(f'''UPDATE USERS set LEVEL = (:level),
                  HEALTH = (:health), 
                  ATTACK = (:attack), 
                  DEFENSE = (:defense),
                  HEALTHMAX = (:healthmax)
                  where NAME = (:name)''', {'level': level, 'health': health, 'attack': attack, 'defense': defense, 'name': nick, 'healthmax': healthmax})
        conn.commit()
        return f"[Player: {nick} is now level {color(level, red)}]"

    elif level == '4':
#        experience = '2000'
        health = '2000'
        attack = '400'
        defense = '400'
        healthmax = '2000'
        c.execute(f'''UPDATE USERS set LEVEL = (:level),
                  HEALTH = (:health), 
                  ATTACK = (:attack), 
                  DEFENSE = (:defense),
                  HEALTHMAX = (:healthmax)
                  where NAME = (:name)''', {'level': level, 'health': health, 'attack': attack, 'defense': defense, 'name': nick, 'healthmax': healthmax})
        conn.commit()
        return f"[Player: {nick} is now level {color(level, red)}]"
  
    elif level == '5':
        experience = '3000'
        health = '3000'
        attack = '500'
        defense = '500'
        healthmax = '3000'
        c.execute(f'''UPDATE USERS set LEVEL = (:level),
                  HEALTH = (:health), 
                  ATTACK = (:attack), 
                  DEFENSE = (:defense),
                  HEALTHMAX = (:healthmax)
                  where NAME = (:name)''', {'level': level, 'health': health, 'attack': attack, 'defense': defense, 'name': nick, 'healthmax': healthmax})
        conn.commit()
        return f"[Player: {nick} is now level {color(level, red)}]"
    elif int(level) > 5:
        return "[Error: Invalid Level]"
        

async def closesql():  
    conn.close()
class combat:
    class attacker:
        name = ''
        attack = ''
    class defender:
        name = ''
        defense = ''
        health = ''
        
async def punch(player, nick):
    check = await checkexist(player)
    checkplayer = await checkexist(nick)
    if check != True:
        await irc.bot.sendmsg(config.irc.channel, f'[{color("Player does not exist.", red)} !register]')
        return
    if checkplayer != True:
        await irc.bot.sendmsg(config.irc.channel, f'[{color("Player does not exist.", red)} !register]')
        return
    else:
        for name in (nick):
            c.execute(f"SELECT * FROM users WHERE name=:name", {'name': nick})
            attacker = c.fetchall()
            c.execute(f"SELECT * FROM users WHERE name=:name", {'name': player})
            defender = c.fetchall()
        if nick == player:
            await irc.bot.sendmsg(config.irc.channel, '[Error: {1}]'.format(0,color('Cannot Attack Yourself', red)))
            return
        for att in attacker:
            combat.attacker.name = att[0]
            combat.attacker.attack = att[4]
            combat.attacker.health = att[3]
            if combat.attacker.health == 0:
                await irc.bot.sendmsg(config.irc.channel, '[Error: You Are {1}!]'.format(0, color('Dead', red)))
                return
        for defend in defender:
            combat.defender.name = defend[0]
            combat.defender.defense = defend[5]
            combat.defender.health = defend[3]
        playerhealth = combat.defender.health

        if combat.defender.health <= 0:
                await irc.bot.sendmsg(config.irc.channel, f'[Player targeted is {color("DEAD", light_blue)}]')
                return
        playerdef = combat.defender.defense
        playerattack = combat.attacker.attack
        critical_multiplier = 1.1 if random.random() < 0.10 else 1.0
        effective_defense = int(playerdef) * random.uniform(0.9, 1.1)
        effective_attack = int(playerattack) * random.uniform(1.0, 1.1)
        damage = effective_attack * (50 / (50 + effective_defense)) * critical_multiplier
        damage = min(damage, int(playerhealth))
    
        combat.defender.health = int(playerhealth) - int(damage)
        c.execute(f'''UPDATE USERS set HEALTH = (:health) where NAME = (:name)''', {'health': combat.defender.health, 'name': combat.defender.name})
 
        conn.commit()
        if combat.defender.health <= 0:
            await irc.bot.sendmsg(config.irc.channel, '[Player {1} killed {2} and did {3} damage]'.format(0, color(nick, light_green), color(player, red), color(int(damage), light_green)))
            await addmoney(nick)
            await addkillstat(nick) 
            await adddeathstat(player)
            await addexp(nick, 25)
            combat.defender.health = 0
            return
        await irc.bot.sendmsg(config.irc.channel, '[Character: {1}] Punched [{2}] and did [{3}] damage!'.format(0, color(nick, light_green), color(player, red), color(int(damage), green)))
 

        c.execute(f'''UPDATE USERS set HEALTH = (:health) where NAME = (:name)''', {'health': combat.defender.health, 'name': combat.defender.name})
 
        conn.commit()
       
async def profile(nick):
    
    name = nick
    check = await checkexist(nick)
    
    if check != True:
        await irc.bot.sendmsg(config.irc.channel, f'[{color("Player does not exist",red)}!]')
        return
    try:
        c.execute(f"SELECT * FROM users WHERE name=(:name)", {'name': nick})
        reg = c.fetchall()
        for regs in reg:
              name = regs[0]
              level = regs[1]
              experience = regs[2]
              health = regs[3]
              attack = regs[4]
              defense = regs[5]
              money = regs[6]
              healthmax = regs[7]
              kills = regs[8]
              deaths = regs[9]
        c.execute(f'SELECT * FROM users WHERE name=(:name)', {'name': name})
        grabstats=c.fetchall()
        for stats in grabstats:
            kills = stats[8]
            deaths = stats[9]
        await irc.bot.sendmsg(config.irc.channel, f'[Player: {color(name, light_green)}] [Level: {color(level, red)}] [Experience: {color(experience, blue)}] [Health: {color(health, light_green)}/{color(healthmax, green)}] [Att/Def: {color(attack, light_green)}/{color(defense, red)}] [Money: {color(money, light_blue)}] [Kills: {color(kills, light_blue)}] [Deaths: {color(deaths, red)}]')
 
    except Exception as ex:
       print('Error {0}'.format(0, ex))
       #bot.sendmsg(config.irc.channel, '[Error: No Such User]')

async def revive(nick):
    check = await checkexist(nick)
    if check != True:
        return
     
    c.execute("SELECT * FROM users WHERE name=(:name)", {'name': nick})

    checkhealth=c.fetchall()

    for amount in checkhealth:
        health = amount[3]
        max = amount[7]
        if health <= 0:
            c.execute("UPDATE USERS set HEALTH = (:health) WHERE NAME = (:name)", {'health': max, 'name': nick})
            logging.debug('test')
            conn.commit()
            return f'[Player {color(nick,light_green)} has been revived!]'
        else:
            return f'[You are not DEAD! No reviving the living!]'


async def getmoney(nick):
    c.execute(f"SELECT * FROM users WHERE name=(:name)", {'name': nick})
    moneygrab = c.fetchall()
    for money in moneygrab:
        moneyamount = money[6]
        writemoney = f'{moneyamount:,}'
        await irc.bot.sendmsg(config.irc.channel, f'[Bank Balance: ${color(writemoney, light_blue)}]')
async def getbandages(nick):
    name = nick
    c.execute(f'SELECT rowid FROM items WHERE name=(:name)', {'name': nick})
    data=c.fetchone()
    if data is None:
        bandages = 0
        c.execute(f'INSERT OR REPLACE INTO items VALUES (:name, :bandages)', {'name': name, 'bandages': bandages})
        conn.commit()
    c.execute(f"SELECT * FROM items WHERE name=(:name)", {'name': nick})
    bandages = c.fetchall()
    for bandage in bandages:
        bandageamount = bandage[1]
        if bandageamount == None:
            logging.debug('test')
            bandageamount = 0
        writebandageamount = f'{bandageamount:,}'
        await irc.bot.sendmsg(config.irc.channel, f'[Bandages: {color(writebandageamount, red)}]')
        
async def ammo(nick):
    c.execute(f'SELECT rowid FROM users WHERE name=(:name)', {'name': nick})
    exist = c.fetchone()
    
    if exist is None:
        await irc.bot.sendmsg(config.irc.channel, f'[User {nick} does not have an account!]')
        return
    c.execute(f"SELECT * FROM weapons WHERE name=(:name)", {'name': nick})
    checkammo = c.fetchall()
    
    for ammo in checkammo:
        hasweapon =  ammo[1]
        if hasweapon == False:
            await irc.bot.sendmsg(config.irc.channel, f'[You do not currently have a weapon.. !buy weapon]')
            return
        ammoclipcount = ammo[2]
        ammomagcount = ammo[3]
    await irc.bot.sendmsg(config.irc.channel, f"[Ammo Count] [Current Clip Holding: {ammoclipcount}] [Arsenal Magazine Rounds: {ammomagcount}]")       
async def addmoney(nick):
    c.execute(f"SELECT * FROM users WHERE name=:name", {'name': nick})
    
    moneygrab = c.fetchall()
    
    for money in moneygrab:
        moneyamount = money[6]
        profit = 500
        moneyamount += profit
        moneyamountformat = f'{moneyamount:,}'
        c.execute(f'''UPDATE USERS set MONEY = (:money) where NAME = (:name)''', {'money': moneyamount, 'name': nick})
        conn.commit()
                           
        return f'[You gained ${color(profit, blue)}!] [Bank Balance: ${color(moneyamountformat, light_blue)}]'
                   
                                         
    

