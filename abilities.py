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

from cost import *
from functools import partial
from objects import *
from selectors import *

class Ability:
    def get_text(self, game, obj):
        return ""

class TriggeredAbility(Ability):

    def isActive(self, game, obj):
        return True

    def getEventHandlers(self, game, obj):
        return []

class StateBasedAbility(Ability):

    def isActive(self, game, obj):
        return True

    def register(self, game, obj):
        pass

class StaticAbility(Ability):

    def isActive(self, game, obj):
        return True

    def getEffects(self):
        return []

class ActivatedAbility(Ability):
    def canActivate(self, game, obj, player):
        return False

    def activate(self, game, obj, player):
        pass

    def determineCost(self, game, obj, player):
        return []

class ManaAbility(ActivatedAbility):
    pass

class BasicManaAbility(ManaAbility):
    def __init__(self, mana):
        self.mana = mana

    def canActivate(self, game, obj, player):
        return player.id == obj.state.controller_id and obj.zone_id == game.get_in_play_zone().id and not obj.tapped

    def activate(self, game, obj, player):
        game.doTap(obj)
        game.doAddMana(player, obj, self.mana)
        game.raise_event("tapped_for_mana", obj, player, self.mana)

    def get_text(self, game, obj):
        return "[%s]" % self.mana

    def __str__ (self):
        return "BasicManaAbility(%s)" % str(self.mana)

class PlayLandAbility(ActivatedAbility):
    def canActivate(self, game, obj, player):
        return (player.land_play_limit is None or player.land_played < player.land_play_limit) and player.id == obj.state.controller_id and obj.state.controller_id == game.active_player_id and (game.current_phase == "precombat main" or game.current_phase == "postcombat main") and game.get_stack_length() == 0 and obj.zone_id  == game.objects[obj.state.controller_id].hand_id

    def activate(self, game, obj, player):
        game.doZoneTransfer(obj, game.get_in_play_zone())
        obj.controller_id = player.id
        player.land_played += 1

    def get_text(self, game, obj):
        return "Play " + str(obj)

    def __str__ (self):
        return "PlayLandAbility()"

class PlaySpell(ActivatedAbility):
    def canActivate(self, game, obj, player):
        return (player.id == obj.state.controller_id  and ("instant" in obj.state.types or (obj.state.controller_id == game.active_player_id and (game.current_phase == "precombat main" or game.current_phase == "postcombat main") and game.get_stack_length() == 0)) and obj.zone_id == game.objects[obj.state.controller_id].hand_id)

    def activate(self, game, obj, player):
        from process import process_play_spell
        process_play_spell (game, self, player, obj)

    def get_text(self, game, obj):
        return "Play " + str(obj) + " [%s]" % (obj.state.manacost)

    def determineCost(self, game, obj, player):

        manacost = obj.state.manacost
        if "X" in obj.state.manacost:
            from process import process_ask_x
            xcost = process_ask_x(game, obj, player)
            manacost = manacost.replace("X", xcost)

        c = ManaCost(manacost)
        return [c]

    def __str__ (self):
        return "PlaySpell()"

class TagAbility(StaticAbility):
    def __init__ (self, tag):
        from effects import XGetsTag
        self.effect = XGetsTag(SelfSelector(), tag)
        self.tag = tag

    def isActive(self, game, obj):
        return True

    def getEffects(self):
        return [self.effect]

    def __str__ (self):
        return "TagAbility(%s)" % self.tag


class ContinuousEffectStaticAbility(StaticAbility):
    def __init__ (self, effect):
        self.effect = effect

    def isActive(self, game, obj):
        return self.effect.isSelf() or game.isInPlay(obj)

    def getEffects(self):
        return [self.effect]

    def __str__ (self):
        return "ContinuousEffectStaticAbility(%s)" % str(self.effect)

