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

import discord

from sigma.core.mechanics.command import SigmaCommand


async def removereaction(cmd: SigmaCommand, message: discord.Message, args: list):
    if args:
        lookup = args[0].lower()
        interaction_item = await cmd.db[cmd.db.db_cfg.database].Interactions.find_one({'ReactionID': lookup})
        if interaction_item:
            await cmd.db[cmd.db.db_cfg.database].Interactions.delete_one(interaction_item)
            response = discord.Embed(color=0, title=f'🔥 Reaction `{lookup}` has been removed.')
        else:
            response = discord.Embed(color=0xBE1931, title=f'❗ Reaction not found.')
    else:
        response = discord.Embed(color=0xBE1931, title=f'❗ Nothing inputted.')
    await message.channel.send(embed=response)
