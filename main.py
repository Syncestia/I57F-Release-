import discord, asyncio, configparser, time, pickle, threading, random

client = discord.Client()

def to_bool(check): # just a simple function, mostly for reading from a config.
    if check in ["True", 1]:
        return True
    return False

def try_load(file, default): # my staple function
    try:
        return pickle.load(open(file, "rb")) # return the loaded file no problems
    except FileNotFoundError:
        pickle.dump(default, open(file, "wb")) # CREATE the file before
        return default # just returning what it was given, lol. It doesn't really matter creating the file here anymore, since I don't load it apart from saving.

def usave():
    pickle.dump(users, open("users.data", "wb"))
def ssave():
    pickle.dump(servers, open("servers.data", "wb"))
def csave():
    pickle.dump(covenants, open("covenants.data", "wb"))

def lprint(what):
    for item in what:
        print(item)

def dprint(what):
    debug = to_bool(cfg['meta']['debug'])
    if isinstance(what, list) or isinstance(what, tuple):
        if debug:
            lprint(what)
    else:
        if debug:
            print(what)

def longest(array, dimensions=1):
    check = [0,]*dimensions
    
    if isinstance(array[0], str):
        for thing in array:
            if len(str(thing)) > check[0]:
                check[0] = len(thing)
        return check[0]
    elif isinstance(array[0], list):
        for i in range(len(array)):
            for x in array[i]:
                if len(str(x)) > check[i]:
                    check[i] = len(str(x))
        return check
    else:
        print("What.")

def check_permissions(message, permissions):
    if permissions == []:
        return True
    if message.author.id == meta.owner_id:
        return True
    for permission in permissions:
        if eval("message.author.guild_permissions.{0}".format(permission)):
            return True
    return False

def convert_mention(mention):
    try:
        mention = mention.lstrip("<@!>")
        mention = int(mention)
        return mention
    except:
        return False

def convert_name(name):
    for user in users:
        if users[user].name == name:
            return user
    return False

def find_covenant(ID):
    try:
        for covenant in covenants:
            if covenant.name == users[ID].covenant:
                return covenant
    except KeyError:
        return "User doesn't exist!"
    return False

class data:
    def __init__(self):
        self.hidden_type = ""

    def update(self):
        if self.hidden_type == "u":
            test_user = user()
        elif self.hidden_type == "s":
            test_user = server()
        elif self.hidden_type == "c":
            test_user = covenant()
        else:
            pass

        needed = False
        for attr, value in test_user.__dict__.items():
            try:
                eval("self.{0} = self.{1}".format(attr, attr))
            except NameError:
                eval("self.{0} = {1}".format(attr, value))
                needed = True
        
        return needed

class user(data):
    def __init__(self, name="test"):
        self.hidden_type = "u"
        self.name = name
        self.bot_launches = 1
        self.messages = 0
        self.faith = 0
        
        self.covenant = "Wifey"
        self.tier = 0
        self.pledged = 0
        self.tier_cost = 5
    
class server(data):
    def __init__(self):
        self.hidden_type = "s"
        self.bot_launches = 1
        self.prefix = "~"
        self.blacklist = []
        self.whitelist = []

class covenant(data):
    def __init__(self, name="test", owner="test"):
        self.hidden_type = "c"
        self.hidden_stimulate = []
        self.hidden_members = []
        self.name = name
        self.leader = False
        self.owner = owner
    
    def check_leader(self):
        check = [0, 0]
        winner = 0
        for member in self.hidden_members:
            if users[member].tier_cost > check[0]:
                check[1] = users[member].pledged
                winner = member
            elif users[member].tier_cost == check[0]:
                if users[member].pledged > check[1]:
                    check[1] = users[member].pledged
                    winner = member
        if winner == 0:
            print("There is nobody in %s covenant."%self.name)
            return
        if check == [0, 0]:
            print("Nobody has pledged to %s covenant!"%self.name)
            return
        print(users[member].name, member, "is the leader of this covenant!")
        self.leader = [users[member].name, member]

class command:
    def __init__(self, name, permissions=[], subcommands={}, arguments=[]):
        self.name = name
        self.run = eval(name)
        self.permissions = permissions
        self.arguments = arguments
        self.subcommands = subcommands

class meta:
    def __init__(self):
        self.owner_id = int(cfg['meta']['owner_id'])
        self.ready = False
        self.messages = 0

users = try_load("users.data", {})
servers = try_load("servers.data", {})
covenants = try_load("covenants.data", {})
cmds = {}
cfg = configparser.ConfigParser()
cfg.read("config.ini")

