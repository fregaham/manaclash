# Copyright 2011 Marek Schmidt
# 
# This file is part of ManaClash
#
# ManaClash is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ManaClash is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ManaClash.  If not, see <http://www.gnu.org/licenses/>.
#
# 

class Selector:
    def all (self):
        return []

class AllSelector:
    def all(self, game):
        for item in game.objects.values():
            yield item

class AllTypeSelector:
    def __init__ (self, type):
        self.type = type

    def all (self, game):
        for item in game.objects.values():
            if self.type in item.state.types:
                yield item

class AllPermanentSelector:
    def all(self, game):
         for item in game.objects.values():
            if "permanent" in item.state.tags:
                yield item


class PermanentPlayerControlsSelector(Selector):
    def __init__ (self, player):
        self.player_id = player.id

    def all (self, game):
        for item in game.objects.values():
            if "permanent" in item.state.tags:
                if item.state.controller_id == self.player_id:
                    yield item


