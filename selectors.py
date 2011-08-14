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

from objects import *

class Selector:
    def all (self, game, context):
        return []

    def contains(self, game, context, obj):
        return obj.get_id() in map(lambda x:x.get_id(), self.all(game, context))

    def slots(self):
        return []

    def __str__(self):
        return "selector"

class AllSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            yield item

    def __str__(self):
        return "all"

class AllTypeSelector(Selector):
    def __init__ (self, type):
        self.type = type

    def all (self, game, context):
        for item in game.objects.values():
            if self.type in item.state.types:
                yield item

    def __str__ (self):
        return "all %s" % self.type

class AllPermanentSelector(Selector):
    def all(self, game, context):
         for item in game.objects.values():
            if "permanent" in item.state.tags:
                yield item

    def __str__(self):
        return "all permanents"

class PermanentPlayerControlsSelector(Selector):
    def __init__ (self, player):
        self.player_id = player.id

    def all (self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags:
                if item.state.controller_id == self.player_id:
                    yield item

    def __str__ (self):
        return "permanent player controls"

class AllPlayersSelector(Selector):
    def all(self, game, context):
        for player in game.players:
            yield player

    def slots(self):
        return ["that player"]

    def __str__(self):
        return "all players"

class SelfSelector(Selector):
    def all(self, game, context):
        yield context.get_source_lki()

    def __str__(self):
        return "SELF"
        
class ThatPlayerSelector(Selector):
    def all(self, game, context):
        player_lki = context.get_slot("that player")
        assert player_lki is not None
        yield player_lki

    def __str__ (self):
        return "that player"

class ThatCreatureSelector(Selector):
    def all(self, game, context):
        creature_lki = context.get_slot("that creature")
        assert creature_lki is not None
        yield creature_lki

    def __str__ (self):
        return "that creature"

class YouSelector(Selector):
    def all(self, game, context):
        yield game.objects[context.get_state().controller_id]

    def __str__ (self):
        return "you"

class LKISelector(Selector):
    def __init__ (self, lki):
        self.lki = lki
    def all(self, game, context):
        if not self.lki.is_moved():
            yield self.lki.get_object()
        return    

class CreatureSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types:
                yield item
    def __str__ (self):
        return "creature"


class CreatureOrPlayerSelector(Selector):
    def all(self, game, context):
        for player in game.players:
            yield player

        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types:
                yield item
    def __str__ (self):
        return "creature or player"

class AttackingOrBlockingCreatureSelector(Selector):
    def all(self, game, context):
        for obj in game.objects.values():
            if "permanent" in obj.state.tags and "creature" in obj.state.types and ("attacking" in obj.state.tags or "blocking" in obj.state.tags):
                yield obj
    def slots(self):
        return ["that creature"]

    def __str__ (self):
        return "attacking or blocking creature"

class AttackingCreatureSelector(Selector):
    def all(self, game, context):
        for obj in game.objects.values():
            if "permanent" in obj.state.tags and "creature" in obj.state.types and "attacking" in obj.state.tags:
                yield obj
    def slots(self):
        return ["that creature"]

    def __str__ (self):
        return "attacking creature"

class CreatureAttackingYouSelector(Selector):
    def all(self, game, context):
        for obj in game.objects.values():
            if "permanent" in obj.state.tags and "creature" in obj.state.types and "attacking" in obj.state.tags and game.defending_player_id == context.get_state().controller_id:
                yield obj
    def slots(self):
        return ["that creature"]

    def __str__ (self):
        return "creature attacking you"

#e.g. non-black creature
class NonColorCreatureSelector(Selector):
    def __init__ (self, color):
        self.color = color
    def all(self, game, context):
        for obj in game.objects.values():
            if "permanent" in obj.state.tags and "creature" in obj.state.types and self.color not in obj.state.tags:
                yield obj
    def slots(self):
        return ["that creature"]
    
    def __str__ (self):
        return "non%s creature" % (self.color)


class EnchantedCreatureSelector(Selector):
    def all(self, game, context):
        if context.enchanted_id != None:
            ret = game.objects[context.enchanted_id]
            if "permanent" in ret.state.tags:
                yield ret

    def __str__ (self):
        return "enchanted creature"

