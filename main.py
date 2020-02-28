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
    for permission in permissions:
        if eval("message.author.guild_permissions.{0}".format(permission)):
            return True
    return False

class data:
    def __init__(self):
        self.bot_launches = 1 # easy

    def update(self):
        test_user = user()

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
        self.name = name
        self.bot_launches = 1
        self.messages = 0
        
        self.tier = 0
        self.faith = 0
    
class server(data):
    def __init__(self):
        self.bot_launches = 1
        self.prefix = "~"
        self.blacklist = []
        self.whitelist = []

class command:
    def __init__(self, name, permissions=[], subcommands={}, arguments=[]):
        self.name = name
        self.run = eval(name)
        self.permissions = permissions
        self.arguments = arguments
        self.subcommands = subcommands

class meta:
    def __init__(self):
        self.owner_id = cfg['meta']['owner_id']
        self.ready = False
        self.messages = 0
        self.stimulate = [
            ["A jolt! But not strong enough to start anything.", "The weakest of resonance is felt in your heart", "You feel a warm tingle in your soul"]
        ]

users = try_load("users.data", {})
servers = try_load("servers.data", {})
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
        ["stats"],
        ["stimulate"],
        ["admin", ["manage_guild"], {"blacklist":blacklist, "whitelist":whitelist}]
    ]
    for cmd in load:
        while len(cmd) != 4:
            cmd.append([])
        cmds[cmd[0]] = command(cmd[0], permissions=cmd[1], subcommands=cmd[2], arguments=cmd[3])
        print("{0} LOADED.".format(cmd[0]))

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
        pass # who cares

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
            for x in cmds[cmd].subcommands:
                if x.startswith(split[1]):
                    await cmds[cmd].subcommands[x](message)
                    return
            await cmds[cmd].run(message)
            return
    await message.channel.send("`You {0}, sure.`".format(message.nonce))

async def mimic(message):
    message.nonce = message.nonce[6:] # mimic is static i guess
    await message.channel.send(message.nonce)

async def stats(message):
    reply = "```ini\n"
    check = [[],[]]
    for attr, value in users[message.author.id].__dict__.items():
        check[0].append(attr)
        check[1].append(value)
    print(check)
    check = longest(check, 2)
    for attr, value in users[message.author.id].__dict__.items():
        attr = attr.capitalize()
        attr = attr.replace("_", " ")
        add = "[ {:%d} ] ; {:>%d}\n"%(check[0], check[1])
        add = add.format(attr, value)
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
    reply = "{0}{1} {2} {3}".format(meta.stimulate[tier][bas], punct[bas], message.author.mention, ("*"*bbs)+"B"+("Z"*z)+"T"+("*"*bbs))
    users[message.author.id].faith += (0.005*(tier+1))*rng/10
    await message.channel.send(reply)

async def admin(message):
    await message.channel.send("You don't use the command like this.")

async def whitelist(message):
    try:
        new = int(message.content.split()[2])
    except:
        await message.channel.send("You didn't give an ID to blacklist!")
        return
    servers[message.guild.id].whitelist.append(new)
    await message.channel.send("`{0} added to the server's channel whitelist.`".format(new))

async def blacklist(message):
    try:
        new = int(message.content.split()[2])
    except:
        await message.channel.send("You didn't give an ID to blacklist!")
        return
    servers[message.guild.id].blacklist.append(new)
    await message.channel.send("`{0} added to the server's channel blacklist.`".format(new))

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