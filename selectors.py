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
        if obj is None:
            return False

        return obj.get_id() in map(lambda x:x.get_id(), self.all(game, context))

    def slots(self):
        return []

    def empty(self, game, context):
        list = [x for x in self.all(game, context)]
        return len(list) == 0

    def __str__(self):
        return "selector"

    def only(self, game, context):
        ret = [x for x in self.all(game, context)]
        assert len(ret) == 1
        return ret[0]

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

class SubtypeYouControlSelector(Selector):
    def __init__ (self, subtype):
        self.subtype = subtype

    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and self.subtype in item.state.subtypes and item.state.controller_id == context.get_state().controller_id:
                yield item

    def __str__ (self):
        return "%s subtype you control" % (self.subtype)

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

    def slots(self):
        return ["it"]

    def __str__(self):
        return "SELF"
        
class ThatPlayerSelector(Selector):
    def all(self, game, context):
        player_lki = context.get_slot("that player")
        assert player_lki is not None
        yield player_lki

    def __str__ (self):
        return "that player"

class ItSelector(Selector):
    def all(self, game, context):
        it_lki = context.get_slot("it")
        assert it_lki is not None
        yield it_lki

    def __str__ (self):
        return "it"

class ThatCreatureSelector(Selector):
    def all(self, game, context):
        creature_lki = context.get_slot("that creature")
        assert creature_lki is not None
        yield creature_lki

    def __str__ (self):
        return "that creature"

class SacrificedCreatureSelector(Selector):
    def all(self, game, context):
        creature_lki = context.get_slot("sacrificed")
        assert creature_lki is not None
        yield creature_lki

    def __str__ (self):
        return "sacrificed creature"

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

class OtherXCreaturesSelector(Selector):

    def __init__ (self, creatureType):
        self.creatureType = creatureType

    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types and self.creatureType in item.state.subtypes and context.get_id() != item.get_id():
                yield item

    def __str__ (self):
        return "other %s creatures" % (self.creatureType)

class LandSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "land" in item.state.types:
                yield item
    def __str__ (self):
        return "land"

class NonBasicLandSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "land" in item.state.types and "mountain" not in item.state.subtypes and "island" not in item.state.subtypes and "plains" not in item.state.subtypes and "forest" not in item.state.subtypes and "swamp" not in item.state.subtypes:
                yield item
    def __str__ (self):
        return "nonbasic land"

class ArtifactOrLandSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and ("land" in item.state.types or "artifact" in item.state.types):
                yield item

    def __str__ (self):
        return "artifact or land"

class CreatureWithFlyingSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types and "flying" in item.state.tags:
                yield item
    def __str__ (self):
        return "creature with flying"

class ArtifactSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "artifact" in item.state.types:
                yield item
    def __str__ (self):
        return "artifact"

class EnchantmentSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "enchantment" in item.state.types:
                yield item
    def __str__ (self):
        return "enchantment"

class OrSelector(Selector):
    def __init__ (self, x, y):
        self.x_selector = x
        self.y_selector = y

    def all(self, game, context):
        for item in self.x_selector.all(game, context):
            yield item

        for item in self.y_selector.all(game, context):
            yield item

    def __str__ (self):
        return "%s or %s" % (self.x_selector, self.y_selector)

class CreatureYouControlSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types and item.state.controller_id == context.get_state().controller_id:
                yield item
    def __str__ (self):
        return "creature you control"


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


class OpponentSelector(Selector):
    def all(self, game, context):
        for player in game.players:
            # TODO: not all non-controllers are opponents
            if player.get_id() != context.get_state().controller_id:
                yield player

    def slots(self):
        return ["that player"]

    def __str__ (self):
        return "opponent"

class EachOtherPlayerSelector(Selector):
    def all(self, game, context):
        for player in game.players:
            if player.get_id() != context.get_state().controller_id:
                yield player

    def slots(self):
        return ["that player"]

    def __str__ (self):
        return "each other player"


class CardSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            yield item
    def __str__ (self):
        return "card"

class CreatureCardSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "creature" in item.state.types:
                yield item

    def __str__ (self):
        return "creature card"

class BasicLandCardSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "land" in item.state.types and "basic" in item.state.supertypes:
                yield item

    def __str__ (self):
        return "basic land card"

class SubTypeCardSelector(Selector):
    def __init__ (self, type):
        self.type = type

    def all(self, game, context):
        for item in game.objects.values():
            if self.type in item.state.subtypes:
                yield item

    def __str__ (self):
        return "%s card" % (self.type)

class SubTypeSelector(Selector):
    def __init__ (self, type):
        self.type = type

    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and self.type in item.state.subtypes:
                yield item

    def __str__ (self):
        return "%s" % (self.type)

class SpellSelector(Selector):
    def __init__ (self):
        pass

    def all(self, game, context):
        for item in game.objects.values():
            if "spell" in item.get_state().tags:
                yield item

    def __str__ (self):
        return "spell"

class CreatureSpellSelector(Selector):
    def __init__ (self):
        pass

    def all(self, game, context):
        for item in game.objects.values():
            if "spell" in item.get_state().tags and "creature" in item.get_state().types:
                yield item

    def __str__ (self):
        return "creature spell"

class ColorSpellSelector(Selector):
    def __init__ (self, color):
        self.color = color

    def all(self, game, context):
        for item in game.objects.values():
            if "spell" in item.get_state().tags and self.color in item.get_state().tags:
                yield item

    def __str__ (self):
        return "%s spell" % (self.color)

class SpellOrAbilityAnOpponentControls(Selector):
    def __init__ (self):
        pass

    def all(self, game, context):
        for item in game.objects.values():
            # TODO: opponent != any other player
            if ("effect" in item.get_state().tags or "spell" in item.get_state().tags) and item.get_controller_id() != context.get_controller_id():
                yield item

    def __str__ (self):
        return "spell or ability an opponent controls"