class ConditionalContinuousEffectStaticAbility(StaticAbility):
    def __init__ (self, condition, effect):
        from effects import ConditionalEffect
        self.effect = ConditionalEffect(condition, effect)

    def isActive(self, game, obj):
        return self.effect.isSelf() or game.isInPlay(obj)

    def getEffects(self):
        return [self.effect]

    def __str__ (self):
        return "ConditionalContinuousEffectStaticAbility(%s)" % (str(self.effect))

class TapCostDoEffectAbility(ActivatedAbility):
    def __init__ (self, costs, effect):
        self.costs = costs
        self.effect = effect

    def canActivate(self, game, obj, player):
        return (player.id == obj.state.controller_id and obj.zone_id == game.get_in_play_zone().id and not obj.tapped and ("creature" not in obj.state.types or "summoning sickness" not in obj.state.tags or "haste" in obj.state.tags))

    def activate(self, game, obj, player):
        from process import process_activate_tapping_ability

        process_activate_tapping_ability(game, self, player, obj, self.effect)

    def get_text(self, game, obj):
        return "Activate \"%s\" [T %s]" % (self.effect, ",".join(map(str,self.costs)))

    def determineCost(self, game, obj, player):
        return self.costs

    def __str__ (self):
        return "TapCostDoEffectAbility(%s, %s)" % (str(map(str,self.costs)), str(self.effect))

class TapDoManaEffectAbility(ManaAbility):
    def __init__ (self, effect):
        self.effect = effect

    def canActivate(self, game, obj, player):
        return (player.id == obj.state.controller_id and obj.zone_id == game.get_in_play_zone().id and not obj.tapped and ("creature" not in obj.state.types or "summoning sickness" not in obj.state.tags or "haste" in obj.state.tags))

    def activate(self, game, obj, player):
        game.doTap(obj)

        # mana abilities don't use stack, resolve immediately
        from rules import manaEffect
        effect = manaEffect(self.effect)
        effect.resolve(game, obj)

        game.raise_event("tapped_for_mana", obj, player, None)

    def get_text(self, game, obj):
        return "Activate \"%s\" [T]" % (self.effect)

    def __str__ (self):
        return "TapDoManaEffectAbility(%s)" % (str(self.effect))

class CostDoEffectAbility(ActivatedAbility):
    def __init__ (self, costs, effect):
        self.costs = costs
        self.effect = effect

    def canActivate(self, game, obj, player):
        return (player.id == obj.state.controller_id and obj.zone_id == game.get_in_play_zone().id)

    def activate(self, game, obj, player):
        from process import process_activate_ability
        process_activate_ability(game, self, player, obj, self.effect)

    def get_text(self, game, obj):
        return "Activate \"%s\" [%s]" % (self.effect, ",".join(map(str,self.costs)))

    def determineCost(self, game, obj, player):
        return self.costs

    def __str__ (self):
        return "CostDoEffectAbility(%s, %s)" % (str(map(str,self.costs)), str(self.effect))

class CostDoEffectAsSorceryAbility(ActivatedAbility):
    def __init__ (self, costs, effect):
        self.costs = costs
        self.effect = effect

    def canActivate(self, game, obj, player):
        return (player.id == obj.state.controller_id and obj.zone_id == game.get_in_play_zone().id and (obj.state.controller_id == game.active_player_id and (game.current_phase == "precombat main" or game.current_phase == "postcombat main") and game.get_stack_length() == 0))

    def activate(self, game, obj, player):
        from process import process_activate_ability
        process_activate_ability(game, self, player, obj, self.effect)

    def get_text(self, game, obj):
        return "Activate \"%s\" [%s]" % (self.effect, ",".join(map(str,self.costs)))

    def determineCost(self, game, obj, player):
        return self.costs

    def __str__ (self):
        return "CostDoEffectAsSorceryAbility(%s, %s)" % (str(map(str,self.costs)), str(self.effect))

