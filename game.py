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
import copy

from objects import *
from actions import Action,ActionSet

class InterceptableMethod:
    def __init__ (self, _callable):
        self.original = _callable
        self.reset()
        self.pos = -1

    def reset(self):
        self.interceptors = [self.original]

    def add(self, _callable):
        self.interceptors = [_callable] + self.interceptors

    def proceed(self, *args, **kargs):

        self.pos += 1

        assert self.pos >= 0
        assert self.pos < len(self.interceptors)

        last = self.pos == (len(self.interceptors) - 1)

        self.interceptors[self.pos](self, *args, **kargs)

        if last:
            self.pos = -1

    def cancel(self):
        self.pos = -1

    def __call__(self, *args, **kargs):
        return self.proceed(*args, **kargs)

class DamageReplacement:
    def __init__ (self, list, combat):
        self.list = list
        self.combat = combat

class AttackerValidator:
    def __init__ (self, attacker, can):
        self.attacker = attacker
        self.can = can

class BlockerValidator:
    def __init__ (self, attacker, blocker, can):
        self.attacker = attacker
        self.blocker = blocker
        self.can = can

class Game:
    def __init__ (self, output):
        self.zones = []
        self.objects = {}
        self.obj_max_id = 0

        self.lkis = {}
        self.lki_max_id = 0

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

        self.output = output

        self.events = {}
        self.volatile_events = {}

        self.until_end_of_turn_effects = []
        self.indefinite_effects = []

        self.end_of_combat_triggers = []

        self.turn_number = 0

        # ids of cards revealed to all players
        self.revealed = []

        # ids of cards looked at by a controller (e.g. from a library)   player_id -> [id]
        self.looked_at = {}

        self.play_cost_replacement_effects = []

        self.damage_preventions = []

        self.creature_that_attacked_this_turn_lkis = set()
        self.additional_combat_phase_followed_by_an_additional_main_phase = False

        self.interceptable_draw = InterceptableMethod(self._drawCard)

        self.process_stack = []

        self.process_returns_stack = []

        # game has ended
        self.end = False

        self.winners = set()
        self.losers = set()


    def reset_interceptables(self):
        # TODO: have single method that also resets all the effects and other replacements stuff at the beginning of the evaluate process
        self.interceptable_draw.reset()

    def add_object (self, object):
        self.obj_max_id += 1
        object.id = self.obj_max_id
        self.objects[self.obj_max_id] = object
        #object.game = self

    def add_lki(self, lki):
        self.lki_max_id += 1
        lki.lki_id = "lki_" + str(self.lki_max_id)
        self.lkis[lki.lki_id] = lki

    def create_lki(self, obj):

        if isinstance(obj, LastKnownInformation):
           return obj.lki_id

        assert isinstance(obj, Object)

        lki = LastKnownInformation(self, obj)
        self.add_lki(lki)

        return lki.lki_id

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

    def create_token(self, owner_id, supertypes, types, subtypes, tags, text, power, toughness):
        o = Object()
        self.add_object(o)
        o.initial_state.title = "Token"
        o.initial_state.supertypes.update(supertypes)
        o.initial_state.types.update(types)
        o.initial_state.subtypes.update(subtypes)
        o.initial_state.tags.update(tags)
        o.initial_state.text = text
        o.initial_state.power = power
        o.initial_state.toughness = toughness

        o.initial_state.tags.add("token")

        o.owner_id = owner_id
        o.controller_id = owner_id
        o.initial_state.controller_id = owner_id

        o.state.tags.add("summoning sickness")

        self.get_in_play_zone().objects.append (o)
        o.zone_id = self.get_in_play_zone().id

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

        self.looked_at[player.id] = []

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

    def create_effect_object(self, origin_lki, controller_id, text, slots):
        e = EffectObject(self.lki(origin_lki), controller_id, text, slots)
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

        # print "EVENT: " + `event`

        args = [self] + list(args)

        event_handlers = self.events.get(event, [])
        for handler in event_handlers:
            # print "EVENT: " + `event` + " handler: " + `handler`
            handler (*args, **kargs)

        event_handlers = self.volatile_events.get(event, [])
        for handler in event_handlers:
            # print "EVENT: " + `event` + " volatile handler: " + `handler`

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

    def get_removed_zone(self):
        return self._get_zone("removed")

    def get_hand(self, player):
        return self.objects[player.hand_id]

    def get_library(self, player):
        return self.objects[player.library_id]

    def get_graveyard(self, player):
        return self.objects[player.graveyard_id]

    def doTap (self, object):

        if (not object.is_moved()) and object.get_object().tapped == False:
            self.raise_event ("pre_tap", object)
            object.get_object().tapped = True
            self.raise_event ("post_tap", object)

    def doUntap (self, object):

        if (not object.is_moved()) and object.get_object().tapped == True:
            self.raise_event ("pre_untap", object)
            object.get_object().tapped = False
            self.raise_event ("post_untap", object)

    def doAddMana (self, player, source, mana):
        player.manapool += mana

    def _drawCard(self, interceptable, game, player):
        library = self.get_library(player)
        if len(library.objects) == 0:
            self.doLoseGame(player)
        else:
            card = library.objects[-1]
            self.doZoneTransfer(card, self.get_hand(player))
            self.raise_event ("post_draw", player, card)

    def doDrawCard (self, player):
        self.interceptable_draw(self, player)
       
    def doLoseGame(self, player):
        # TODO: multiplayer
        self.losers.add(player.get_id())
        for p in self.players:
            if p.id != player.id:
                self.winners.add(p.id)

        self.end = True

    def doEndGame(self):
        self.output.gameEnds(None)
        self.end = True

    def doWinGame(self, player):
        self.output.gameEnds(player.get_object())
        self.end = True
        self.winners.add (player.get_id())

        # TODO: multiplayer
        for p in self.players:
            if p.id != player.id:
                self.losers.add(p.id)

    def get_active_player(self):
        return self.objects[self.active_player_id]

    def get_defending_player(self):
        return self.objects.get(self.defending_player_id)

    def get_attacking_player(self):
        return self.objects.get(self.attacking_player_id)

    def doShuffle(self, zone):
        random.shuffle(zone.objects)

    def doZoneTransfer (self, object, zone, cause = None):

        assert self.obj(object.id) == object

        object.damage = 0
        zone_from = self.objects[object.zone_id]

        #print("pre zone transfer %s from %s" % (object, object.zone_id))

        # TODO: change to event handler
        self._moveLkis(object, zone_from, zone, cause)

        self.raise_event ("pre_zone_transfer", object, zone_from, zone, cause)

        # also move enchantments to graveyard
        enchantments = []
        if zone_from.id == self.get_in_play_zone().id:
            for obj in self.objects.values():
                if obj.enchanted_id == object.id:
                    self.doZoneTransfer(obj, self.get_graveyard(self.objects[obj.owner_id]), cause)

        object.zone_id = zone.id
        zone_from.objects.remove(object)
        zone.objects.append (object)

        if zone.id != self.get_in_play_zone().id:
            object.enchanted_id = None
            object.damage = 0
            object.regenerated = False
            object.tapped = False
            if "summoning sickness" in object.initial_state.tags:
                object.initial_state.tags.remove("summoning sickness")
            object.counters = []

        if zone_from.id == self.get_in_play_zone().id:
            # coming out of play resets controller
            object.controller_id = object.owner_id

        self.output.zoneTransfer(zone_from, zone, object)
        #print("post zone transfer %s to %s" % (object, object.zone_id))

        if zone.type == "in play":
            if "comes into play tapped" in object.state.tags:
                object.tapped = True

        from process import evaluate
        evaluate(self)

        # objects moving into play have summoning sickness tag applied to them
        if zone == self.get_in_play_zone():
            object.initial_state.tags.add("summoning sickness")

        self.raise_event ("post_zone_transfer", object, zone_from, zone, cause)


    def doDiscard(self, player, card, cause = None):
        self.raise_event ("pre_discard", player, card, cause)
        self.doZoneTransfer (card, self.get_graveyard(player))
        self.raise_event ("post_discard", player, card, cause)

    def doLoseLife(self, player, count):
        player.life -= count

    def doGainLife(self, player, count):
        player.life += count

    def doPayLife(self, player, count):
        player.life -= count

    def doDealDamage(self, list, combat=False):

        dr = DamageReplacement(list, combat)
        self.raise_event("damage_replacement", dr)

        for a_lki_id, b_lki_id, n in dr.list:
            if not self.lki(b_lki_id).is_moved():

                # go through all applicable damage prevention effects
                applicable = []
                for damage_prevention in self.damage_preventions:
                    if damage_prevention.canApply(self, (a_lki_id, b_lki_id, n), combat):
                        applicable.append (damage_prevention)

                while len(applicable) > 0:
                    # do we have a unique applicable effect?
                    if len(applicable) == 1:
                        a_lki_id,b_lki_id,n = applicable[0].apply(self, (a_lki_id, b_lki_id, n), combat)
                        applicable = []
                    else:
                        # we let the reciever's controller choose
                        # TODO: make threadless
                        controller = self.objects[self.lki(b_lki_id).get_controller_id()]

                        actions = []
                        for damage_prevention in applicable:
                            action = Action()
                            action.text = damage_prevention.getText()
                            action.damage_prevention = damage_prevention
                            actions.append(action)

                        _as = ActionSet (self, controller, "Which damage prevention effect apply first for %d damage to %s?" % (n, str(self.lki(b_lki_id))), actions)
                        action = self.input.send (_as)

                        damage_prevention = action.damage_prevention

                        a_lki_id,b_lki_id,n = damage_prevention.apply(self, (a_lki_id,b_lki_id,n), combat)
                        applicable.remove(damage_prevention)

                        if n <= 0:
                            break

                        new_applicable = []
                        for damage_prevention in applicable[:]:
                            if damage_prevention.canApply(self, (a_lki_id,b_lki_id,n), combat):
                                new_applicable.append(damage_prevention)
                        applicable = new_applicable


                if n <= 0:
                    continue

                if combat:
                     self.raise_event("pre_deal_combat_damage", a_lki_id, b_lki_id, n)

                self.raise_event("pre_deal_damage", a_lki_id, b_lki_id, n)

                a = self.lki(a_lki_id)
                b = self.lki(b_lki_id)
                if "player" in b.get_state().types:
                    if "damage that would reduce your life total to less than 1 reduces it to 1 instead" in b.get_state().tags and (b.get_object().life - n < 1):
                        b.get_object().life = 1
                    else:
                        b.get_object().life -= n
                else:
                    b.get_object().damage += n

                self.output.damage(a.get_object(), b.get_object, n)

                if combat:
                     self.raise_event("post_deal_combat_damage", a_lki_id, b_lki_id, n)

                self.raise_event("post_deal_damage", a_lki_id, b_lki_id, n)

    def doRegenerate(self, obj):
        obj = obj.get_object()
        self.output.regenerate(obj)
        obj.regenerated = True 

    def doDestroy(self, obj, cause=None):
        obj = obj.get_object()
        self.output.destroy(obj)

        if obj.regenerated:
            obj.tapped = True
            obj.damage = 0
            obj.regenerated = False

            # remove from combat
            self.doRemoveFromCombat(obj)
        else:
            self.doZoneTransfer(obj, self.get_graveyard(self.objects[obj.owner_id]), cause)

    def doCounter(self, obj):
        obj = obj.get_object()

        if "can't be countered" not in obj.get_state().tags:
            self.output.counter(obj)
            self.doZoneTransfer(obj, self.get_graveyard(self.objects[obj.owner_id]))
            return True

        return False

    def doSacrifice(self, obj, cause = None):
        obj = obj.get_object()
        self.output.sacrifice(obj)
        self.doZoneTransfer(obj, self.get_graveyard(self.objects[obj.owner_id]))

    def doBury(self, obj, cause = None):
        obj = obj.get_object()
        self.output.bury(obj)
        self.doZoneTransfer(obj, self.get_graveyard(self.objects[obj.owner_id]), cause)

    def doRemoveFromGame(self, obj, cause = None):
        obj = obj.get_object()
        self.output.removeFromGame(obj)
        self.doZoneTransfer(obj, self.get_removed_zone(), cause)

    def doRemoveFromCombat(self, obj):
        id = obj.get_id()
        for a in self.declared_attackers:
            if a.get_id() == id:
                self.declared_attackers.remove (a)
                break

        for b in self.declared_blockers:
            if b.get_id() == id:
                self.declared_blockers.remove (b)
                game.declared_blockers_map.remove(b.get_id())
                break

        for b in self.declared_blockers:
            blocked_ids = self.declared_blockers_map[b.get_id()]
            if obj.get_id() in blocked_ids:
                blocked_ids.remove(obj.get_id())

    def doCoinFlip(self, player):
        result = random.choice(["heads", "tails"])
        self.output.coinFlip(player.get_object(), result)
        self.process_returns_push(result)

    def delete(self, obj):

        if obj.zone_id is not None:
            self.objects[obj.zone_id].objects.remove(obj)
        obj.zone_id = None
        del self.objects[obj.id]

    def isInPlay(self, obj):
        return obj.zone_id == self.get_in_play_zone().id

    def onResolve(self, resolvable):
        self.raise_event ("resolve", resolvable)

    def onPlay(self, spell):
        self.raise_event ("play", spell)

    def replacePlayCost(self, ability, obj, player, costs):

