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

class Ability:
    def get_text(self, obj):
        return ""

class TriggeredAbility(Ability):
    def register(self, game, obj):
        pass

class StaticAbility(Ability):
    def evaluate(self, game, obj):
        pass

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

    def get_text(self, game, obj):
        return "[%s]" % self.mana

class PlayLandAbility(ActivatedAbility):
    def canActivate(self, game, obj, player):
        return (player.land_play_limit is None or player.land_played < player.land_play_limit) and player.id == obj.state.controller_id and obj.state.controller_id == game.active_player_id and (game.current_phase == "precombat main" or game.current_phase == "postcombat main") and game.get_stack_length() == 0 and obj.zone_id  == game.objects[obj.state.controller_id].hand_id

    def activate(self, game, obj, player):
        game.doZoneTransfer(obj, game.get_in_play_zone())
        obj.controller_id = player.id
        player.land_played += 1

    def get_text(self, game, obj):
        return "Play " + obj.state.title

class PlaySpell(ActivatedAbility):
    def canActivate(self, game, obj, player):
        return (player.id == obj.state.controller_id and obj.state.controller_id == game.active_player_id and (game.current_phase == "precombat main" or game.current_phase == "postcombat main") and game.get_stack_length() == 0 and obj.zone_id == game.objects[obj.state.controller_id].hand_id)

    def activate(self, game, obj, player):
        from process import process_play_spell
        process_play_spell (game, self, player, obj)

    def get_text(self, game, obj):
        return "Play " + obj.state.title + " [%s]" % (obj.state.manacost)

    def determineCost(self, game, obj, player):
        c = ManaCost(obj.state.manacost)
        return [c]

class FlyingAbility(StaticAbility):
   def evaluate(self, game, obj):
        if obj.zone_id == game.get_in_play_zone().id:
            obj.state.tags.add("flying")

class TapCostDoEffectAbility(ActivatedAbility):
    def __init__ (self, manacost, effect):
        self.manacost = manacost
        self.effect = effect

    def canActivate(self, game, obj, player):
        return (player.id == obj.state.controller_id and obj.state.controller_id == game.active_player_id and obj.zone_id == game.get_in_play_zone().id and not obj.tapped and ("creature" not in obj.state.types or "summoning sickness" not in obj.state.tags))

    def activate(self, game, obj, player):
        from process import process_activate_tapping_ability

        process_activate_tapping_ability(game, self, player, obj, self.effect)

    def get_text(self, game, obj):
        return "Activate \"%s\" [T %s]" % (self.effect, self.manacost)

    def determineCost(self, game, obj, player):
        if self.manacost != "":
            c = ManaCost(self.manacost)
            return [c]
        return []

class WhenXComesIntoPlayDoEffectAbility(TriggeredAbility):
    def __init__(self, selector, effect):
        self.selector = selector
        self.effect = effect

    def register(self, game, obj):
        game.add_volatile_event_handler("post_zone_transfer", partial(self.onPostZoneTransfer, game, obj))

    def onPostZoneTransfer(self, game, SELF, obj, zone_from, zone_to):
        if self.selector.contains(game, SELF, obj) and zone_to.type == "in play":
            from process import process_trigger_effect

            slots = {}
            for slot in self.selector.slots():
                slots[slot] = obj

            process_trigger_effect(game, SELF, self.effect, slots)

class WhenXDealsDamageToYDoEffectAbility(TriggeredAbility):
    def __init__(self, x_selector, y_selector, effect):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.effect = effect

    def register(self, game, obj):
        game.add_volatile_event_handler("post_deal_damage", partial(self.onPostDealDamage, game, obj))

    def onPostDealDamage(self, game, SELF, source, dest, n):
        if self.x_selector.contains(game, SELF, source) and self.y_selector.contains(game, SELF, dest):
            from process import process_trigger_effect

            slots = {}
            for slot in self.x_selector.slots():
                slots[slot] = source.get_id()

            for slot in self.y_selector.slots():
                slots[slot] = dest.get_id()

            process_trigger_effect(game, SELF, self.effect, slots)