class CostDoEffectGraveyardUpkeepAbility(ActivatedAbility):
    def __init__ (self, costs, effect):
        self.costs = costs
        self.effect = effect

    def canActivate(self, game, obj, player):
        return player.id == obj.state.controller_id and obj.zone_id == game.get_graveyard(player).id and game.current_step == "upkeep" and player.id == game.active_player_id

    def activate(self, game, obj, player):
        from process import process_activate_ability
        process_activate_ability(game, self, player, obj, self.effect)

    def get_text(self, game, obj):
        return "Activate \"%s\" [%s]" % (self.effect, ",".join(map(str,self.costs)))

    def determineCost(self, game, obj, player):
        return self.costs

    def __str__ (self):
        return "CostDoEffectGraveyardUpkeepAbility(%s, %s)" % (str(map(str,self.costs)), str(self.effect))

class SelfTurnTapCostDoEffectAbility(ActivatedAbility):
    def __init__ (self, costs, effect):
        self.costs = costs
        self.effect = effect

    def canActivate(self, game, obj, player):
        return (player.id == obj.state.controller_id and obj.state.controller_id == game.active_player_id and obj.zone_id == game.get_in_play_zone().id and not obj.tapped and ("creature" not in obj.state.types or "summoning sickness" not in obj.state.tags or "haste" in obj.state.tags))

    def activate(self, game, obj, player):
        from process import process_activate_tapping_ability

        process_activate_tapping_ability(game, self, player, obj, self.effect)

    def get_text(self, game, obj):
        return "Activate \"%s\" [T %s]" % (self.effect, ",".join(map(str,self.costs)))

    def determineCost(self, game, obj, player):
        return self.costs

    def __str__ (self):
        return "SelfTurnTapCostDoEffectAbility(%s, %s)" % (str(map(str,self.costs)), str(self.effect))

class WhenXComesIntoPlayDoEffectAbility(TriggeredAbility):
    def __init__(self, selector, effect):
        self.selector = selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("post_zone_transfer", partial(self.onPostZoneTransfer, game, obj))]

    def onPostZoneTransfer(self, game, SELF, obj, zone_from, zone_to, cause):
        if self.selector.contains(game, SELF, obj) and zone_to.type == "in play":
            from process import process_trigger_effect

            slots = {}
            for slot in self.selector.slots():
                slots[slot] = obj

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXComesIntoPlayDoEffectAbility(%s, %s)" % (str(self.selector), str(self.effect))

class AsSelfComesIntoPlayAnswerDialog(TriggeredAbility):
    def __init__(self, dialog):
        self.dialog = dialog

    def isActive(self, game, obj):
        return True

    def getEventHandlers(self, game, obj):
        return [("post_zone_transfer", partial(self.onPostZoneTransfer, game, obj))]

    def onPostZoneTransfer(self, game, SELF, obj, zone_from, zone_to, cause):
        if SelfSelector().contains(game, SELF, obj) and zone_to.type == "in play":
            self.dialog.doModal(game, SELF)

    def __str__ (self):
        return "AsSelfComesIntoPlayAnswerDialog(%s)" % (str(self.dialog))


class WhenXIsPutIntoGraveyardFromPlayDoEffectAbility(TriggeredAbility):
    def __init__(self, selector, effect):
        self.selector = selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("pre_zone_transfer", partial(self.onPostZoneTransfer, game, obj))]

    def onPostZoneTransfer(self, game, SELF, obj, zone_from, zone_to, cause):
        if self.selector.contains(game, SELF, obj) and zone_to.type == "graveyard" and zone_from.type == "in play":
            from process import process_trigger_effect

            slots = {}
            for slot in self.selector.slots():
                slots[slot] = obj

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXIsPutIntoGraveyardFromPlayDoEffectAbility(%s, %s)" % (str(self.selector), str(self.effect))

