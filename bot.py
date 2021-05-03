#████████╗██╗    ██╗██╗████████╗ ██████╗██╗  ██╗     ██████╗██╗  ██╗ █████╗ ████████╗██████╗  ██████╗ ████████╗
#╚══██╔══╝██║    ██║██║╚══██╔══╝██╔════╝██║  ██║    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝██╔══██╗██╔═══██╗╚══██╔══╝
#   ██║   ██║ █╗ ██║██║   ██║   ██║     ███████║    ██║     ███████║███████║   ██║   ██████╔╝██║   ██║   ██║   
#   ██║   ██║███╗██║██║   ██║   ██║     ██╔══██║    ██║     ██╔══██║██╔══██║   ██║   ██╔══██╗██║   ██║   ██║   
#   ██║   ╚███╔███╔╝██║   ██║   ╚██████╗██║  ██║    ╚██████╗██║  ██║██║  ██║   ██║   ██████╔╝╚██████╔╝   ██║   
#   ╚═╝    ╚══╝╚══╝ ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═════╝  ╚═════╝    ╚═╝                                                                                                             

import yaml
from twitchio.ext import commands
from datetime import datetime
from random import randint
from commands import Commands

#Reads auth data
def read_auth():
    with open('config/auth.yml') as f_auth:
        data = yaml.load(f_auth, Loader=yaml.FullLoader)
        bot_username = data.get('bot-name')
        irc_token = data.get('auth-id')
        client_id = data.get('client-id')
        client_secret = data.get('client-secret')
        cmd_prefix = data.get('cmd-prefix')
        channel = data.get('channel')
    return (bot_username, irc_token, client_id, client_secret, cmd_prefix, channel)


#Reads config
def read_broadcasts():
    with open('config/broadcasts.yml') as f_broadcasts:
        data = yaml.load(f_broadcasts, Loader=yaml.FullLoader)
        broadcasts = data.get('broadcasts')
    return broadcasts


broadcasts = read_broadcasts()

# Main Twitch Bot Class
class Bot(commands.Bot):
    cmds_on_cooldown = dict()
    n_current = 0

    # called when creating the Bot()
    def __init__(self):

        # Reads config and stores the variables
        self.auth_data = read_auth() # auth_data = (bot_username, irc_token, client_id, client_secret, cmd_prefix, channel)
        self.bot_username = self.auth_data[0]
        self.irc_token = self.auth_data[1]
        self.client_id = self.auth_data[2]
        self.client_secret = self.auth_data[3]
        self.cmd_prefix = self.auth_data[4]
        self.channel = self.auth_data[5]

        # calls the twitchio library's superclass bot
        super().__init__(
            nick = self.bot_username,
            irc_token = self.irc_token,
            client_id = self.client_id,
            client_secret = self.client_secret,
            prefix = self.cmd_prefix,
            initial_channels = [self.channel]
        )

        # creating the custom command library
        self.bot_commands = Commands('config/commands.yml', self.cmd_prefix)

    # On bot startup
    async def event_ready(self):
        print(f'\nBot: {self.bot_username}')
        print(f'Channel: {self.channel}')
        print('Connected!\n')
        ws = bot._ws
        await ws.send_privmsg(self.channel, f"/me is online")
        await bot.http.generate_token()

    # Everytime a message is sent in the chat
    async def event_message(self, message):
        if message.author.name == self.bot_username: return # ignores itself
        await self.bot_commands.handler(message, await self.get_context(message))
        await self.handle_broadcast(message)

    async def handle_broadcast(self, message):

        # ignores commands to prevent bot from spamming messages
        if message.content.startswith(self.cmd_prefix): return

        # whenever a message is sent, theres a 1/15 chance a broadcast is sent
        if randint(1,15) == 3:
            ws = bot._ws

            # loops through the broadcasts in the 'broadcast.yml' sending a broadcast
            await ws.send_privmsg(self.channel, f'/me {broadcasts[self.n_current]}')
            if self.n_current >= (len(broadcasts)-1): self.n_current = 0
            else: self.n_current +=1
        return

# creates and runs the bot
bot = Bot()
bot.run()