def update_data(client):
    values = [0,0,0,0]
    for guild in client.guilds:
        try:
            servers[guild.id].bot_launches += 1
            values[0] += 1
        except KeyError:
            servers[guild.id] = server()
            values[1] += 1
        for member in guild.members:
            try:
                users[member.id].bot_launches += 1
                values[2] += 1
            except KeyError:
                users[member.id] = user(name=member.name)
                values[3] += 1
    return values

def load_cmds():
    load = [
        ["mimic"],
        ["stats", [], {"covenant":check_covenant}],
        ["stimulate"],
        ["admin", ["manage_guild"], {"blacklist":blacklist, "whitelist":whitelist}]
    ]
    for cmd in load:
        while len(cmd) != 4:
            cmd.append([])
        cmds[cmd[0]] = command(cmd[0], permissions=cmd[1], subcommands=cmd[2], arguments=cmd[3])
        print("{0} LOADED.".format(cmd[0]))

def default_covenants():
    load = [
        ["wifey"],
    ]
    for c in load:
        covenants[c[0]] = covenant(name=c[0].capitalize(), owner=[users[540426841203146754].name, 540426841203146754])
    stimulates = {
        "wifey": [
            ["You feel nothing but pain.", "Your soul reacts with hatred, but only because it knows something is there", "A slight glow emits from your soul"],
            ["A slight warmth fills you with joy.", "The pain is almost gone. There is something out there stopping it", "Your chest glows with the power of your faith"]
        ],
    }
    for c in covenants:
        covenants[c].hidden_stimulate = stimulates[c]
    csave()

def passive_generation():
    tick = 0
    notification_limiter = 1
    while True:
        time.sleep(5)
        for user in users:
            users[user].faith += 0.001*(users[user].tier+1)
        if tick % 20*notification_limiter == 0:
            print("FAITH TICK COMPLETED SUCCESSFULLY")
            notification_limiter += 1
        tick += 1

@client.event
async def on_ready():
    print("CONNECTED")
    stats = update_data(client)
    load_cmds()
    if covenants == {}:
        default_covenants()
    lprint([
        ("%s NEW SERVERS"%stats[0]),
        ("%s OLD SERVERS"%stats[1]),
        ("%s NEW USERS"%stats[2]),
        ("%s OLD USERS"%stats[3]),
        ("-"*25),
        ("NOW READY"),
    ])
    threading.Thread(name="z", target=passive_generation).start()
    meta.ready = True

@client.event
async def on_message(message):
    if not meta.ready or client.user.id == message.author.id:
        return
    
    print("{0}: {1}".format(message.author.name, message.content))
    try:
        users[message.author.id].messages += 1
    except:
        users[message.author.id] = user(name=message.author.name)

    server = servers[message.guild.id]

    if message.content.startswith(server.prefix) and message.content[1] != "~":
        if server.whitelist != []:
            if message.channel.id not in server.whitelist:
                return
        if server.blacklist != []:
            if message.channel.id in server.blacklist:
                return
        print("COMMAND SEEN IN SERVER {0}".format(message.guild.name))
        message.nonce = message.content[len(server.prefix):]
        await command_parse(message)
    
    if meta.messages % 2 == 0:
        usave()

async def command_parse(message):
    split = message.nonce.split()
    for cmd in cmds:
        if message.nonce.startswith(cmd):
            if not check_permissions(message, cmds[cmd].permissions):
                await message.channel.send("You do not have the permissions to use this command!")
                return
            try:
                for x in cmds[cmd].subcommands:
                    if x.startswith(split[1]):
                        await cmds[cmd].subcommands[x](message)
                        return
            except IndexError:
                pass
            await cmds[cmd].run(message)
            return
    await message.channel.send("`You {0}, sure.`".format(message.nonce))

async def mimic(message):
    message.nonce = message.nonce[6:] # mimic is static i guess
    await message.channel.send(message.nonce)

async def stats(message):
    reply = "```ini\n"
    check = [[],[]]

    try:
        message.author.id = int(message.nonce[5:])
    except IndexError:
        pass
    except ValueError:
        x = convert_name(message.nonce[5:])
        y = convert_mention(message.nonce[5:])
        if x:
            message.author.id = x
        elif y:
            message.author.id = y
        else:
            pass

    for attr, value in users[message.author.id].__dict__.items():
        if attr.startswith("hidden_"):
            continue
        if isinstance(value, float):
            value = "{0:.2f}".format(value)
        check[0].append(attr)
        check[1].append(value)
    print(check)
    check = longest(check, 2)
    for attr, value in users[message.author.id].__dict__.items():
        if attr.startswith("hidden_"):
            continue
        attr = attr.capitalize()
        attr = attr.replace("_", " ")
        add = "[ {:%d} ] ; {:>%d}\n"%(check[0], check[1])
        if isinstance(value, float):
            value = "{0:.2f}".format(value)
        add = add.format(attr, str(value))
        reply += add
    reply += "```"
    await message.channel.send(reply)