class WheneverXCausesYToBePutIntoYourGraveyardFromTheBattlefield(TriggeredAbility):
    def __init__(self, x_selector, y_selector, effect):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.y_selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("pre_zone_transfer", partial(self.onPostZoneTransfer, game, obj))]

    def onPostZoneTransfer(self, game, SELF, obj, zone_from, zone_to, cause):
        if cause is not None and  self.x_selector.contains(game, SELF, cause) and self.y_selector.contains(game, SELF, obj) and zone_to.type == "graveyard" and zone_from.type == "in play" and zone_to.player_id == SELF.get_controller_id():
            from process import process_trigger_effect

            slots = {}
            slots["that card"] = obj
            for slot in self.y_selector.slots():
                slots[slot] = obj

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WheneverXCausesYToBePutIntoYourGraveyardFromTheBattlefield(%s, %s, %s)" % (str(self.x_selector), str(self.y_selector), str(self.effect))

class WhenXDealsDamageToYDoEffectAbility(TriggeredAbility):
    def __init__(self, x_selector, y_selector, effect):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.x_selector, SelfSelector) or isinstance(self.y_selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("post_deal_damage", partial(self.onPostDealDamage, game, obj))]

    def onPostDealDamage(self, game, SELF, source, dest, n):
        if self.x_selector.contains(game, SELF, source) and self.y_selector.contains(game, SELF, dest):
            from process import process_trigger_effect

            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = source

            for slot in self.y_selector.slots():
                slots[slot] = dest

            slots["that much"] = n

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXDealsDamageToYDoEffectAbility(%s, %s, %s)" % (str(self.x_selector), str(self.y_selector), str(self.effect))

class WhenXDealsDamageDoEffectAbility(TriggeredAbility):
    def __init__(self, x_selector, effect):
        self.x_selector = x_selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.x_selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("post_deal_damage", partial(self.onPostDealDamage, game, obj))]

    def onPostDealDamage(self, game, SELF, source, dest, n):
        if self.x_selector.contains(game, SELF, source):
            from process import process_trigger_effect

            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = source

            slots["that much"] = n

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXDealsDamageDoEffectAbility(%s, %s)" % (str(self.x_selector), str(self.effect))

class WhenXDealsCombatDamageToYDoEffectAbility(TriggeredAbility):
    def __init__(self, x_selector, y_selector, effect):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.x_selector, SelfSelector) or isinstance(self.y_selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("post_deal_combat_damage", partial(self.onPostDealDamage, game, obj))]

    def onPostDealDamage(self, game, SELF, source, dest, n):
        if self.x_selector.contains(game, SELF, source) and self.y_selector.contains(game, SELF, dest):
            from process import process_trigger_effect

            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = source

            for slot in self.y_selector.slots():
                slots[slot] = dest

            slots["that much"] = n

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXDealsCombatDamageToYDoEffectAbility(%s, %s, %s)" % (str(self.x_selector), str(self.y_selector), str(self.effect))

class WhenXDealsCombatDamageDoEffectAbility(TriggeredAbility):
    def __init__(self, x_selector, effect):
        self.x_selector = x_selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.x_selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("post_deal_combat_damage", partial(self.onPostDealDamage, game, obj))]

    def onPostDealDamage(self, game, SELF, source, dest, n):
        if self.x_selector.contains(game, SELF, source):
            from process import process_trigger_effect

            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = source

            slots["that much"] = n

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXDealsCombatDamageDoEffectAbility(%s, %s)" % (str(self.x_selector), str(self.effect))

class WhenXAttacksDoEffectAbility(TriggeredAbility):
    def __init__(self, selector, effect):
        self.selector = selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("attacks", partial(self.onAttacks, game, obj))]

    def onAttacks(self, game, SELF, attacker):
        from process import process_trigger_effect
        if self.selector.contains(game, SELF, attacker):
            slots = {}
            for slot in self.selector.slots():
                slots[slot] = attacker

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXAttacksDoEffectAbility(%s, %s)" % (str(self.selector), str(self.effect))

class WhenXBlocksDoEffectAbility(TriggeredAbility):
    def __init__(self, selector, effect):
        self.selector = selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("blocks", partial(self.onBlocks, game, obj))]

    def onBlocks(self, game, SELF, blocker, attacker):
        from process import process_trigger_effect
        if self.selector.contains(game, SELF, blocker):
            slots = {}
            for slot in self.selector.slots():
                slots[slot] = blocker

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXBlocksDoEffectAbility(%s, %s)" % (self.selector, self.effect)

