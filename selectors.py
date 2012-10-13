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

class SubTypeXControlsSelector(Selector):
    def __init__ (self, type, player_selector):
        self.type = type
        self.player_selector = player_selector

    def all(self, game, context):
        player = self.player_selector.only(game, context)

        for item in game.objects.values():
            if "permanent" in item.state.tags and self.type in item.state.subtypes and item.state.controller_id == player.get_id():
                yield item

    def __str__ (self):
        return "%s %s controls" % (self.type, self.player_selector)

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

class ThatCardSelector(Selector):
    def all(self, game, context):
        that_lki = context.get_slot("that card")
        assert that_lki is not None
        yield that_lki

    def __str__ (self):
        return "that card"

class ItsControllerSelector(Selector):
    def all(self, game, context):
        it_lki = context.get_slot("it")
        assert it_lki is not None
        yield game.objects[it_lki.get_controller_id()]

    def __str__ (self):
        return "its controller"

class ThatCreatureSelector(Selector):
    def all(self, game, context):
        creature_lki = context.get_slot("that creature")
        assert creature_lki is not None
        yield creature_lki

    def __str__ (self):
        return "that creature"

class ThatCreaturesControllerSelector(Selector):
    def all(self, game, context):
        creature_lki = context.get_slot("that creature")
        assert creature_lki is not None
        yield game.objects[creature_lki.get_controller_id()]

    def __str__ (self):
        return "that creature's controller"

class ThatLandSelector(Selector):
    def all(self, game, context):
        land_lki = context.get_slot("that land")
        assert land_lki is not None
        yield land_lki

    def __str__ (self):
        return "that land"

class ThatLandsControllerSelector(Selector):
    def all(self, game, context):
        land_lki = context.get_slot("that land")
        assert land_lki is not None
        yield game.objects[land_lki.get_controller_id()]

    def __str__ (self):
        return "that land's controller"

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
        if self.lki.is_valid():
            yield self.lki.get_object()
        return    
    def __str__ (self):
        return str(self.lki)

class CreatureSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types:
                yield item

    def slots(self):
        return ["that creature", "it"]

    def __str__ (self):
        return "creature"

class TappedCreatureSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types and item.tapped:
                yield item

    def slots(self):
        return ["that creature", "it"]

    def __str__ (self):
        return "tapped creature"


class CreatureWithPowerGreaterThanNSelector(Selector):
    def __init__ (self, n):
        self.n = n

    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types and item.state.power > self.n.evaluate(game, context):
                yield item

    def slots(self):
        return ["that creature", "it"]

    def __str__ (self):
        return "creature with power greater than %s" % self.n

class CreatureWithPowerNOrGreaterSelector(Selector):
    def __init__ (self, n):
        self.n = n

    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types and item.state.power >= self.n.evaluate(game, context):
                yield item

    def slots(self):
        return ["that creature", "it"]

    def __str__ (self):
        return "creature with power %s or greater" % self.n