#        self.process_returns_push(costs)

         # TODO:
        for effect in self.play_cost_replacement_effects:
            costs = effect(self, ability, obj, player, costs)

        self.process_returns_push(costs)
#        return costs

    def next(self, action):
        while True:
#            print "Stack: " + `self.process_stack` + " Returns: " + `self.process_returns_stack`

            p = self.process_stack.pop()
            ret = p.next(self, action)

            action = None

            if ret is not None:
                self.process_stack.append (p)
                return ret

    def process_push(self, process):
        assert process != None
        self.process_stack.append (process)

    def process_pop(self):
        self.process_stack.pop()

    def process_top(self):
        return self.process_stack[-1]

    def process_returns_push(self, thing):
        self.process_returns_stack.append(thing)

    def process_returns_pop(self):
        return self.process_returns_stack.pop()

    def process_returns_top(self):
        return self.process_returns_stack[-1]

    def obj(self, _id):
        return self.objects[_id]

    def lki(self, _id):
        ret = self.lkis[_id]
        ret.game = self
        return ret

    def _moveLkis(self, object, zone_from, zone_to, cause):
        for lki in self.lkis.itervalues():
            if lki.object_id == object.id:
                lki.onPreMoveObject(object, zone_from, zone_to, cause)


    def copy(self):
        from effects import ContinuousEffect
        g = Game(self.output)
        
        for key, obj in self.objects.iteritems():
            assert obj is not None

            obj_copy = obj.copy()
            g.objects[key] = obj_copy

            assert obj != obj_copy

            assert g.objects[key] is not None

        g.obj_max_id = self.obj_max_id
        for zone in self.zones:
            zone_clone = g.objects[zone.id]
            g.zones.append (zone_clone)

            zone_clone.objects = []
            for obj in zone.objects:
                zone_clone.objects.append ( g.objects[obj.id] )

            assert zone != zone_clone
            assert id(zone.objects) != id(zone_clone.objects)
            assert len(zone.objects) == len(zone_clone.objects)

        # LKIs are special, as they hold reference to the current game, we replace it here:
        for key, lki in self.lkis.iteritems():
            lki_copy = lki.copy()
            lki_copy.game = g
            g.lkis[key] = lki_copy

        g.lki_max_id = self.lki_max_id    
        
        # effect objects are special as they hold reference to the source_lki, we replace it here:
        for key, obj in g.objects.iteritems():
            if isinstance(obj, EffectObject):
                obj.source_lki = g.lkis[obj.source_lki.get_lki_id()]

        for player in self.players:
            g.players.append (g.objects[player.id])
    
        g.active_player_id = self.active_player_id
        g.current_player_priority_id = self.current_player_priority_id
        g.current_phase = self.current_phase
        g.current_step = self.current_step

        g.defending_player_id = self.defending_player_id
        g.attacking_player_id = self.attacking_player_id

        for effect in self.triggered_abilities:
            g.triggered_abilities.append (g.objects[effect.id])

        g.declared_attackers = self.declared_attackers.copy()
        g.declared_blockers = self.declared_blockers.copy()
        g.declared_blockers_map = self.declared_blockers_map.copy()

        g.output = self.output

        g.events = self.events.copy()
        g.volatile_events = self.volatile_events.copy()

        effect_map = {}

        for obj, effect in self.until_end_of_turn_effects:
            assert isinstance(effect, ContinuousEffect)
            effect_copy = copy.copy(effect)
            effect_map[effect] = effect_copy
            g.until_end_of_turn_effects.append ( (g.obj(obj.id), effect_copy ) )

        for obj, lki, effect in self.indefinite_effects:
            assert isinstance(effect, ContinuousEffect)
            effect_copy = copy.copy(effect)
            g.indefinite_effects.append ( (g.obj(obj.id), g.lki(lki.get_lki_id()), effect_copy ) )

        for e in self.end_of_combat_triggers:
            g.end_of_combat_triggers.append (g.obj(e.id))

        g.turn_number = self.turn_number

        g.revealed = self.revealed[:]

        g.looked_at = self.looked_at.copy()

        # TODO: clone the effect, change from partial to an interface
        g.play_cost_replacement_effects = self.play_cost_replacement_effects[:]

        # damage prevention effects may hold references to continuous effects that created them
        for dp in self.damage_preventions:
            dp_copy = copy.copy(dp)

            effect = dp.getEffect()
            if effect is not None and effect in effect_map:
                dp_copy.setEffect(effect_map[effect])
                
            g.damage_preventions.append(dp_copy)

        g.creature_that_attacked_this_turn_lkis = self.creature_that_attacked_this_turn_lkis.copy()

        g.additional_combat_phase_followed_by_an_additional_main_phase = self.additional_combat_phase_followed_by_an_additional_main_phase

        g.interceptable_draw = copy.copy(self.interceptable_draw)
        g.interceptable_draw.original = g._drawCard

        for process in self.process_stack:
            process_copy = copy.copy(process)
            g.process_stack.append(process_copy)

        for ret in self.process_returns_stack:
            ret_copy = None
            if isinstance(ret, LastKnownInformation):
                ret_copy = g.lki(ret.get_lki_id())
            elif isinstance(ret, Object):
                ret_copy = g.obj(ret.id)
            else:
                ret_copy = copy.copy(ret)

            g.process_returns_stack.append (ret_copy)

        g.stack = g.get_stack_zone().objects

        # game has ended
        g.end = self.end

        g.winners = self.winners.copy()
        g.losers = self.losers.copy()

        return g