class WhenXAttacksOrBlocksDoEffectAbility(TriggeredAbility):
    def __init__(self, selector, effect):
        self.selector = selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("attacks", partial(self.onAttacks, game, obj)), ("blocks", partial(self.onBlocks, game, obj))]

    def onAttacks(self, game, SELF, attacker):
        from process import process_trigger_effect
        if self.selector.contains(game, SELF, attacker):
            slots = {}
            for slot in self.selector.slots():
                slots[slot] = attacker

            process_trigger_effect(game, SELF, self.effect, slots)

    def onBlocks(self, game, SELF, blocker, attacker):
        from process import process_trigger_effect
        if self.selector.contains(game, SELF, blocker):
            slots = {}
            for slot in self.selector.slots():
                slots[slot] = blocker

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXAttacksOrBlocksDoEffectAbility(%s, %s)" % (str(self.selector), str(self.effect))


class WhenXBlocksOrBecomesBlockedByYDoEffectAbility(TriggeredAbility):
    def __init__(self, x_selector, y_selector, effect):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.x_selector, SelfSelector) or isinstance(self.y_selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("blocks", partial(self.onBlocks, game, obj))]

    def onBlocks(self, game, SELF, blocker, attacker):
        from process import process_trigger_effect
        if self.x_selector.contains(game, SELF, blocker) and self.y_selector.contains(game, SELF, attacker):
            slots = {}
            for slot in self.y_selector.slots():
                slots[slot] = attacker
            process_trigger_effect(game, SELF, self.effect, slots)

        elif (self.x_selector.contains(game, SELF, attacker) and self.y_selector.contains(game, SELF, blocker)):
            slots = {}
            for slot in self.y_selector.slots():
                slots[slot] = blocker
            process_trigger_effect(game, SELF, self.effect, slots)
  
    def __str__ (self):
        return "WhenXBlocksOrBecomesBlockedByYDoEffectAbility(%s, %s, %s)" % (self.x_selector, self.y_selector, self.effect)

class WhenXDiscardsACardDoEffectAbility(TriggeredAbility):
    def __init__ (self, x_selector, effect):
        self.x_selector = x_selector
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("post_discard", partial(self.onDiscard, game, obj))]

    def onDiscard(self, game, SELF, player, card, cause):
        from process import process_trigger_effect
        if self.x_selector.contains(game, SELF, player):
            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = player
            process_trigger_effect(game, SELF, self.effect, slots)
       
    def __str__ (self):
        return "WhenXDiscardsACardDoEffectAbility(%s, %s)" % (self.x_selector, self.effect)

class WhenXDrawsACardDoEffectAbility(TriggeredAbility):
    def __init__ (self, x_selector, effect):
        self.x_selector = x_selector
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("post_draw", partial(self.onDraw, game, obj))]

    def onDraw(self, game, SELF, player, card):
        from process import process_trigger_effect
        if self.x_selector.contains(game, SELF, player):
            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = player
            process_trigger_effect(game, SELF, self.effect, slots)
       
    def __str__ (self):
        return "WhenXDrawsACardDoEffectAbility(%s, %s)" % (self.x_selector, self.effect)

class WhenXCausesYToDiscardZ(TriggeredAbility):
    def __init__ (self, x_selector, y_selector, z_selector, effect):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.z_selector = z_selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.x_selector, SelfSelector) or isinstance(self.z_selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("post_discard", partial(self.onDiscard, game, obj))]

    def onDiscard(self, game, SELF, player, card, cause):
        from process import process_trigger_effect
        if self.x_selector.contains(game, SELF, cause) and self.y_selector.contains(game, SELF, player) and self.z_selector.contains(game, SELF, card):
            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = cause
            for slot in self.y_selector.slots():
                slots[slot] = player
            for slot in self.z_selector.slots():
                slots[slot] = card

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXCausesYToDiscardZ(%s, %s, %s, %s)" % (self.x_selector, self.y_selector, self.z_selector, self.effect)


