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

import operator

import discord
from humanfriendly.tables import format_pretty_table as boop

from sigma.core.mechanics.command import SigmaCommand


async def ingame(cmd: SigmaCommand, message: discord.Message, args: list):
    games = {}
    online_count = 0
    playing_count = 0
    total_count = 0
    for member in message.guild.members:
        total_count += 1
        status = str(member.status)
        if status != 'offline':
            online_count += 1
        if not member.bot:
            if member.activity:
                game_name = member.activity.name
                repl_name = game_name.replace(' ', '')
                if repl_name != '':
                    playing_count += 1
                    if game_name not in games:
                        games.update({game_name: 1})
                    else:
                        curr_count = games[game_name]
                        new_count = curr_count + 1
                        games.update({game_name: new_count})
    embed = discord.Embed(color=0x1ABC9C)
    sorted_games = sorted(games.items(), key=operator.itemgetter(1))
    if args:
        page = args[0]
        try:
            page = int(page)
        except ValueError:
            page = 1
    else:
        page = 1
    if page < 1:
        page = 1
    start_range = 5 * (page - 1)
    end_range = 5 * page
    out_table_list = []
    game_count = len(sorted_games)
    n = 0
    for key, value in list(reversed(sorted_games))[start_range:end_range]:
        n += 1
        index = n + start_range
        if len(key) > 32:
            key = key[:32] + '...'
        out_table_list.append(
            [str(index), key.title(), value, str(((value / playing_count) * 10000) // 100).split('.')[0] + '%'])
    out = boop(out_table_list)
    general_stats_list = [['Online', online_count], ['In-Game', playing_count], ['Unique Games', game_count]]
    general_stats_out = boop(general_stats_list)
    embed.add_field(name='👾 Current Gaming Statistics on ' + message.guild.name,
                    value='```hs\n' + general_stats_out + '\n```', inline=False)
    embed.add_field(name=f'🎮 By Game on Page {page}', value='```haskell\n' + out + '\n```', inline=False)
    await message.channel.send(None, embed=embed)
