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

import random

from objects import *

class DamageReplacement:
    def __init__ (self, list, combat):
        self.list = list
        self.combat = combat

class Game:
    def __init__ (self, input, output):
        self.zones = []
        self.objects = {}
        self.obj_max_id = 0

        self.players = []

        self.active_player_id = None
        self.current_player_priority_id = None
        self.current_phase = None
        self.current_step = None

        # Player chosen as the defending player during combat
        self.defending_player_id = None
        self.attacking_player_id = None

        self.triggered_abilities = []

        self.declared_attackers = set()
        self.declared_blockers = set()
        self.declared_blockers_map = {}

        self.input = input
        self.output = output

        self.events = {}
        self.volatile_events = {}

        self.volatile_effects = []

        self.until_end_of_turn_effects = []

        self.end_of_combat_triggers = []

        self.turn_number = 0

    def add_object (self, object):
        self.obj_max_id += 1
        object.id = self.obj_max_id
        self.objects[self.obj_max_id] = object
        #object.game = self

    def create_card (self, title, manacost, supertypes, types, subtypes, tags, text, power, toughness):
        o = Object()
        self.add_object(o)
        o.initial_state.title = title
        o.initial_state.manacost = manacost
        o.initial_state.supertypes.update(supertypes)
        o.initial_state.types.update(types)
        o.initial_state.subtypes.update(subtypes)
        o.initial_state.tags.update(tags)
        o.initial_state.text = text
        o.initial_state.power = power
        o.initial_state.toughness = toughness

        self.output.createCard(o.id)

        return o

    def create_player (self, name, cards):
        player = Player (name)
        self.add_object (player)
        self.players.append (player)

        player.initial_state.types.add ("player")
        player.initial_state.title = name

        hand = Zone ("hand", player.id)
        library = Zone ("library", player.id)
        graveyard = Zone ("graveyard", player.id)

        self.add_object(hand)
        self.add_object(library)
        self.add_object(graveyard)

        self.output.createPlayer(player.id)
        self.output.createZone(hand.id, player.id, "hand")
        self.output.createZone(library.id, player.id, "library")
        self.output.createZone(graveyard.id, player.id, "graveyard")

        player.hand_id = hand.id
        player.library_id = library.id
        player.graveyard_id = graveyard.id

        self.zones.append (hand)
        self.zones.append (library)
        self.zones.append (graveyard)

        # add cards to player library
        for card in cards:
            card.zone_id = library.id
            card.owner_id = player.id
            card.controller_id = player.id
            library.objects.append (card)

        return player

    def get_next_player (self, player):
        # returns a player next in succession
        for i in range(len(self.players)):
            if self.players[i] == player:
                return self.players[(i + 1) % len(self.players)]

    def create_damage_assignment(self, damage_assignment_list, combat=False):
        d = DamageAssignment(damage_assignment_list, combat)
        self.add_object(d)

        self.output.createDamageAssignment(d.id)

        return d

    def create_effect_object(self, origin, controller_id, text, slots):
        e = EffectObject(origin, controller_id, text, slots)
        self.add_object(e)

        self.output.createEffectObject(e.id)

        return e

    def create (self):
        #p1 = self.create_player("Alice")
        #p2 = self.create_player("Bob")  

        in_play = Zone ("in play", None)
        self.add_object(in_play)

        removed = Zone("removed", None)
        self.add_object(removed)

        stack = Zone("stack", None)
        self.add_object(stack)

        self.output.createZone(in_play.id, None, "in play")
        self.output.createZone(removed.id, None, "removed")
        self.output.createZone(stack.id, None, "stack")

        self.zones.append ( in_play )
        self.zones.append ( removed )
        self.zones.append ( stack )

        self.stack = self.get_stack_zone().objects

    def get_stack_length (self):
        return len(self.stack)

    def stack_top (self):
        return self.stack[-1]

    def stack_pop (self):
        return self.stack.pop ()

    def stack_push (self, s):
        assert s.zone_id == None
        s.zone_id = self.get_stack_zone().id
        self.stack.append (s)

    def add_event_handler (self, event, handler):
        event_handlers = self.events.get (event)
        if event_handlers is None:
            event_handlers = []
            self.events[event] = event_handlers

        event_handlers.append (handler)

    def add_volatile_event_handler(self, event, handler):
        event_handlers = self.volatile_events.get(event)
        if event_handlers is None:
            event_handlers = []
            self.volatile_events[event] = event_handlers

        event_handlers.append (handler)

    def raise_event (self, event, *args, **kargs):
        event_handlers = self.events.get(event, [])
        for handler in event_handlers:
            handler (*args, **kargs)

        event_handlers = self.volatile_events.get(event, [])
        for handler in event_handlers:
            handler (*args, **kargs)

    def _get_zone (self, type):
        for zone in self.zones:
            if zone.type == type:
                return zone
        return None

    def get_in_play_zone (self):
        return self._get_zone ("in play")

    def get_stack_zone (self):
        return self._get_zone ("stack")

    def get_hand(self, player):
        return self.objects[player.hand_id]

    def get_library(self, player):
        return self.objects[player.library_id]

    def get_graveyard(self, player):
        return self.objects[player.graveyard_id]

    def doTap (self, object):

        if object.tapped == False:
            self.raise_event ("pre_tap", object)
            object.tapped = True
            self.raise_event ("post_tap", object)

    def doUntap (self, object):

        if object.tapped == True:
            self.raise_event ("pre_untap", object)
            object.tapped = False
            self.raise_event ("post_untap", object)

    def doAddMana (self, player, source, mana):
        player.manapool += mana

    def doDrawCard (self, player):
        library = self.get_library(player)
        if len(library.objects) == 0:
            #  TODO: lose
            pass
        else:
            card = library.objects[-1]
            self.doZoneTransfer(card, self.get_hand(player))

    def get_active_player(self):
        return self.objects[self.active_player_id]

    def get_defending_player(self):
        return self.objects.get(self.defending_player_id)

    def get_attacking_player(self):
        return self.objects.get(self.attacking_player_id)

    def doShuffle(self, zone):
        random.shuffle(zone.objects)

    def doZoneTransfer (self, object, zone):
        object.damage = 0
        zone_from = self.objects[object.zone_id]

        print "pre zone transfer %s from %s" % (object, object.zone_id)

        self.raise_event ("pre_zone_transfer", object, zone_from, zone)

        # also move enchantments to graveyard
        enchantments = []
        if zone_from.id == self.get_in_play_zone().id:
            for obj in self.objects.values():
                if obj.enchanted_id == object.id:
                    self.doZoneTransfer(obj, self.get_graveyard(self.objects[obj.owner_id]))

        object.zone_id = zone.id
        zone_from.objects.remove(object)
        zone.objects.append (object)

        if zone.id != self.get_in_play_zone().id:
            object.enchanted_id = None
            object.damage = 0
            object.regenerated = False
            object.preventNextDamage = 0
            object.tapped = False

        print "post zone transfer %s to %s" % (object, object.zone_id)

        from process import evaluate
        evaluate(self)

        # objects moving into play have summoning sickness tag applied to them
        if zone == self.get_in_play_zone():
            object.initial_state.tags.add("summoning sickness")

        self.raise_event ("post_zone_transfer", object, zone_from, zone)


    def doDiscard(self, player, card, cause = None):
        self.raise_event ("pre_discard", player, card, cause)
        self.doZoneTransfer (card, self.get_graveyard(player))
        self.raise_event ("post_discard", player, card, cause)

    def doLoseLife(self, player, count):
        player.life -= count

    def doGainLife(self, player, count):
        player.life += count

    def doDealDamage(self, list, combat=False):
        print "doDealDamage"

        dr = DamageReplacement(list, combat)
        self.raise_event("damage_replacement", dr)

        for a, b, n in dr.list:
            if not b.is_moved():

                ndiff = b.get_object().preventNextDamage
                if ndiff > n:
                    ndiff = n
                n -= ndiff
                b.get_object().preventNextDamage -= ndiff

                if n == 0:
                    continue

                if combat:
                     self.raise_event("pre_deal_combat_damage", a, b, n)

                self.raise_event("pre_deal_damage", a, b, n)

                if "player" in b.get_state().types:
                    print "%d damage to player %s " % (n, b.get_object())
                    b.get_object().life -= n
                else:
                    print "%d damage to %s" % (n, b.get_object())
                    b.get_object().damage += n

                if combat:
                     self.raise_event("post_deal_combat_damage", a, b, n)

                self.raise_event("post_deal_damage", a, b, n)

    def doRegenerate(self, obj):
        obj = obj.get_object()
        print "doRegenerate %s" % (obj)
        obj.regenerated = True 

    def doDestroy(self, obj):
        obj = obj.get_object()
        print "doDestroy %s" % (obj)

        if obj.regenerated:
            obj.tapped = True
            obj.damage = 0
            obj.regenerated = False

            # remove from combat
            self.doRemoveFromCombat(obj)
        else:
            self.doZoneTransfer(obj, self.get_graveyard(self.objects[obj.owner_id]))

    def doCounter(self, obj):
        obj = obj.get_object()
        print "doCounter %s" % (obj)
        self.doZoneTransfer(obj, self.get_graveyard(self.objects[obj.owner_id]))

    def doSacrifice(self, obj):
        obj = obj.get_object()
        print "doSacrifice %s" % (obj)
        self.doZoneTransfer(obj, self.get_graveyard(self.objects[obj.owner_id]))

    def doBury(self, obj):
        obj = obj.get_object()
        print "doBury %s" % (obj)
        self.doZoneTransfer(obj, self.get_graveyard(self.objects[obj.owner_id]))

    def doRemoveFromCombat(self, obj):
        id = obj.get_id()
        for a in self.declared_attackers:
            if a.get_id() == id:
                self.declared_attackers.remove (a)
                return

        for b in self.declared_blockers:
            if b.get_id() == id:
                self.declared_attackers.remove (b)
                return

    def doPreventNextDamage(self, obj, n):
        obj.preventNextDamage += n

    def delete(self, obj):
        print "deleting object %s" % obj
        self.objects[obj.zone_id].objects.remove(obj)
        obj.zone_id = None
        del self.objects[obj.id]

    def isInPlay(self, obj):
        return obj.zone_id == self.get_in_play_zone().id

    def onResolve(self, resolvable):
        self.raise_event ("resolve", resolvable)

    def onPlay(self, spell):
        self.raise_event ("play", spell)