class WhenXCastsYDoEffectAbility(TriggeredAbility):
    def __init__(self, x_selector, y_selector, effect):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.y_selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("play", partial(self.onPlay, game, obj))]

    def onPlay(self, game, SELF, spell):
        from process import process_trigger_effect

        if self.x_selector.contains(game, SELF, game.objects[spell.get_controller_id()]) and self.y_selector.contains(game, SELF, spell):

            slots = {}
            for slot in self.y_selector.slots():
                slots[slot] = spell

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXCastsYDoEffectAbility(%s, %s, %s)" % (str(self.x_selector), str(self.y_selector), str(self.effect))

class WhenXBecomesTappedDoEffectAbility(TriggeredAbility):
    def __init__ (self, x_selector, effect):
        self.x_selector = x_selector
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("post_tap", partial(self.onTap, game, obj))]

    def onTap(self, game, SELF, obj):
        from process import process_trigger_effect
        if self.x_selector.contains(game, SELF, obj):
            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = obj

            process_trigger_effect(game, SELF, self.effect, slots)
       
    def __str__ (self):
        return "WhenXBecomesTappedDoEffectAbility(%s, %s)" % (self.x_selector, self.effect)

class WhenXBecomesTappedForManaDoManaEffectAbility(TriggeredAbility):
    def __init__ (self, x_selector, effect):
        self.x_selector = x_selector
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("tapped_for_mana", partial(self.onTap, game, obj))]

    def onTap(self, game, SELF, obj, player, mana):
        from process import process_trigger_effect
        if self.x_selector.contains(game, SELF, obj):
            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = obj

            # mana abilities don't use stack, resolve immediately
            from rules import manaEffect
            e = EffectObject(obj, obj.get_controller_id(), self.effect, slots)
            effect = manaEffect(self.effect)
            effect.resolve(game, e)

    def __str__ (self):
        return "WhenXBecomesTappedForManaDoManaEffectAbility(%s, %s)" % (self.x_selector, self.effect)

class WhenXTapsYForManaDoEffectAbility(TriggeredAbility):
    def __init__ (self, x_selector, y_selector, effect):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("tapped_for_mana", partial(self.onTap, game, obj))]

    def onTap(self, game, SELF, obj, player, mana):
        from process import process_trigger_effect
        if self.x_selector.contains(game, SELF, player) and self.y_selector.contains(game, SELF, obj):
            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = obj

            for slot in self.y_selector.slots():
                slots[slot] = obj

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXTapsYForManaDoEffectAbility(%s, %s, %s)" % (self.x_selector, self.y_selector, self.effect)

class WhenXBecomesTargetOfYDoEffectAbility(TriggeredAbility):
    def __init__ (self, x_selector, y_selector, effect):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj) or isinstance(self.x_selector, SelfSelector) or isinstance(self.y_selector, SelfSelector)

    def getEventHandlers(self, game, obj):
        return [("target", partial(self.onTarget, game, obj))]

    def onTarget(self, game, SELF, source, target):
        from process import process_trigger_effect
        if self.x_selector.contains(game, SELF, target) and self.y_selector.contains(game, SELF, source):
            slots = {}
            for slot in self.y_selector.slots():
                slots[slot] = source

            for slot in self.x_selector.slots():
                slots[slot] = target

            process_trigger_effect(game, SELF, self.effect, slots)
       
    def __str__ (self):
        return "WhenXBecomesTargetOfYDoEffectAbility(%s, %s, %s)" % (self.x_selector, self.y_selector, self.effect)

