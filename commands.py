#  ██████╗ ██████╗ ███╗   ███╗███╗   ███╗ █████╗ ███╗   ██╗██████╗ ███████╗
# ██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝
# ██║     ██║   ██║██╔████╔██║██╔████╔██║███████║██╔██╗ ██║██║  ██║███████╗
# ██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║  ██║╚════██║
# ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝███████║
#  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝
                                                                          
import yaml
from twitchio.ext import commands
import datetime
import asyncio

#prevents serializing aliases to config files
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

#Commands class
class Commands:

    # init
    def __init__(self, file_path, cmd_prefix):
        self.config_file = file_path # config file location
        self.simple_cmds = self.read_config('simple-commands') # loads simple commands from config file
        self.triggers = [trigger for trigger in self.simple_cmds.keys() if not self.simple_cmds[trigger].get('prefix')] # gets all commands that doesnt require a prefix
        self.default = self.read_config('default') # the default values when creating a command
        self.cmds_on_cooldown = dict()  # cmds_on_cooldown = { cmd_label: available_time}
        self.smart_cmds = self.read_config('smart-commands') # loads smart commands from config file
        self.cmd_prefix = cmd_prefix # refereces command prefix (ex. '!')

    # gets data from config file
    def read_config(self, section):
        # opens the config file 
        with open(self.config_file) as f_cmds:

            # gets all data
            data = yaml.load(f_cmds, Loader=yaml.FullLoader)

            # returns specified section
            return data.get(section)
    
    # updates the config file
    def update_config(self):

        # opens the config file
        with open(self.config_file, 'w') as f_cmds:

            # data to be written to file
            updated_cmds_yml = {
                'default': self.default,
                'simple-commands': self.simple_cmds,
                'smart-commands': self.smart_cmds
            }

            # writes data to file
            yaml.dump(updated_cmds_yml, f_cmds, Dumper=NoAliasDumper)
            self.simple_cmds = self.read_config('simple-commands')

    # adds a new command then upates the config file
    def add_cmd(self, cmd_label: str, response: str = None, cooldown: int = None, prefix: bool = None, roles: list = None, aliases: list = None):
        
        # does nothing if command label not specified
        if cmd_label == None: return

        # uses default values from config if not specified
        if response == None: response = self.default.get('response')
        if cooldown == None: cooldown = self.default.get('cooldown')
        if prefix == None: prefix = self.default.get('prefix')
        if roles == None: roles = self.default.get('roles')

        # adds command to bot
        self.simple_cmds[cmd_label] = {
            'response': response,
            'cooldown': cooldown,
            'prefix': prefix,
            'roles': roles,
            'aliases': aliases
        }

        # updates config with new command
        self.update_config()

        # prints to log
        print(f'Command Added: {cmd_label}')
        print(f'- Data: {self.simple_cmds[cmd_label]}')
    
    # deletes a command then updates the config file
    def del_cmd(self, cmd_label):

        # deletes command
        self.simple_cmds.pop(cmd_label, None)

        # updates the config
        self.update_config()

        # prints to log
        print(f'Command Deleted: {cmd_label}')

    # edits a command
    def edit_cmd(self, cmd_label, tag, value):
        
        # edits command
        self.simple_cmds[cmd_label][tag] = value

        # updates the config
        self.update_config()

        # prints to log
        print(f'Command Edited: {cmd_label}')
        print(f'- Data: {self.simple_cmds[cmd_label]}')

    # gets the command label from the message
    def get_cmd_label(self, message):
        
        # ignores case
        content = message.content.lower()

        # checks for aliases, and converts to 
        # aliases = dict()
        # for key in self.smart_cmds.keys():
        #     key_aliases = self.smart_cmds[key].get('aliases')
        #     if key_aliases:
        #         for alias in key_aliases: aliases[alias] = key

        # if message starts with command prefix
        if content.startswith(self.cmd_prefix): 

            # returns cmd_label if command exists, else returns None
            cmd_label = content.split(' ')[0][1:]
            return cmd_label if cmd_label in self.get_cmd_list() else None

        # checks if theres any trigger word in the message (ex. joe - but must be seperated by spaces)
        listener = [trigger for trigger in self.triggers if trigger in content.split(' ')]

        # returns 1st trigger if trigger exists
        
        if listener: return listener[0]
    
    # returns the cooldown of the command from the config (time in seconds)
    def get_cooldown(self, cmd_label):
        return self.simple_cmds[cmd_label].get('cooldown')

    def get_cmd_type(self, cmd_label):
        
        return

    # checks if the command is on cooldown, and updates the commands cooldown list
    def is_on_cooldown(self, cmd_label):

        # returns false if command was never on cooldown
        if not cmd_label in self.cmds_on_cooldown.keys(): return False

        # gets when the command is allowed to be used
        available_time = self.cmds_on_cooldown.get(cmd_label)

        # returns false if current time is past available time and then removes from cooldown list
        if datetime.datetime.now() > available_time:
            del self.cmds_on_cooldown[cmd_label]
            return False

        # else returns true
        return True
    
    # gets roles of user
    def get_user_roles(self, user):
        roles = ['pleb']
        badges = user._badges
        if 'broadcaster' in badges: roles.append('broadcaster')
        if 'moderator' in badges: roles.append('mod')
        if 'vip' in badges: roles.append('vip')
        if 'subscriber' in badges: roles.append('sub')
        return roles
    
    def has_permission(self, user, cmd_label):
        if not cmd_label in self.simple_cmds.keys(): return False
        user_roles = self.get_user_roles(user)
        if 'broadcaster' in user_roles: return True
        cmd_roles = self.simple_cmds[cmd_label].get('roles')
        mixed = set(cmd_roles) & set(user_roles)
        return True if mixed else False
    
    # gets the response of the command
    def get_response(self, cmd_label):
        # returns the response if command exists, else returns None
        return self.simple_cmds.get(cmd_label).get('response') if cmd_label else None

    # main command handler, if applicable, will return the response
    async def handle_simple_cmds(self, user, cmd_label, ctx):
        if not self.has_permission(user, cmd_label): return None
        if self.is_on_cooldown(cmd_label): return None
        cd = self.get_cooldown(cmd_label)
        available_time = datetime.datetime.now() + datetime.timedelta(seconds=cd)
        self.cmds_on_cooldown[cmd_label] = available_time
        response = self.get_response(cmd_label)
        if response == None: return
        await ctx.send(f'/me {response}')

    # 
    def handle_smart_cmds(self, user, cmd_label):
        return


    async def handler(self, message, ctx):
        user = message.author
        cmd_label = self.get_cmd_label(message)

        if cmd_label == None: return
        await self.handle_simple_cmds(user, cmd_label, ctx)
    
    def get_cmd_list(self):
        return list(self.simple_cmds.keys())
    

