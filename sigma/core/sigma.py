import errno
import os
import shutil
import arrow
import discord
import pymongo

from sigma.core.mechanics.config import configuration
from sigma.core.mechanics.config import information
from sigma.core.mechanics.logger import create_logger
from sigma.core.mechanics.cooldown import CooldownControl
from sigma.core.mechanics.database import Database
from sigma.core.mechanics.music import MusicCore
from sigma.core.mechanics.plugman import PluginManager
from sigma.core.mechanics.threading import QueueControl

# Apex Sigma: The Database Giant Discord Bot.
# Copyright (C) 2017  Lucia's Cipher
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# I love spaghetti!
# Valebu pls, no take my spaghetti... :'(

init_cfg = configuration()

if init_cfg.dsc.bot:
    client_class = discord.AutoShardedClient
else:
    client_class = discord.Client


class ApexSigma(client_class):
    def __init__(self):
        super().__init__()
        self.ready = False
        # State attributes before initialization.
        self.cfg = init_cfg
        self.queue = QueueControl()
        self.launched = False
        self.cache = {}
        # Initialize startup methods and attributes.
        self.create_cache()

        self.log = create_logger('Sigma')
        self.log.info('---------------------------------')
        self.log.info(f'Running as a Bot: {self.cfg.dsc.bot}')
        self.log.info(f'Default Bot Prefix: {self.cfg.pref.prefix}')
        self.log.info('---------------------------------')
        self.db = Database(self, self.cfg.db)
        self.log.info('---------------------------------')
        self.cool_down = CooldownControl(self)
        self.log.info('---------------------------------')
        self.music = MusicCore(self)
        self.log.info('---------------------------------')
        self.info = information()
        self.modules = PluginManager(self, init=True)

        self.start_time = arrow.utcnow()
        self.message_count = 0
        self.command_count = 0

    @staticmethod
    def create_cache():
        if os.path.exists('cache'):
            shutil.rmtree('cache')
        os.makedirs('cache')

    def get_prefix(self, message):
        prefix = self.cfg.pref.prefix
        if message.guild:
            pfx_search = self.db.get_guild_settings(message.guild.id, 'Prefix')
            if pfx_search:
                prefix = pfx_search
        return prefix

    def run(self):
        try:
            self.log.info('Connecting to Discord Gateway...')
            super().run(self.cfg.dsc.token, bot=self.cfg.dsc.bot)
        except discord.LoginFailure:
            self.log.error('Invalid Token!')
            exit(errno.EPERM)

    async def event_runner(self, event_name, *args):
        if event_name in self.modules.events:
            for event in self.modules.events[event_name]:
                # self.loop.create_task(event.execute(*args))
                task = event, *args
                await self.queue.queue.put(task)

    async def on_connect(self):
        event_name = 'connect'
        if event_name in self.modules.events:
            for event in self.modules.events[event_name]:
                self.loop.create_task(event.execute())

    async def on_shard_ready(self, shard_id):
        self.log.info(f'Connection to Discord Shard #{shard_id} Established')
        event_name = 'shard_ready'
        self.loop.create_task(self.event_runner(event_name, shard_id))

    async def on_ready(self):
        self.ready = True
        self.log.info('---------------------------------')
        self.log.info('Apex Sigma Fully Loaded and Ready')
        self.log.info('---------------------------------')
        self.log.info(f'User Account: {self.user.name}#{self.user.discriminator}')
        self.log.info(f'User Snowflake: {self.user.id}')
        self.log.info('---------------------------------')
        self.log.info('Launching On-Ready Modules...')
        self.loop.create_task(self.event_runner('ready'))
        if not self.launched:
            self.loop.create_task(self.event_runner('launch'))
            self.launched = True
        self.log.info('All On-Ready Module Loops Created')
        self.log.info('---------------------------------')

    def get_cmd_and_args(self, message, args, mention=False):
        args = list(filter(lambda a: a != '', args))
        if mention:
            if args:
                cmd = args.pop(0).lower()
            else:
                cmd = None
        else:
            cmd = args.pop(0)[len(self.get_prefix(message)):].lower()
        return cmd, args

    def clean_self_mentions(self, message):
        for mention in message.mentions:
            if mention.id == self.user.id:
                message.mentions.remove(mention)
                break

    async def on_message(self, message):
        self.message_count += 1
        if not message.author.bot:
            event_name = 'message'
            self.loop.create_task(self.event_runner(event_name, message))
            if self.user.mentioned_in(message):
                event_name = 'mention'
                self.loop.create_task(self.event_runner(event_name, message))
            prefix = self.get_prefix(message)
            if message.content.startswith(prefix):
                args = message.content.split(' ')
                cmd, args = self.get_cmd_and_args(message, args)
            elif message.content.startswith(self.user.mention):
                args = message.content.split(' ')[1:]
                self.clean_self_mentions(message)
                cmd, args = self.get_cmd_and_args(message, args, mention=True)
            elif message.content.startswith(f'<@!{self.user.id}>'):
                args = message.content.split(' ')[1:]
                cmd, args = self.get_cmd_and_args(message, args, mention=True)
            else:
                cmd = None
                args = []
            if cmd:
                if cmd in self.modules.alts:
                    cmd = self.modules.alts[cmd]
                if cmd in self.modules.commands:
                    command = self.modules.commands[cmd]
                    # self.loop.create_task(command.execute(message, args))
                    task = command, message, args
                    await self.queue.queue.put(task)

    async def on_message_edit(self, before, after):
        if not before.author.bot:
            event_name = 'message_edit'
            self.loop.create_task(self.event_runner(event_name, before, after))

    async def on_message_delete(self, message):
        if not message.author.bot:
            event_name = 'message_delete'
            self.loop.create_task(self.event_runner(event_name, message))

    async def on_member_join(self, member):
        if not member.bot:
            event_name = 'member_join'
            self.loop.create_task(self.event_runner(event_name, member))

    async def on_member_remove(self, member):
        if not member.bot:
            event_name = 'member_remove'
            self.loop.create_task(self.event_runner(event_name, member))

    async def on_member_update(self, before, after):
        if not before.bot:
            event_name = 'member_update'
            self.loop.create_task(self.event_runner(event_name, before, after))

    async def on_guild_join(self, guild):
        event_name = 'guild_join'
        self.loop.create_task(self.event_runner(event_name, guild))

    async def on_guild_remove(self, guild):
        event_name = 'guild_remove'
        self.loop.create_task(self.event_runner(event_name, guild))

    async def on_voice_state_update(self, member, before, after):
        event_name = 'voice_state_update'
        self.loop.create_task(self.event_runner(event_name, member, before, after))