class CreatureOfTheChosenType(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types and context.get_modal() in item.state.subtypes:
                yield item

    def __str__ (self):
        return "creature of the chosen type"

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

    def slots(self):
        return ["that land"]

    def __str__ (self):
        return "land"

class NonBasicLandSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "land" in item.state.types and "mountain" not in item.state.subtypes and "island" not in item.state.subtypes and "plains" not in item.state.subtypes and "forest" not in item.state.subtypes and "swamp" not in item.state.subtypes:
                yield item
    def __str__ (self):
        return "nonbasic land"

class ArtifactEnchantmentOrLandSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and ("land" in item.state.types or "artifact" in item.state.types or "enchantment" in item.state.types):
                yield item

    def __str__ (self):
        return "artifact, enchantment or land"

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

class CreatureYouDontControlSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and "creature" in item.state.types and item.state.controller_id != context.get_state().controller_id:
                yield item

    def __str__ (self):
        return "creature you don't control"


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

class NonArtifactNonColorCreatureSelector(Selector):
    def __init__ (self, color):
        self.color = color
    def all(self, game, context):
        for obj in game.objects.values():
            if "permanent" in obj.state.tags and "creature" in obj.state.types and self.color not in obj.state.tags and "artifact" not in obj.state.types:
                yield obj
    def slots(self):
        return ["that creature"]
    
    def __str__ (self):
        return "nonartifact non%s creature" % (self.color)

class ColorCreatureSelector(Selector):
    def __init__ (self, color):
        self.color = color

    def all(self, game, context):
        for obj in game.objects.values():
            if "permanent" in obj.state.tags and "creature" in obj.state.types and self.color in obj.state.tags:
                yield obj

    def slots(self):
        return ["that creature"]

    def __str__ (self):
        return "%s creature" % (self.color)

class ColorPermanentSelector(Selector):
    def __init__ (self, color):
        self.color = color

    def all(self, game, context):
        for obj in game.objects.values():
            if "permanent" in obj.state.tags and self.color in obj.state.tags:
                yield obj

    def slots(self):
        return ["that permanent"]

    def __str__ (self):
        return "%s permanent" % (self.color)

class EnchantedCreatureSelector(Selector):
    def all(self, game, context):
        if context.get_enchanted_id() != None:
            ret = game.objects[context.get_enchanted_id()]
            if "permanent" in ret.state.tags:
                yield ret

    def slots(self):
        return ["it"]

    def __str__ (self):
        return "enchanted creature"

class EnchantedLandSelector(Selector):
    def all(self, game, context):
        if context.get_enchanted_id() != None:
            ret = game.objects[context.get_enchanted_id()]
            if "permanent" in ret.state.tags:
                yield ret

    def slots(self):
        return ["it"]

    def __str__ (self):
        return "enchanted land"

class EnchantedPermanentSelector(Selector):
    def all(self, game, context):
        if context.get_enchanted_id() != None:
            ret = game.objects[context.get_enchanted_id()]
            if "permanent" in ret.state.tags:
                yield ret

    def slots(self):
        return ["it"]

    def __str__ (self):
        return "enchanted permanent"

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

class CreatureCardFromYourGraveyardSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "creature" in item.state.types and item.zone_id == game.get_graveyard(game.objects[context.get_controller_id()]).id:
                yield item

    def __str__ (self):
        return "creature card from your graveyard"

class ColorCardFromYourGraveyardSelector(Selector):

    def __init__(self, color):
        self.color = color

    def all(self, game, context):
        for item in game.objects.values():
            if self.color in item.state.tags and item.zone_id == game.get_graveyard(game.objects[context.get_controller_id()]).id:
                yield item

    def __str__ (self):
        return "%s card from your graveyard" % (self.color)

class SubTypeCardFromYourGraveyardSelector(Selector):
    def __init__(self, type):
        self.type = type

    def all(self, game, context):
        for item in game.objects.values():
            if self.type in item.state.subtypes and item.zone_id == game.get_graveyard(game.objects[context.get_controller_id()]).id:
                yield item

    def __str__ (self):
        return "%s card from your graveyard" % (self.type)

class CreatureCardFromAnyGraveyardSelector(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "creature" in item.state.types and game.objects[item.zone_id].type == "graveyard":
                yield item

    def __str__ (self):
        return "creature card from any graveyard"

class CreatureCardOfTheChosenType(Selector):
    def all(self, game, context):
        for item in game.objects.values():
            if "creature" in item.state.types and context.get_modal() in item.state.subtypes:
                yield item

    def __str__ (self):
        return "creature card of the chosen type"

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

class ColorTypeCardSelector(Selector):
    def __init__ (self, color, type):
        self.color = color
        self.type = type

    def all(self, game, context):
        for item in game.objects.values():
            if self.type in item.state.types and self.color in item.state.tags:
                yield item

    def __str__ (self):
        return "%s %s card" % (self.color, self.type)

class SubTypeSelector(Selector):
    def __init__ (self, type):
        self.type = type

    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and self.type in item.state.subtypes:
                yield item

    def __str__ (self):
        return "%s" % (self.type)

class LandSubTypeSelector(Selector):
    def __init__ (self, type):
        self.type = type

    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and self.type in item.state.subtypes and "land" in item.state.types:
                yield item

    def __str__ (self):
        return "%s" % (self.type)

class CreatureSubTypeSelector(Selector):
    def __init__ (self, type):
        self.type = type

    def all(self, game, context):
        for item in game.objects.values():
            if "permanent" in item.state.tags and self.type in item.state.subtypes and "creature" in item.state.types:
                yield item

    def __str__ (self):
        return "%s creature" % (self.type)

class SpellSelector(Selector):
    def __init__ (self):
        pass

    def all(self, game, context):
        for item in game.objects.values():
            if "spell" in item.get_state().tags:
                yield item

    def __str__ (self):
        return "spell"

class InstantSpellSelector(Selector):
    def __init__ (self):
        pass

    def all(self, game, context):
        for item in game.objects.values():
            if "spell" in item.get_state().tags and "instant" in item.get_state().types:
                yield item

    def __str__ (self):
        return "instant spell"

class SpellWithSingleTargetSelector(Selector):
    def __init__ (self):
        pass

    def all(self, game, context):
        for item in game.objects.values():
            if "spell" in item.get_state().tags and item.targets.get("target") is not None:
                yield item

    def __str__ (self):
        return "spell with single target"

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

class ColorSourceSelector(Selector):
    def __init__ (self, color):
        self.color = color

    def all(self, game, context):
        for item in game.objects.values():
            if self.color in item.get_state().tags and ("permanent" in item.get_state().tags or "spell" in item.get_state().tags or "effect" in item.get_state().tags):
                yield item

    def __str__ (self):
        return "%s source" % (self.color)

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

class SpellOrAbilitySelector(Selector):
    def __init__ (self):
        pass

    def all(self, game, context):
        for item in game.objects.values():
            if ("effect" in item.get_state().tags or "spell" in item.get_state().tags):
                yield item

    def __str__ (self):
        return "spell or ability"

class CreatureThatAttackedThisTurnSelector(Selector):
    def all(self, game, context):
        for item in game.creature_that_attacked_this_turn_lkis:
            yield item

    def slots(self):
        return ["that creature", "it"]

    def __str__ (self):
        return "creature that attacked this turn"