class WhenXControlsNoOtherYDoEffectAbility(StateBasedAbility):
    def __init__ (self, x_selector, y_selector, effect):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj)

    def register(self, game, obj):
        from process import process_trigger_effect

        player = self.x_selector.only(game, obj)
        for o in self.y_selector.all(game, obj):
            if o.get_controller_id() == player.get_id() and o.get_id() != obj.get_id():
                return

        # this is a state-based trigger, check stack for an existing effect
        for so in game.get_stack_zone().objects:
            if isinstance(so, EffectObject):
                if obj.get_id() == so.get_source_lki().get_id() and self.effect == so.get_state().text:
                    return

        # maybe it hasn't triggered yet...
        for so in game.triggered_abilities:
            if isinstance(so, EffectObject):
                if obj.get_id() == so.get_source_lki().get_id() and self.effect == so.get_state().text:
                    return

        slots = {}
        process_trigger_effect(game, obj, self.effect, slots)
                   
    def __str__ (self):
        return "WhenXControlsNoOtherYDoEffectAbility(%s, %s, %s)" % (self.x_selector, self.y_selector, self.effect)

class AtTheBeginningOfEachPlayerssUpkeepDoEffectAbility(TriggeredAbility):
    def __init__(self, effect):
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("step", partial(self.onStep, game, obj))]

    def onStep(self, game, SELF):
        from process import process_trigger_effect
        if game.current_step == "upkeep":
            slots = {}
            slots["that player"] = game.get_active_player()
            process_trigger_effect(game, SELF, self.effect, slots)


    def __str__ (self):
        return "AtTheBeginningOfEachPlayerssUpkeepDoEffectAbility(%s)" % (self.effect)

class AtTheBeginningOfYourUpkeepDoEffectAbility(TriggeredAbility):
    def __init__(self, effect):
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("step", partial(self.onStep, game, obj))]

    def onStep(self, game, SELF):
        from process import process_trigger_effect
        if game.current_step == "upkeep" and str(SELF.get_controller_id()) == str(game.get_active_player().id):
            slots = {}
            slots["that player"] = game.get_active_player()
            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "AtTheBeginningOfYourUpkeepDoEffectAbility(%s)" % (self.effect)

class AtTheBeginningOfEachPlayerssEndStepDoEffectAbility(TriggeredAbility):
    def __init__(self, effect):
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("step", partial(self.onStep, game, obj))]

    def onStep(self, game, SELF):
        from process import process_trigger_effect
        if game.current_step == "end of turn":
            slots = {}
            slots["that player"] = game.get_active_player()
            process_trigger_effect(game, SELF, self.effect, slots)


    def __str__ (self):
        return "AtTheBeginningOfEachPlayerssEndStepDoEffectAbility(%s)" % (self.effect)

class AtTheBeginningOfEachPlayerssDrawStepDoEffectAbility(TriggeredAbility):
    def __init__(self, effect):
        self.effect = effect

    def isActive(self, game, obj):
        return game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("step", partial(self.onStep, game, obj))]

    def onStep(self, game, SELF):
        from process import process_trigger_effect
        if game.current_step == "draw":
            slots = {}
            slots["that player"] = game.get_active_player()
            process_trigger_effect(game, SELF, self.effect, slots)


    def __str__ (self):
        return "AtTheBeginningOfEachPlayerssDrawStepDoEffectAbility(%s)" % (self.effect)

class WhenXIsReturnedToPlayersHandDoEffectAbility(TriggeredAbility):
    def __init__(self, selector, effect):
        self.selector = selector
        self.effect = effect

    def isActive(self, game, obj):
        return isinstance(self.selector, SelfSelector) or game.isInPlay(obj)

    def getEventHandlers(self, game, obj):
        return [("pre_zone_transfer", partial(self.onPostZoneTransfer, game, obj))]

    def onPostZoneTransfer(self, game, SELF, obj, zone_from, zone_to, cause):
        if self.selector.contains(game, SELF, obj) and zone_to.type == "hand" and zone_from.type == "in play":
            from process import process_trigger_effect

            slots = {}
            for slot in self.selector.slots():
                slots[slot] = obj

            slots["that player"] = game.objects[zone_to.player_id]

            process_trigger_effect(game, SELF, self.effect, slots)

    def __str__ (self):
        return "WhenXIsReturnedToPlayersHandDoEffectAbility(%s, %s)" % (str(self.selector), str(self.effect))

