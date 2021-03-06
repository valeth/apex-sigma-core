# Apex Sigma: The Database Giant Discord Bot.
# Copyright (C) 2018  Lucia's Cipher
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

import copy
import secrets

import discord

interaction_cache = {}


async def update_id(db, interaction):
    new_id = secrets.token_hex(4)
    new_data = copy.deepcopy(interaction)
    new_data.update({'ReactionID': new_id})
    await db[db.db_cfg.database]['Interactions'].update_one(interaction, {'$set': new_data})


async def get_interaction_list(db, intername):
    return await db[db.db_cfg.database]['Interactions'].find({'Name': intername}).to_list(None)


async def grab_interaction(db, intername):
    if intername not in interaction_cache:
        fill = True
    else:
        if not interaction_cache[intername]:
            fill = True
        else:
            fill = False
    if fill:
        interactions = await get_interaction_list(db, intername)
        refill = False
        for interaction in interactions:
            inter_id = interaction.get('ReactionID')
            if not inter_id:
                await update_id(db, interaction)
                refill = True
        if refill:
            interactions = await get_interaction_list(db, intername)
        interaction_cache.update({intername: interactions})
    if interaction_cache[intername]:
        choice = interaction_cache[intername].pop(secrets.randbelow(len(interaction_cache[intername])))
    else:
        choice = {'URL': 'https://i.imgur.com/m59E4nx.gif', 'UserID': None, 'ServerID': None, 'ReactionID': None}
    return choice


def target_check(x, lookup):
    return x.display_name.lower() == lookup.lower() or x.name.lower() == lookup.lower()


def get_target(message):
    if message.mentions:
        target = message.mentions[0]
    else:
        if message.content:
            lookup = ' '.join(message.content.split(' ')[1:])
            target = discord.utils.find(
                lambda x: target_check(x, lookup), message.guild.members)
        else:
            target = None
    return target


def make_footer(cmd, item):
    uid = item.get('UserID')
    user = discord.utils.find(lambda x: x.id == uid, cmd.bot.get_all_members())
    if user:
        username = user.name
    else:
        username = 'Unknown User'
    sid = item.get('ServerID')
    srv = discord.utils.find(lambda x: x.id == sid, cmd.bot.guilds)
    if srv:
        servername = srv.name
    else:
        servername = 'Unknown Server'
    react_id = item.get('ReactionID')
    footer = f'[{react_id}] | Submitted by {username} from {servername}.'
    return footer