async def check_covenant(message):
    reply = "```ini\n"
    check = [[],[]]
    try:
        c = covenants[message.nonce.split()[2]]
    except KeyError:
        await message.channel.send("Covenant does not exist!")
    for attr, value in c.__dict__.items():
        if attr.startswith("hidden_"):
            continue
        if attr.startswith("owner"):
            value = value[0]
        check[0].append(attr)
        check[1].append(value)
    print(check)
    check = longest(check, 2)
    for attr, value in c.__dict__.items():
        if attr.startswith("hidden_"):
            continue
        if attr.startswith("owner"):
            value = value[0]
        attr = attr.capitalize()
        attr = attr.replace("_", " ")
        add = "[ {:%d} ] ; {:>%d}\n"%(check[0], check[1])
        add = add.format(attr, str(value))
        reply += add
    reply += "```"
    await message.channel.send(reply)

async def stimulate(message):
    rng = random.randint(1, 25)
    bas = rng//10
    bbs = bas + 1
    punct = ["", ",", "."]
    tier = users[message.author.id].tier
    z = bbs * (tier + 1)
    try:
        c_message = find_covenant(message.author.id).hidden_stimulate[tier][bas]
    except IndexError:
        c_message = find_covenant(message.author.id).hidden_stimulate[-1][bas]
    reply = "{0}{1} {2} {3}".format(c_message, punct[bas], message.author.mention, ("*"*bbs)+"B"+("Z"*z)+"T"+("*"*bbs))
    users[message.author.id].faith += (0.005*(tier+1))*rng/10
    await message.channel.send(reply)

async def pledge(message):
    split = message.nonce.split()
    user = users[message.author.id]
    try:
        amount = int(split[1])
    except (IndexError, ValueError):
        await message.channel.send("`{0} faith needed for next tier in covenant {1}.` {2}".format(user.tier_cost, user.covenant, message.author.mention))
        return
    if user.faith - amount < 0:
        await message.channel.send("`You do not have enough faith for this pledge.` {0}".format(message.author.mention))
        return
    users[message.author.id].faith -= amount
    users[message.author.id].pledged += amount
    complete = 0
    increase = 0
    while not complete:
        if user.pledged > user.tier_cost:
            users[message.author.id].tier += 1
            increase += 1
            users[message.author.id].tier_cost *= (users[message.author.id].tier_cost/2)
            users[message.author.id].pledged -= user.tier_cost
        else:
            complete = 1
    await message.channel.send("`{0} faith pledged to {1}. You have gone up {2} tiers.`".format(amount, user.covenant, increase))
    covenants[user.covenant].check_leader()

async def admin(message):
    await message.channel.send("You don't use the command like this.")
async def whitelist(message):
    split = message.nonce.split()
    try:
        new = int(split[3])
    except:
        await message.channel.send("You didn't give an ID to whitelist!")
        return
    if split[2] == "add":
        if new in servers[message.guild.id].whitelist:
            await message.channel.send("`This channel is already whitelisted.`")
            return
        servers[message.guild.id].whitelist.append(new)
        what = "added"
    elif split[2] == "remove":
        if new not in servers[message.guild.id].whitelist:
            await message.channel.send("`This channel is not whitelisted.`")
            return
        servers[message.guild.id].whitelist.remove(new)
        what = "removed"
    else:
        await message.channel.send("`Invalid syntax.`")
    await message.channel.send("`{0} {1} to the server's channel whitelist.`".format(new, what))
    ssave()
async def blacklist(message):
    split = message.nonce.split()
    try:
        new = int(split[3])
    except:
        await message.channel.send("You didn't give an ID to blacklist!")
        return
    if split[2] == "add":
        if new in servers[message.guild.id].blacklist:
            await message.channel.send("`This channel is already blacklisted.`")
            return
        servers[message.guild.id].blacklist.append(new)
        what = "added"
    elif split[2] == "remove":
        if new not in servers[message.guild.id].blacklist:
            await message.channel.send("`This channel is not blacklisted.`")
            return
        servers[message.guild.id].blacklist.remove(new)
        what = "removed"
    else:
        await message.channel.send("`Invalid syntax.`")
    await message.channel.send("`{0} {1} to the server's channel blacklist.`".format(new, what))
    ssave()

def start():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(client.start(cfg['meta']['token'], bot=to_bool(cfg['meta']['bot'])))
    except KeyboardInterrupt:
        loop.run_until_complete(client.logout())
    finally:
        loop.close()

meta = meta()

if __name__ == "__main__":
    start()
