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

class Process:
    def next(self, game, action):
        pass

class SandwichProcess(Process):
    def __init__ (self):
        self.state = 0

    def next(self, game, action):
        if self.state == 0:
            self.state = 1
            game.process_push(self)
            self.pre(game)
        elif self.state == 1:
            self.state = 2
            game.process_push(self)
            self.main(game)
        else:
            self.post(game)

    def pre(self, game):
        pass

    def main(self, game):
        pass

    def post(self, game):
        pass


from selectors import *
from rules import *
from actions import *
from cost import *
from objects import *
from game import AttackerValidator, BlockerValidator

class GameEndException(Exception):
    def __init__ (self, player):
        self.player = player

def get_possible_actions (game, player):
    ret = []
    _al = AllSelector()
    for obj in _al.all(game, None):
        for ability in obj.state.abilities:
            if isinstance(ability, ActivatedAbility):
                #print "testing ability: " + `ability`
                if ability.canActivate(game, obj, player):
                    ret.append (AbilityAction(player, obj, ability, ability.get_text(game, obj)))

    return ret

def do_action (game, player, a):
    if isinstance(a, AbilityAction):
        a.ability.activate(game, a.object, player)
    else:
        raise Exception("cannot do action " + repr(a))

def resolve (game, resolvable):
    evaluate(game)

    print "XXX: " + `resolvable.rules`

    resolvable.rules.resolve(game, resolvable)

def sort_effects(effects):
    effect_groups = {}
    effect_groups["copy_chardef"] = []
    effect_groups["copy"] = []

    effect_groups["control_chardef"] = []
    effect_groups["control"] = []

    effect_groups["text_chardef"] = []
    effect_groups["text"] = []

    effect_groups["type_chardef"] = []
    effect_groups["type"] = []

    effect_groups["other_chardef"] = []
    effect_groups["other"] = []

    effect_groups["power_chardef"] = []
    effect_groups["power_set"] = []
    effect_groups["power_other"] = []
    effect_groups["power_modify"] = []
    effect_groups["power_switch"] = []
   
    nonpowerLayers = set(["copy", "control", "text", "type", "other"])
    powerLayers = set(["power_set", "power_switch", "power_modify", "power_other"])

    for source, effect in effects:
        layer = effect.getLayer()
        isEffect = isinstance(source, EffectObject)
        isSelf = effect.isSelf()
        isCharDef = (not isEffect) and isSelf

        if layer in nonpowerLayers:
            if isCharDef:
                effect_groups[layer + "_chardef"].append ( (source, effect) )
            else:
                effect_groups[layer].append( (source, effect) )
        elif layer in powerLayers:
            if layer == "power_set" and isCharDef:
                effect_groups["power_chardef"].append ( (source, effect) )
            else:
                effect_groups[layer].append( (source, effect) )
        else:
            raise Exception("Unknown layer '%s'" % layer)

    return effect_groups

def evaluate (game):
    """ evaluate all continuous effects """

    game.damage_preventions = []
    game.volatile_events = {}
    game.play_cost_replacement_effects = []

    game.reset_interceptables()

    for player in game.players:
        player.maximum_hand_size = 7
        player.land_play_limit = 1
        player.draw_cards_count = 1

    old_controller_map = {}

    original_texts_map = {}

    # clear states of all objects and evalute card texts
    _as = AllSelector ()
    for object in _as.all(game, None):

        # remember old controller so we notice controller change
        old_controller_map[object.id] = object.state.controller_id

        object.state = object.initial_state.copy ()

        # store the original text that is used to parse rules, so we can spot when the text changed
        original_texts_map[object.id] = object.state.text

        # show_to rules
        # cards in play, stack and graveyards are visible to all
        zone = game.objects.get(object.zone_id)
        if zone is not None:
            if zone.type == "in play" or zone.type == "stack" or zone.type == "graveyard" or object.get_id() in game.revealed:
                for player in game.players:
                    object.state.show_to.append(player.get_id())

            # cards in hand are visible to controllers
            if zone.type == "hand":
                object.state.show_to.append( zone.player_id )

            for player in game.players:
                if object.id in game.looked_at[player.id]:
                    object.state.show_to.append( object.controller_id )

        # some basic rules

        # taxonomy

        # 200.6
        if object.zone_id == game.get_in_play_zone().id:
            object.state.tags.add("permanent")

        # card on stack is a spell, unless it's an effect (therefore not a card)
        if object.zone_id == game.get_stack_zone().id and "effect" not in object.state.tags:
            object.state.tags.add("spell")

        # use the controller and owner property directly on the object to allow "stable" controller switch in addition to modification by effects
        object.state.controller_id = object.controller_id
        object.state.owner_id = object.owner_id

        object.rules = parse(object)

        for ability in object.rules.getAbilities():
            object.state.abilities.append (ability)

        # counters
#        for counter in object.counters:
#            if "+1/+1" == counter:
#                object.state.power += 1
#                object.state.toughness += 1
#            elif "-1/-1" == counter:
#                object.state.power -= 1
#                object.state.toughness -= 1


    # 306.2
    if game.current_phase == "combat":
        game.get_active_player().state.tags.add ("attacking")
        game.get_defending_player().state.tags.add ("defending")

        attacker_lki_map = {}

        unblocked = set()
        for obj in game.declared_attackers:
            attacker_lki_map[obj.get_id()] = obj
            obj.get_state().tags.add ("attacking")
            unblocked.add (obj)

        for obj in game.declared_blockers:

            obj.get_state().tags.add ("blocking")

            blocked_ids = game.declared_blockers_map[obj.get_id()]
            for blocked_id in blocked_ids:
                blocked_lki = attacker_lki_map[blocked_id]
                blocked_lki.get_state().tags.add ("blocked")

                if blocked_lki in unblocked:
                    unblocked.remove (blocked_lki)

        for obj in unblocked:
            obj.get_state().tags.add ("unblocked")

    # colors
    _as = AllSelector()
    for object in _as.all(game, None):
        if object.state.manacost is not None:
            if "R" in object.state.manacost:
                object.state.tags.add("red")
            if "G" in object.state.manacost:
                object.state.tags.add("green")
            if "U" in object.state.manacost:
                object.state.tags.add("blue")
            if "B" in object.state.manacost:
                object.state.tags.add("black")
            if "W" in object.state.manacost:
                object.state.tags.add("white")

    all_effects = []
    _as = AllSelector ()
    for object in _as.all(game, None):
        for ability in object.state.abilities:
            if isinstance(ability, StaticAbility):
                if ability.isActive(game, object):
                    for effect in ability.getEffects():
                        all_effects.append ( (object, effect) )

    # until end of turn effects
    for source, effect in game.until_end_of_turn_effects:
        all_effects.append ( (source, effect) )

    # indefinite effects
    indefinite_effects = []
    for source, lki, effect in game.indefinite_effects:
        if lki.is_valid():
            all_effects.append ( (source, effect) )
            indefinite_effects.append ( (source, lki, effect) )

    game.indefinite_effects = indefinite_effects

    effect_groups = sort_effects(all_effects)

    #layer_order = ["copy_chardef", "copy", "control_chardef", "control", "text_chardef", "text", "type_chardef", "type", "other_chardef", "other", "power_chardef", "power_other"]
    layer_order = ["copy_chardef", "copy", "control_chardef", "control", "text_chardef", "text"]
    for layer in layer_order:
        for source, effect in effect_groups[layer]:
            effect.apply(game, source)

    # reparse changed effects
    for object in _as.all(game, None):
        if original_texts_map[object.id] != object.state.text:

            print "XXX: reparsing changed text '%s'" % object.state.text

            object.rules = parse(object)
            # we can safely replace, as no abilities can be added/removed in copy, control or text layers
            object.state.abilities = object.rules.getAbilities()

    # Do the second pass of effects
    all_effects = []
    _as = AllSelector ()
    for object in _as.all(game, None):
        for ability in object.state.abilities:
            if isinstance(ability, StaticAbility):
                if ability.isActive(game, object):
                    for effect in ability.getEffects():
                        all_effects.append ( (object, effect) )

    # until end of turn effects
    for source, effect in game.until_end_of_turn_effects:
        all_effects.append ( (source, effect) )

    # indefinite effects
    for source, lki, effect in game.indefinite_effects:
        all_effects.append ( (source, effect) )

    effect_groups = sort_effects(all_effects)

    layer_order = ["type_chardef", "type", "other_chardef", "other", "power_chardef", "power_other"]
    for layer in layer_order:
        for source, effect in effect_groups[layer]:
            effect.apply(game, source)

    # counters
    _as = AllSelector()
    for object in _as.all(game, None):
        for counter in object.counters:
            if "+1/+1" == counter:
                object.state.power += 1
                object.state.toughness += 1
            elif "-1/-1" == counter:
                object.state.power -= 1
                object.state.toughness -= 1


    layer_order = ["power_modify", "power_switch"]
    for layer in layer_order:
        for source, effect in effect_groups[layer]:
            effect.apply(game, source)

    # register triggered abilities' triggers
    _as = AllSelector ()
    for object in _as.all(game, None):
        for ability in object.state.abilities:
            if isinstance(ability, TriggeredAbility):
                if ability.isActive(game, object):
                    for event, callback in ability.getEventHandlers(game, object):
                        game.add_volatile_event_handler(event, callback)

            elif isinstance(ability, StateBasedAbility):
                if ability.isActive(game, object):
                    ability.register(game, object)

    # state based effects
    _ap = AllPermanentSelector()
    for object in _ap.all(game, None):
        if "creature" in object.state.types:
            if object.damage >= object.state.toughness:
                game.doDestroy(object)

            if old_controller_map[object.id] != None and old_controller_map[object.id] != object.state.controller_id:
                # controller change, add summoning sickness
                object.initial_state.tags.add("summoning sickness")
                object.state.tags.add("summoning sickness")

        if "token" in object.state.tags and object.zone_id != game.get_in_play_zone().id:
            game.doRemoveFromGame(object)

    # Playing lands
    _al = AllTypeSelector("land")
    for land in _al.all(game, None):
        land.state.abilities.append (PlayLandAbility())

    # lands
    for obj in _as.all(game, None):
        if "land" in obj.state.types:
            if "forest" in obj.state.subtypes:
                obj.state.abilities.append (BasicManaAbility("G"))
            if "island" in obj.state.subtypes:
                obj.state.abilities.append (BasicManaAbility("U"))
            if "plains" in obj.state.subtypes:
                obj.state.abilities.append (BasicManaAbility("W"))
            if "swamp" in obj.state.subtypes:
                obj.state.abilities.append (BasicManaAbility("B"))
            if "mountain" in obj.state.subtypes:
                obj.state.abilities.append (BasicManaAbility("R"))

    lost = []
    for player in game.players:
        if player.life <= 0:
            lost.append (player)

    if len(lost) == 1:
        for player in game.players:
            if player != lost[0]:
                raise GameEndException(player)
    elif len(lost) > 1:
        raise GameEndException(None)


class PayCostProcess(Process):
    def __init__ (self, player, obj, effect, costs):
        self.player_id = player.id
        self.obj_id = obj.id
        self.effect_id = effect.id
        self.notpaid = costs

        self.state = 0
   
    def next(self, game, action):
        if self.state == 0:
            if len(self.notpaid) > 0:

                self.state = 1

                player = game.obj(self.player_id)
                obj = game.obj(self.obj_id)

                actions = []
                _pass = PassAction (player)
                _pass.text = "Cancel"
                actions.append (_pass)

                _al = AllSelector()
                for o in _al.all(game, None):
                    for ability in o.state.abilities:
                        if isinstance(ability, ManaAbility):
                            if ability.canActivate(game, o, player):
                                actions.append (AbilityAction(player, o, ability, ability.get_text(game, o)))

                for cost in self.notpaid:
                    if cost.canPay(game, obj, player):
                        actions.append (PayCostAction(player, cost, cost.get_text(game, obj, player)))

                _as = ActionSet (game, player, "Play Mana Abilities", actions)
                return _as
            else:
                game.process_returns_push(True) 

        elif self.state == 1:
            if isinstance(action, PassAction):
                game.process_returns_push(False)
            else:

                player = game.obj(self.player_id)
                obj = game.obj(self.obj_id)
                effect = game.obj(self.effect_id)

                self.state = 0
                game.process_push(self)

                if isinstance(action, PayCostAction):
                    if action.cost.pay(game, obj, effect, player):
                        self.notpaid.remove(action.cost)

                if isinstance(action, AbilityAction):
                    do_action (game, player, action) 
        
# DONE
def process_pay_cost (game, player, obj, effect, costs):
    notpaid = costs
    while len(notpaid) > 0:
        actions = []

        _pass = PassAction (player)
        _pass.text = "Cancel"
        actions.append (_pass)

        _al = AllSelector()
        for o in _al.all(game, None):
            for ability in o.state.abilities:
                if isinstance(ability, ManaAbility):
                    if ability.canActivate(game, o, player):
                        actions.append (AbilityAction(player, o, ability, ability.get_text(game, o)))

        for cost in notpaid:
            if cost.canPay(game, obj, player):
                actions.append (PayCostAction(player, cost, cost.get_text(game, obj, player)))

        _as = ActionSet (game, player, "Play Mana Abilities", actions)
        a = game.input.send (_as)

        if a == _pass:
            return False

        if isinstance(a, PayCostAction):
            if a.cost.pay(game, obj, effect, player):
                notpaid.remove(a.cost)

        if isinstance(a, AbilityAction):
            do_action (game, player, a)

    return True

class AbstractPlayProcess(Process):
    def __init__ (self, ability, player):
        self.ability = ability
        self.player_id = player.id
        self.state = 0

    def getSelfObject(self, game):
        # e.g. object with an activated ability, same as object for ordinary spells
        pass

    def getObject(self, game):
        # e.g. an effect object representing an activated ability on the stack.  same as selfObject for ordinary spells
        pass

    def onPlay(self, game):
        game.onPlay(self.getObject(game))

    def next(self, game, action):
        if self.state == 0:
            # TODO save the game state before the playing spell and return to it if it failed to select targets

            obj = self.getObject(game)
            if obj.zone_id is not None:
                # move to stack
                obj = game.objects[self.obj_id]
                zone_from = game.objects[obj.zone_id]

                stack = game.get_stack_zone()
                obj.zone_id = stack.id
                zone_from.objects.remove(obj)
                stack.objects.append (obj)
            else:
                stack = game.get_stack_zone()
                obj.zone_id = stack.id
                stack.objects.append (obj)

            self.state = 1
            game.process_push(self)

            evaluate(game)

        elif self.state == 1:
            self.state = 2
            game.process_push(self)

            player = game.objects[self.player_id]
            obj = self.getObject(game)
            obj.rules.selectTargets(game, player, obj)

        elif self.state == 2:
            if not game.process_returns_pop():
                # TODO: return state to the before playing spell if target selection failed
                return

            self.state = 3
            game.process_push(self)

            player = game.objects[self.player_id]
            obj = self.getObject(game)
            
            self.ability.determineCost(game, obj, player)

        elif self.state == 3:
            self.state = 4
            game.process_push(self)

            costs = game.process_returns_pop()
            costs = costs[:]

            player = game.objects[self.player_id]
            obj = self.getObject(game)

            game.replacePlayCost(self.ability, obj, player, costs)

        elif self.state == 4:
            self.state = 5
            game.process_push(self)

            player = game.objects[self.player_id]
            obj = self.getObject(game)
            selfObj = self.getSelfObject(game)

            costs = game.process_returns_pop()

            if len(costs) > 0:
                game.process_push(PayCostProcess(player, selfObj, obj, costs))

        elif self.state == 5:
            payed = game.process_returns_pop()

            obj = self.getObject(game)

            if not payed:
                # TODO: return to the previus game state
                pass
            else:
                self.onPlay(game)


class PlaySpellProcess(AbstractPlayProcess):
    def __init__ (self, ability, player, obj):
        AbstractPlayProcess.__init__ (self, ability, player)
        self.obj_id = obj.id

    def getObject(self, game):
        return game.obj(self.obj_id)

    def getSelfObject(self, game):
        return game.obj(self.obj_id)

class ActivateTappingAbilityProcess(AbstractPlayProcess):
    def __init__ (self, ability, player, obj, effect):
        AbstractPlayProcess.__init__ (self, ability, player)
        self.self_obj_id = obj.id
        self.effect = effect
        self.obj_id = None

    def getObject(self, game):
        if self.obj_id is None:
            selfObj = self.getSelfObject(game)
            e = game.create_effect_object (LastKnownInformation(game, selfObj), self.player_id, self.effect, {})
            self.obj_id = e.id
       
        return game.obj(self.obj_id)

    def getSelfObject(self, game):
        return game.obj(self.self_obj_id)

    def onPlay(self, game):
        game.doTap(self.getSelfObject(game))
        game.onPlay(self.getObject(game))


def process_activate_ability(game, ability, player, obj, effect):

    e = game.create_effect_object (LastKnownInformation(game, obj), player.id, effect, {})

    stack = game.get_stack_zone()
    e.zone_id = stack.id
    stack.objects.append (e)

    evaluate(game)

    if not e.rules.selectTargets(game, player, e):
        game.delete(e)
        return

    costs = ability.determineCost(game, obj, player)
    costs = costs[:]
    # cost = ability.get_cost(game, player, obj)
    if len(costs) > 0:
        if not process_pay_cost(game, player, obj, e, costs):

            print("not payed, returning to previous state")
            game.delete(e)
            return

    game.onPlay(obj)


class PrioritySuccessionProcess(Process):
    def __init__ (self, player):
        self.player_id = player.id
        self.state = 0
        self.first_passed_id = None

    def next(self, game, action):
        if self.state == 0:
            game.current_player_priority = game.obj(self.player_id)
            self.first_passed_id = None
            self.state = 1
            game.process_push(self)
        elif self.state == 1:
            for ability in game.triggered_abilities:
                game.stack_push (ability)
            game.triggered_abilities = []

            self.state = 2
            game.process_push(self)

            evaluate(game)
        elif self.state ==2:
            actions = []
            _pass = PassAction (game.current_player_priority)
            actions.append (_pass)

            actions.extend(get_possible_actions (game, game.current_player_priority))
            _as = ActionSet (game, game.current_player_priority, "You have priority", actions)

            self.state = 3

            return _as
        elif self.state == 3:
            if not isinstance(action, PassAction):
                self.state = 1
                game.process_push(self)
                self.first_passed_id = None
                do_action (game, game.current_player_priority, action)
            else:
                np = game.get_next_player (game.current_player_priority)
                if self.first_passed_id == np.id:
                    if game.get_stack_length () == 0:
                        return
                    else:
                        self.state = 4
                        game.process_push(self)
                        resolve (game, game.stack_top ())
                else:
                    if self.first_passed_id == None:
                        self.first_passed_id = game.current_player_priority.id
                    game.current_player_priority = np

                    self.state = 1
                    game.process_push(self)

        elif self.state == 4:

            # have the spell resolution succeeded?
            game.process_returns_pop()

            self.first_passed_id = None
            game.current_player_priority = game.obj(self.player_id)

            self.state = 1
            game.process_push(self)


class UntapProcess(Process):
    def __init__ (self, permanent):
        self.permanent_id = permanent.id

    def next(self, game, action):
        game.doUntap(game.obj(self.permanent_id))

class DrawCardProcess(Process):
    def next(self, game, action):
        game.doDrawCard(player)

class PrePhaseProcess(Process):
    def next(self, game, action):
        game.current_step = ""
        evaluate(game)

class PostPhaseProcess(Process):
    def next(self, game, action):
        # 300.3
        for player in game.players:
            converted_mana = mana_converted_cost(player.manapool)
            if converted_mana > 0:
                howmuch = converted_mana
                print("manaburn %d" % (howmuch))
                player.manapool = ""
                game.doLoseLife(player, howmuch)

        evaluate(game)

class PreStepProcess(Process):
    def next(self, game, action):
        evaluate(game)
        game.raise_event("step")

class PostStepProcess(Process):
    def next(self, game, action):
        evaluate(game)

class UntapStepProcess(SandwichProcess):
    def __init__ (self):
        SandwichProcess.__init__ (self)

    def pre(self, game):
        game.current_step = "untap"
        game.process_push(PreStepProcess())

    def main(self, game):
        selector = PermanentPlayerControlsSelector (game.get_active_player())
        for permanent in selector.all (game, None):
            if "does not untap" not in permanent.state.tags:
                game.process_push(UntapProcess(permanent))

    def post(self, game):
        game.process_push(PostStepProcess())


class UpkeepStepProcess(SandwichProcess):
    """ 303.1 """

    def __init__ (self):
        SandwichProcess.__init__ (self)

    def pre(self, game):
        game.current_step = "upkeep"
        game.process_push(PreStepProcess())

    def main(self, game):
        for ability in game.triggered_abilities:
            game.stack_push (ability)
        game.triggered_abilities = []

        game.process_push(PrioritySuccessionProcess(game.get_active_player()))

    def post(self, game):
        game.process_push(PostStepProcess())


class DrawStepProcess(SandwichProcess):
    """ 304.1 """
    def __init__ (self):
        SandwichProcess.__init__ (self)

    def pre(self, game):
        game.current_step = "draw"
        game.process_push(PreStepProcess())

    def main(self, game):
        game.process_push(DrawCardProcess(game.get_active_player()))

    def post(self, game):
        for ability in game.triggered_abilities:
            game.stack_push (ability)
        game.triggered_abilities = []

        game.process_push(PostStepProcess())
        game.process_push(PrioritySuccessionProcess(game.get_active_player()))


class BeginningPhaseProcess(SandwichProcess):
    def __init__ (self):
        SandwichProcess.__init__ (self)

    def pre(self, game):
        game.current_phase = "beginning"
        game.process_push(PrePhaseProcess())

    def main(self, game):
        # remove the summoning sickness tag
        selector = PermanentPlayerControlsSelector (game.get_active_player())
        for permanent in selector.all (game, None):
            if "summoning sickness" in permanent.initial_state.tags:
                permanent.initial_state.tags.remove("summoning sickness")

        # 101.6a
        if not (game.turn_number == 0 and game.get_active_player() == game.players[0]):
            game.process_push(DrawStepProcess())

        game.process_push(UpkeepStepProcess())
        game.process_push(UntapStepProcess())

    def post(self, game):
        game.process_push(PostPhaseProcess())


class MainPhaseProcess(SandwichProcess):
    def __init__ (self, which):
        SandwichProcess.__init__ (self)
        self.which = which

    def pre(self, game):
        game.current_phase = self.which
        game.process_push(PrePhaseProcess())

    def main(self, game):
        for ability in game.triggered_abilities:
            game.stack_push (ability)
        game.triggered_abilities = []

        game.process_push(PrioritySuccessionProcess(game.get_active_player()))
    
    def post(self, game):
        game.process_push(PostPhaseProcess())

class BeginningOfCombatStepProcess(SandwichProcess):
    def __init__(self):
        SandwichProcess.__init__ (self)

    def pre(self, game):
        game.current_step = "beginning of combat"
        game.process_push(PreStepProcess())

    def main(self, game):
        for ability in game.triggered_abilities:
            game.stack_push (ability)
        game.triggered_abilities = []

        game.process_push(PrioritySuccessionProcess(game.get_active_player()))

    def post(self, game):
        game.process_push(PostPhaseProcess())
        
# DONE?
def process_step_beginning_of_combat (game):
    game.current_step = "beginning of combat"
    process_step_pre (game)
    for ability in game.triggered_abilities:
        game.stack_push (ability)
    game.triggered_abilities = []

    process_priority_succession (game, game.get_active_player())

    process_step_post (game)


class DeclareAttackersStepProcess(Process):
    def __init__ (self):
        self.state = 0
        self.valid = False
        self.attackers = set()

    def next(self, game, action):
        if self.state == 0:
            game.current_step = "declare attackers"

            self.state = 1
            self.valid = False

            game.process_push(self)
            game.process_push(PreStepProcess())

        elif self.state == 1:
            if self.valid:
                self.state = 5
                game.process_push(self)
            else:
                self.attackers = set()
                self.state = 2
                game.process_push(self)

        elif self.state == 2:

            self.state = 3

            actions = []
            _pass = PassAction (game.get_attacking_player())
            _pass.text = "No more attackers"
            actions.append (_pass)

            selector = PermanentPlayerControlsSelector(game.get_attacking_player())
            for permanent in selector.all(game, None):
                if "creature" in permanent.state.types and not permanent.tapped and ("haste" in permanent.state.tags or not "summoning sickness" in permanent.state.tags) and permanent.id not in self.attackers and "can't attack" not in permanent.state.tags and "can't attack or block" not in permanent.state.tags and ("defender" not in permanent.state.tags or "can attack as though it didn't have defender" in permanent.state.tags):

                    v = AttackerValidator(permanent, True)
                    game.raise_event("validate_attacker", v)
                    if v.can:
                        _p = Action ()
                        _p.object = permanent
                        _p.player = game.get_attacking_player()
                        _p.text = "Attack with %s" % permanent
                        actions.append (_p)

            _as = ActionSet (game, game.get_attacking_player(), "Select attackers", actions)
            return _as

        elif self.state == 3:
            if isinstance(action, PassAction):
                self.state = 4
                game.process_push(self)
            else:
                self.attackers.add(action.object.id)
                self.state = 2
                game.process_push(self)

        elif self.state == 4:
            self.valid = validate_attack(game, self.attackers)
            self.state = 1
            game.process_push(self)

        elif self.state == 5:
            for a in self.attackers:
                a_lki = LastKnownInformation(game, game.obj(a))
                game.declared_attackers.add (a_lki)
                game.creature_that_attacked_this_turn_lkis.add (a_lki)

            # tap attacking creatures
            for a in game.declared_attackers:
                if "vigilance" not in a.get_state().tags:
                    game.doTap(a.get_object())

            # attacks event
            for a in game.declared_attackers:
                game.raise_event("attacks", a)

            for ability in game.triggered_abilities:
                game.stack_push (ability)

            game.triggered_abilities = []

            self.state = 6
            game.process_push(self)
            game.process_push(PrioritySuccessionProcess(game.get_active_player()))

        elif self.state == 6:
            # remove the moved declared attackers
            torm = []
            for attacker in game.declared_attackers:
                if attacker.is_moved():
                    torm.append (attacker)
            for attacker in torm:
                game.declared_attackers.remove(attacker)
        
            game.process_push(PostStepProcess())


def process_step_declare_attackers (game):
    game.current_step = "declare attackers"
    process_step_pre (game)

    valid = False
    while not valid:
        # select attackers
        attackers = set()
        while True:

            actions = []
            _pass = PassAction (game.get_attacking_player())
            _pass.text = "No more attackers"
            actions.append (_pass)

            selector = PermanentPlayerControlsSelector(game.get_attacking_player())
            for permanent in selector.all(game, None):
                if "creature" in permanent.state.types and not permanent.tapped and ("haste" in permanent.state.tags or not "summoning sickness" in permanent.state.tags) and permanent not in attackers and "can't attack" not in permanent.state.tags and "can't attack or block" not in permanent.state.tags and ("defender" not in permanent.state.tags or "can attack as though it didn't have defender" in permanent.state.tags):

                    v = AttackerValidator(permanent, True)
                    game.raise_event("validate_attacker", v)
                    if v.can:
                        _p = Action ()
                        _p.object = permanent
                        _p.player = game.get_attacking_player()
                        _p.text = "Attack with %s" % permanent
                        actions.append (_p)

            _as = ActionSet (game, game.get_attacking_player(), "Select attackers", actions)
            a = game.input.send (_as)

            if a != _pass:
                attackers.add (a.object)
            else:
                break

        valid = validate_attack(game, attackers)
    for a in attackers:
        a_lki = LastKnownInformation(game, a)
        game.declared_attackers.add (a_lki)
        game.creature_that_attacked_this_turn_lkis.add (a_lki)

    # tap attacking creatures
    for a in game.declared_attackers:
        if "vigilance" not in a.get_state().tags:
            game.doTap(a.get_object())

    # attacks event
    for a in game.declared_attackers:
        game.raise_event("attacks", a)

    for ability in game.triggered_abilities:
        game.stack_push (ability)
    game.triggered_abilities = []

    process_priority_succession (game, game.get_active_player())

    # remove the moved declared attackers
    torm = []
    for attacker in game.declared_attackers:
        if attacker.is_moved():
            torm.append (attacker)
    for attacker in torm:
        game.declared_attackers.remove(attacker)

    process_step_post (game)


def validate_attack(game, attacker_ids):

    for attacker_id in attacker_ids:
        attacker = game.obj(attacker_id)
        if "can't attack unless a creature with greater power also attacks" in attacker.get_state().tags:
            isSuch = False
            for other_attacker_id in attacker_ids:
                if attacker_id != other_attacker_id:
                    other_attacker = game.obj(other_attacker_id)
                    if other_attacker.get_state().power > attacker.get_state().power:
                        isSuch = True
                        break

            if not isSuch:
                return False

    return True

# this is a not a formal validation, just a "shortcut" to disallow obvious evasion abilities
# per rules, only the whole set of blocks is validated, not individual blocks.
def is_valid_block(game, attacker, blocker):
    if "flying" in attacker.get_state().tags and "flying" not in blocker.get_state().tags and "reach" not in blocker.get_state().tags:
        print("%s cannot block %s because of the flying evasion rule" % (blocker, attacker))
        return False

    if "fear" in attacker.get_state().tags and "artifact" not in blocker.get_state().types and "black" not in blocker.get_state().tags:
        print("%s cannot block %s because of the fear evasion rule" % (blocker, attacker))
        return False

    if "can't be blocked except by walls" in attacker.get_state().tags and "wall" not in blocker.get_state().subtypes:
        print("%s cannot block %s because of the invisibility evasion rule" % (blocker, attacker))
        return False

    if "can't block" in blocker.get_state().tags or "can't attack or block" in blocker.get_state().tags:
        return False

    if "unblockable" in attacker.get_state().tags:
        return False

    if "mountainwalk" in attacker.get_state().tags:
        if not SubtypeYouControlSelector("mountain").empty(game, blocker):
            return False

    if "forestwalk" in attacker.get_state().tags:
        if not SubtypeYouControlSelector("forest").empty(game, blocker):
            return False

    if "plainswalk" in attacker.get_state().tags:
        if not SubtypeYouControlSelector("plains").empty(game, blocker):
            return False

    if "islandwalk" in attacker.get_state().tags:
        if not SubtypeYouControlSelector("island").empty(game, blocker):
            return False

    if "swampwalk" in attacker.get_state().tags:
        if not SubtypeYouControlSelector("swamp").empty(game, blocker):
            return False

    v = BlockerValidator(attacker, blocker, True)
    game.raise_event("validate_blocker", v)
    if not v.can:
        return False

    # lure
    # warning, this can turn into a recursive hell, if not taken care
    if "lure" not in attacker.get_state().tags:
        for a2 in game.declared_attackers:
            if "lure" in a2.get_state().tags and "can't be blocked except by three or more creatures" not in attacker.get_state().tags and "can't be blocked except by two or more creatures" not in attacker.get_state().tags:
                if is_valid_block(game, a2, blocker):
                    print("%s cannot block %s because there is a valid lure %s" % (blocker, attacker, a2))
                    return False

    return True

def validate_block(game, blockers, blockers_map):

    blockers_inv_map = {}

    # evasion abilities
    for blocker_id, attacker_ids in blockers_map.items():
        blocker = game.objects[blocker_id]

        # we normally allow only one attacker per blocker
        if len(attacker_ids) > 1:
            if "can block any number of creatures" not in blocker.state.tags:
                if len(attacker_ids) == 2 and "can block an additional creature" in blocker.state.tags:
                    pass
                else:
                    return False

        for attacker_id in attacker_ids:
            attacker = game.obj(attacker_id)
            if not is_valid_block(game, attacker, blocker):
                return False

        if "can't block unless a creature with greater power also blocks" in blocker.get_state().tags:
            isSuch = False
            for other_blocker in blockers:
                if blocker != other_blocker:
                    if other_blocker.get_state().power > blocker.get_state().power:
                        isSuch = True
                        break

            if not isSuch:
                return False

        for attacker_id in attacker_ids:
            lst = blockers_inv_map.get(attacker_id, [])
            lst.append (blocker)
            blockers_inv_map[attacker_id] = lst

    for attacker_id, a_blockers in blockers_inv_map.items():
        attacker = game.obj(attacker_id)
        if "can't be blocked except by three or more creatures" in attacker.get_state().tags:
            if len(a_blockers) > 0 and len(a_blockers) < 3:
                return False

        if "can't be blocked except by two or more creatures" in attacker.get_state().tags:
            if len(a_blockers) > 0 and len(a_blockers) < 2:
                return False

    # check for lures and that all creature able to block are blocking them are blocking something
    for attacker in game.declared_attackers:
        if "lure" in attacker.get_state().tags and "can't be blocked except by three or more creatures" not in attacker.get_state().tags and "can't be blocked except by two or more creatures" not in attacker.get_state().tags:
            selector = PermanentPlayerControlsSelector(game.get_defending_player())
            for permanent in selector.all(game, None):
                if "creature" not in permanent.state.types:
                    continue
                if permanent.tapped:
                    continue
                if permanent in blockers:

                    blocked = blockers_map.get(permanent.id, [])

                    if "can block any number of creatures" not in permanent.state.tags:
                        if len(blocked) == 1 and "can block an additional creature" in permanent.state.tags:
                            pass
                        else:
                            continue

                if is_valid_block(game, attacker, permanent):
                    print("Invalid block, %s not blocking a lure" % permanent)
                    return False

    return True

class DeclareBlockersStepProcess(Process):
    def __init__ (self):
        self.state = 0

        self.blocker_id = None
        self.blockers = set()
        self.blockers_map = {}

    def next(self, game, action):
        if self.state == 0:
            game.current_step = "declare blockers"

            self.state = 2
            game.process_push(self)
            game.process_push(PreStepProcess())

#        elif self.state == 1:
#            if self.valid:
#                self.state = XXX
#                game.process_push(self)
#            else:
#                self.state = 2
#                game.process_push(self)

        elif self.state == 2:
            self.blockers = set()
            self.blockers_map = {}

            self.state = 3
            game.process_push(self)

        elif self.state == 3:

            self.state = 4

            self.blocker_id = None

            actions = []
            _pass = PassAction (game.get_defending_player())
            _pass.text = "No more blockers"
            actions.append (_pass)

            selector = PermanentPlayerControlsSelector(game.get_defending_player())
            for permanent in selector.all(game, None):
                if "creature" not in permanent.state.types:
                    continue
                if permanent.tapped:
                    continue
                if permanent.id in self.blockers:
                    blocked = self.blockers_map.get(permanent.id, [])

                    if "can block any number of creatures" not in permanent.state.tags:
                        if len(blocked) == 1 and "can block an additional creature" in permanent.state.tags:
                            pass
                        else:
                            continue

                _p = Action ()
                _p.object = permanent
                _p.player = game.get_defending_player()
                _p.text = "Block with %s" % permanent
                actions.append (_p)

            _as = ActionSet (game, game.get_defending_player(), "Select blockers", actions)
            return _as

        elif self.state == 4:
            if isinstance(action, PassAction):
                self.state = 6
                game.process_push(self)
            else:

                self.blocker_id = action.object.id
                blocker = game.obj(self.blocker_id)

                self.state = 5

                actions = []
                _pass = PassAction (game.get_defending_player())
                _pass.text = "Cancel block"
                actions.append (_pass)

                selector = AllPermanentSelector()
                for permanent in selector.all(game, None):
                    if "attacking" in permanent.state.tags:
                        # cannot block the same object more than once
                        if permanent.id in self.blockers_map.get(self.blocker_id, []):
                            continue

                        if is_valid_block(game, permanent, blocker):
                            _p = Action ()
                            _p.object = permanent
                            _p.player = game.get_defending_player()
                            _p.text = "Let %s block %s" % (blocker, permanent)
                            actions.append (_p)
                _as = ActionSet (game, game.get_defending_player(), "Block which attacker", actions) 
                return _as

        elif self.state == 5:
            if isinstance(action, PassAction):
                self.state = 3
                game.process_push(self)
            else:
                self.blockers.add (self.blocker_id)

                _as = self.blockers_map.get(self.blocker_id, [])
                self.blockers_map[self.blocker_id] = _as + [action.object.id]

                self.state = 6
                game.process_push(self)

        elif self.state == 6:
            valid = validate_block(game, self.blockers, self.blockers_map)
            if not valid:
                self.state = 2
                game.process_push(self)
            else:
                for b_id in self.blockers:
                    b = game.obj(b_id)
                    b_lki = LastKnownInformation(game, b)
                    game.declared_blockers.add (b_lki)
                    game.declared_blockers_map[b_id] = self.blockers_map[b_id][:]

                process_raise_blocking_events(game)

                for ability in game.triggered_abilities:
                    game.stack_push (ability)

                game.triggered_abilities = []

                self.state = 7
                game.process_push(self)
                game.process_push(PrioritySuccessionProcess(game.get_active_player()))

        elif self.state == 7:
            # remove the moved declared attackers
            torm = []
            for attacker in game.declared_attackers:
                if attacker.is_moved():
                    torm.append (attacker)
            for attacker in torm:
                game.declared_attackers.remove(attacker)

            game.process_push(PostStepProcess())
   
# DONE ?
def process_step_declare_blockers (game):
    game.current_step = "declare blockers"
    process_step_pre (game)
    # select blockers

    valid = False
    while not valid:
        blockers = set()
        blockers_map = {}

        # TODO: save the game state

        while True:

            actions = []
            _pass = PassAction (game.get_defending_player())
            _pass.text = "No more blockers"
            actions.append (_pass)

            selector = PermanentPlayerControlsSelector(game.get_defending_player())
            for permanent in selector.all(game, None):
                if "creature" not in permanent.state.types:
                    continue
                if permanent.tapped:
                    continue
                if permanent in blockers:
                    blocked = blockers_map.get(permanent.id, [])

                    if "can block any number of creatures" not in permanent.state.tags:
                        if len(blocked) == 1 and "can block an additional creature" in permanent.state.tags:
                            pass
                        else:
                            continue

                _p = Action ()
                _p.object = permanent
                _p.player = game.get_defending_player()
                _p.text = "Block with %s" % permanent
                actions.append (_p)

            _as = ActionSet (game, game.get_defending_player(), "Select blockers", actions)
            b = game.input.send (_as)

            if b != _pass:

                actions = []
                _pass = PassAction (game.get_defending_player())
                _pass.text = "Cancel block"
                actions.append (_pass)

                selector = AllPermanentSelector()
                for permanent in selector.all(game, None):
                    if "attacking" in permanent.state.tags:
                        # cannot block the same object more than once
                        if permanent in blockers_map.get(b.object.id, []):
                            continue

                        if is_valid_block(game, permanent, b.object):
                            _p = Action ()
                            _p.object = permanent
                            _p.player = game.get_defending_player()
                            _p.text = "Let %s block %s" % (b.object, permanent)
                            actions.append (_p)
                _as = ActionSet (game, game.get_defending_player(), "Block which attacker", actions)
                a = game.input.send (_as)

                if a != _pass:
                    blockers.add (b.object)

                    _as = blockers_map.get(b.object.id, [])
                    blockers_map[b.object.id] = _as + [a.object]
                else:
                    pass
            else:
                break

        valid = validate_block(game, blockers, blockers_map)

    for b in blockers:
        b_lki = LastKnownInformation(game, b)
        game.declared_blockers.add (b_lki)
        game.declared_blockers_map[b.id] = map(lambda x:x.id, blockers_map[b.id])

    process_raise_blocking_events(game)

    for ability in game.triggered_abilities:
        game.stack_push (ability)

    game.triggered_abilities = []

    process_priority_succession (game, game.get_active_player())

    # remove the moved declared attackers
    torm = []
    for attacker in game.declared_attackers:
        if attacker.is_moved():
            torm.append (attacker)
    for attacker in torm:
        game.declared_attackers.remove(attacker)

    process_step_post (game)

def process_raise_blocking_events(game):
    attacker_lki_map = {}

    for obj in game.declared_attackers:
        attacker_lki_map[obj.get_id()] = obj

    for obj in game.declared_blockers:
        blocked_ids = game.declared_blockers_map[obj.get_id()]
        for blocked_id in blocked_ids:
            blocked_lki = attacker_lki_map[blocked_id]

            game.raise_event("blocks", obj, blocked_lki)

class CombatDamageStepProcess(Process):
    # TODO: cleanup, factor

    def __init__ (self, firstStrike):
        self.firstStrike = firstStrike
        self.state = 0

        # map attacker id to list of blocker ids that block the attacker
        self.a_id2b_ids = []
        # map blocker id to list of attacker ids it blocks
        self.b_id2a_ids = []

        # map object ids to object last known information
        # TODO: store id2lki globally in game somewhere...
        self.id2lki = {}

        self.i = 0
        self.damage = []

        self.damageToAssign = 0
 
    def next(self, game, action):
        if self.state == 0:
            game.current_step = "combat damage"
            
            self.state = 1
            game.process_push(self)

            game.process_push(PreStepProcess())

        elif self.state == 1:
            a_id2b_ids = {}
            b_id2a_ids = {}

            self.damage = []

            # Init the maps... for attackers
            for a in game.declared_attackers:
                # declared_attackers is an LastKnownInformation
                _id = a.get_object().id
                self.id2lki[_id] = a
                a_id2b_ids[_id] = []

            # ...and for blockers...
            for b in game.declared_blockers:
                _id = b.get_object().id
                self.id2lki[_id] = b

                b_id2a_ids[_id] = []

                # the declared_blockers_map map blocker id to the attacker ids it
                # blocks
                a_ids = game.declared_blockers_map[b.get_object().id]

                for a_id in a_ids:
                    a_id2b_ids[a_id].append (_id)
                    b_id2a_ids[_id].append (a_id)

            self.i = 0

            self.a_id2b_ids = a_id2b_ids.items()
            self.b_id2a_ids = b_id2a_ids.items()

            self.state = 2
            game.process_push(self)

        elif self.state == 2:
            if self.i >= len(self.a_id2b_ids):
                self.i = 0
                self.state = 6
                game.process_push(self)
            else:
                a_id, b_ids = self.a_id2b_ids[self.i]

                a_lki = self.id2lki[a_id]
                a_obj = self.id2lki[a_id].get_object()
                a_state = self.id2lki[a_id].get_state()

                # only creatures deal combat damage
                if not a_lki.is_moved() and "creature" in a_state.types and ((self.firstStrike and "first strike" in a_lki.get_state().tags) or (not self.firstStrike and "first strike" not in a_lki.get_state().tags) or (self.firstStrike and "double strike" in a_lki.get_state().tags)):
                    if len(b_ids) == 0:
                        # unblocked creature deal damage to the defending player
                        self.damage.append ( (a_lki, LastKnownInformation(game, game.get_defending_player()), a_state.power) )

                        self.i += 1
                        game.process_push(self)
                    else:
                        if "x-sneaky" in a_lki.get_state().tags:
                            self.state = 3
                            game.process_push(self)
                        else:
                            self.state = 4
                            game.process_push(self)

                else:
                    self.i += 1
                    game.process_push(self)

        elif self.state == 3:
            # x-sneaky
            a_id, b_ids = self.a_id2b_ids[self.i]
            a_lki = id2lki[a_id]
            a_obj = self.id2lki[a_id].get_object()
            a_state = self.id2lki[a_id].get_state()

            if action is None:
                actions = []
                _yes = Action()
                _yes.text = "Yes"
                actions.append (_yes)

                _no = Action()
                _no.text = "No" 
                actions.append (_no)

                _as = ActionSet (game, game.get_attacking_player(), "Assign %s combat damage as though it wasn't blocked" % (a_lki.get_object()), actions)

                return _as 

            else:
                if action.text == "Yes":
                    self.damage.append ( (a_lki, LastKnownInformation(game, game.get_defending_player()), a_state.power) )
                    self.i += 1
                    self.state = 2
                    game.process_push(self)
                else:
                    self.state = 4
                    game.process_push(self)

        elif self.state == 4:
            a_id, b_ids = self.a_id2b_ids[self.i]
            a_lki = self.id2lki[a_id]
            a_obj = self.id2lki[a_id].get_object()
            a_state = self.id2lki[a_id].get_state()
            
            if len(b_ids) == 1:
                # blocked by one creature deal all damage to that creature
                b_id = b_ids[0]
                b_lki = self.id2lki[b_id]
                self.damage.append ( (a_lki, b_lki, a_state.power) )
            else:
                self.damageToAssign = a_state.power

                self.state = 5
                game.process_push(self)

        elif self.state == 5:
            a_id, b_ids = self.a_id2b_ids[self.i]
            a_lki = id2lki[a_id]
            a_obj = self.id2lki[a_id].get_object()
            a_state = self.id2lki[a_id].get_state()

            if self.damageToAssign > 0:
                if action is None:
                    # attacking player choose how to assign damage
                    actions = []

                    for b_id in b_ids:
                        _p = Action ()
                        _p.object = self.id2lki[b_id].get_object()
                        _p.text = str(_p.object)
                        actions.append (_p)

                    _as = ActionSet (game, game.get_attacking_player(), "Assign 1 damage from %s to what defending creature?" % (a_lki.get_object()), actions)
                    return _as
                else:
                    b_lki = self.id2lki[a.object.id]
                    self.damage.append ( (a_lki, b_lki, 1) )

                    self.damageToAssign -= 1

                    game.process_push(self)
                    
            else:
                self.i += 1
                self.state = 2
                game.process_push(self)

        elif self.state == 6:
            # damage done by blocker creatures           
            if self.i >= len(self.b_id2a_ids):
                self.i = 0
                self.state = 8
                game.process_push(self)
            else:
                b_id, a_ids = self.b_id2a_ids[self.i]
                b_lki = self.id2lki[b_id]
                b_obj = self.id2lki[b_id].get_object()
                b_state = self.id2lki[b_id].get_state()

                if not b_lki.is_moved() and "creature" in b_state.types and ((self.firstStrike and "first strike" in b_lki.get_state().tags) or (not self.firstStrike and "first strike" not in b_lki.get_state().tags) or (self.firstStrike and "double strike" in b_lki.get_state().tags)):

                    if len(a_ids) == 0:
                        # creature not blocking any attacker, do nothing
                        self.i += 1
                        game.process_push(self)

                    elif len(a_ids) == 1:
                        # creature blocking one attacker
                        a_id = a_ids[0]
                        a_lki = id2lki[a_id]
                        damage.append ( (b_lki, a_lki, b_state.power) )

                        self.i += 1
                        game.process_push(self)

                    else:
                        self.damageToAssign = b_state.power
                        self.state = 7
                        game.process_push(self)

        elif self.state == 7:
             b_id, a_ids = self.b_id2a_ids[self.i]
             b_lki = self.id2lki[b_id]
             b_obj = self.id2lki[b_id].get_object()
             b_state = self.id2lki[b_id].get_state()

             if self.damageToAssign > 0:
                if action is None:
                    actions = []

                    for a_id in a_ids:
                        _p = Action ()
                        _p.object = self.id2lki[a_id].get_object()
                        _p.text = str(_p.object)
                        actions.append (_p)

                    _as = ActionSet (game, game.get_defending_player(), "Assign 1 damage from %s to what attacking creature?" % (b_lki.get_object()), actions)
                    return _as
                else:
                    b_lki = self.id2lki[action.object.id]
                    damage.append ( (a_lki, b_lki, 1) )

                    self.damageToAssign -= 1
                    game.process_push(self)

             else:
                self.i += 1
                self.state = 6
                game.process_push(self)

        elif self.state == 8:
            merged = {}
            for a, b, n in self.damage:
                d = merged.get( (a,b), 0)
                merged[ (a,b) ] = d + n

            damage = []
            for (a,b), n in merged.iteritems():
                damage.append ( (a, b, n) )

            damage_object = game.create_damage_assignment(damage, True)
            game.stack_push(damage_object)
            for ability in game.triggered_abilities:
                game.stack_push (ability)
            game.triggered_abilities = []

            game.process_push(PostStepProcess())
            game.process_push(PrioritySuccessionProcess(game.get_active_player()))
  

# DONE?
def process_step_combat_damage (game, firstStrike):
    game.current_step = "combat damage"
    process_step_pre (game)

    # map object ids to object last known information
    id2lki = {}

    # map attacker id to list of blocker ids that block the attacker
    a_id2b_ids = {}

    # map blocker id to list of attacker ids it blocks
    b_id2a_ids = {}

    # Init the maps... for attackers
    for a in game.declared_attackers:
        # declared_attackers is an LastKnownInformation
        _id = a.get_object().id
        id2lki[_id] = a
        a_id2b_ids[_id] = []

    # ...and for blockers...
    for b in game.declared_blockers:
        _id = b.get_object().id
        id2lki[_id] = b

        b_id2a_ids[_id] = []

        # the declared_blockers_map map blocker id to the attacker ids it
        # blocks
        a_ids = game.declared_blockers_map[b.get_object().id]

        for a_id in a_ids:
            a_id2b_ids[a_id].append (_id)
            b_id2a_ids[_id].append (a_id)


    # list of  (source lki,
    #           target lki,
    #           damage (integer))
    damage = []
    for a_id, b_ids in a_id2b_ids.items():
        a_lki = id2lki[a_id]
        a_obj = id2lki[a_id].get_object()
        a_state = id2lki[a_id].get_state()
        
        # only creatures deal combat damage
        if not a_lki.is_moved() and "creature" in a_state.types and ((firstStrike and "first strike" in a_lki.get_state().tags) or (not firstStrike and "first strike" not in a_lki.get_state().tags) or (firstStrike and "double strike" in a_lki.get_state().tags)):

            if len(b_ids) == 0:
                # unblocked creature deal damage to the defending player
                damage.append ( (a_lki, LastKnownInformation(game, game.get_defending_player()), a_state.power) )

            else:

                doDamage = True

                if "x-sneaky" in a_lki.get_state().tags:
                    actions = []
                    _yes = Action()
                    _yes.text = "Yes"
                    actions.append (_yes)

                    _no = Action()
                    _no.text = "No" 
                    actions.append (_no)

                    _as = ActionSet (game, game.get_attacking_player(), "Assign %s combat damage as though it wasn't blocked" % (a_lki.get_object()), actions)
                    a = game.input.send (_as)

                    if a.text == "Yes":
                        damage.append ( (a_lki, LastKnownInformation(game, game.get_defending_player()), a_state.power) )
                        doDamage = False

                if doDamage:
                    if len(b_ids) == 1:
                        # blocked by one creature deal all damage to that creature
                        b_id = b_ids[0]
                        b_lki = id2lki[b_id]
                        damage.append ( (a_lki, b_lki, a_state.power) )
                    else:
                        # damage to assign
                        d = a_state.power

                        while d > 0:
                            # attacking player choose how to assign damage
                            actions = []

                            for b_id in b_ids:
                                _p = Action ()
                                _p.object = id2lki[b_id].get_object()
                                _p.text = str(_p.object)
                                actions.append (_p)

                            _as = ActionSet (game, game.get_attacking_player(), "Assign 1 damage from %s to what defending creature?" % (a_lki.get_object()), actions)
                            a = game.input.send (_as)

                            b_lki = id2lki[a.object.id]
                            damage.append ( (a_lki, b_lki, 1) )

                            d -= 1

    # damage by the blocked creatures
    for b_id, a_ids in b_id2a_ids.items():
        b_lki = id2lki[b_id]
        b_obj = id2lki[b_id].get_object()
        b_state = id2lki[b_id].get_state()

        if not b_lki.is_moved() and "creature" in b_state.types and ((firstStrike and "first strike" in b_lki.get_state().tags) or (not firstStrike and "first strike" not in b_lki.get_state().tags) or (firstStrike and "double strike" in b_lki.get_state().tags)):
            if len(a_ids) == 0:
                # creature not blocking any attacker, do nothing
                pass

            elif len(a_ids) == 1:
                # creature blocking one attacker
                a_id = a_ids[0]
                a_lki = id2lki[a_id]
                damage.append ( (b_lki, a_lki, b_state.power) )

            else:
                d = b_state.power

                while d > 0:
                    # defending player choose how to assign damage
                    actions = []

                    for a_id in a_ids:
                        _p = Action ()
                        _p.object = id2lki[a_id].get_object()
                        _p.text = str(_p.object)
                        actions.append (_p)

                    _as = ActionSet (game, game.get_defending_player(), "Assign 1 damage from %s to what attacking creature?" % (b_lki.get_object()), actions)
                    a = game.input.send (_as)

                    a_lki = id2lki[a.object.id]
                    damage.append ( (b_lki, a_lki, 1) )

                    d -= 1


    merged = {}
    for a, b, n in damage:
        d = merged.get( (a,b), 0)
        merged[ (a,b) ] = d + n

    damage = []
    for (a,b), n in merged.iteritems():
        damage.append ( (a, b, n) )

    damage_object = game.create_damage_assignment(damage, True)
    game.stack_push(damage_object)
    for ability in game.triggered_abilities:
        game.stack_push (ability)
    game.triggered_abilities = []

    process_priority_succession (game, game.get_active_player())

    process_step_post (game)

class EndOfCombatStepProcess(SandwichProcess):
    def __init__(self):
        SandwichProcess.__init__ (self)

    def pre(self, game):
        game.current_step = "end of combat"
        game.process_push(PreStepProcess())

    def main(self, game):
        for ability in game.end_of_combat_triggers:
            game.triggered_abilities.append (ability)
        game.end_of_combat_triggers = []

        for ability in game.triggered_abilities:
            game.stack_push (ability)
        game.triggered_abilities = []

        game.process_push(PostPhaseProcess())
        game.process_push(PrioritySuccessionProcess(game.get_active_player()))

    def post(self, game):
        game.declared_attackers = set()
        game.declared_blockers = set()
        game.declared_blockers_map = {}

# DONE?
def process_step_end_of_combat (game):
    game.current_step = "end of combat"
    process_step_pre (game)

    for ability in game.end_of_combat_triggers:
        game.triggered_abilities.append (ability)
    game.end_of_combat_triggers = []

    for ability in game.triggered_abilities:
        game.stack_push (ability)
    game.triggered_abilities = []

    process_priority_succession (game, game.get_active_player())

    process_step_post (game)

    game.declared_attackers = set()
    game.declared_blockers = set()
    game.declared_blockers_map = {}


class CombatPhaseProcess(Process):

    def __init__ (self):
        self.state = 0

    def next(self, game, action):
        if self.state == 0:
            game.current_phase = "combat"

            # 306.2
            game.attacking_player_id = game.active_player_id
            game.defending_player_id = game.get_next_player(game.get_active_player()).id

            self.state = 1
            game.process_push(self)
            game.process_push(DeclareAttackersStepProcess())
            game.process_push(BeginningOfCombatStepProcess())
            game.process_push(PrePhaseProcess())

        elif self.state == 1:
            # 308.5
            if len(game.declared_attackers) != 0:
                self.state = 2
                game.process_push(self)
                game.process_push(DeclareBlockersStepProcess())

            else:
                self.state = 3
                game.process_push(self)

        elif self.state == 2:

            self.state = 3
            game.process_push(self)

            # any first or double strikers?
            firstStrike = False
            for a in game.declared_attackers:
                if "first strike" in a.get_state().tags or "double strike" in a.get_state().tags:
                    firstStrike = True

            for b in game.declared_blockers:
                if "first strike" in b.get_state().tags or "double strike" in b.get_state().tags:
                    firstStrike = True

            game.process_push(CombatDamageStepProcess(False))

            if firstStrike:
                game.process_push(CombatDamageStepProcess(True))

        elif self.state == 3:
            self.state = 4
            game.process_push(self)
            game.process_push(PostPhaseProcess())
            game.process_push(EndOfCombatStepProcess())

        elif self.state == 4:
            game.defending_player_id = None 
    
# DONE?
def process_phase_combat (game):
    game.current_phase = "combat"

    # 306.2
    game.attacking_player_id = game.active_player_id
    game.defending_player_id = game.get_next_player(game.get_active_player()).id

    process_phase_pre(game)

    process_step_beginning_of_combat (game)
    process_step_declare_attackers (game)

    # 308.5
    if len(game.declared_attackers) != 0:
        process_step_declare_blockers (game)

        # any first or double strikers?
        firstStrike = False
        for a in game.declared_attackers:
            if "first strike" in a.get_state().tags or "double strike" in a.get_state().tags:
                firstStrike = True

        for b in game.declared_blockers:
            if "first strike" in b.get_state().tags or "double strike" in b.get_state().tags:
                firstStrike = True

        if firstStrike:
            process_step_combat_damage (game, True)
        process_step_combat_damage (game, False)

    process_step_end_of_combat (game)

    process_phase_post(game)

    game.defending_player_id = None

class EndOfTurnStepProcess(SandwichProcess):

    def __init__(self):
        SandwichProcess.__init__ (self)

    def pre(self, game):
        game.current_step = "end of turn"
        game.process_push(PreStepProcess())

    def main(self, game):
        # 313.1
        for ability in game.triggered_abilities:
            game.stack_push (ability)

        game.triggered_abilities = []
        game.process_push(PrioritySuccessionProcess(game.get_active_player()))

    def post(self, game):
        game.process_push(PostStepProcess())


class DiscardACardProcess(Process):
    def __init__ (self, player, cause = None):
        self.player_id = player.id
        self.cause_id = None if cause is None else cause.id

    def next(self, game, action):

        player = game.obj(self.player_id)
        cause = None if self.cause_id is None else game.obj(self.cause_id)

        if action is None:

            if len(game.get_hand(player).objects) == 0:
                return

            actions = []
            for card in game.get_hand(player).objects:
                _p = Action ()
                _p.object = card
                _p.text = "Discard " + str(card)
                actions.append (_p)

            _as = ActionSet (game, player, "Discard a card", actions)
            return _as
        else:
            game.doDiscard(player, action.object, cause)

# DONE
def process_discard_a_card(game, player, cause = None):

    if len(game.get_hand(player).objects) == 0:
        return

    actions = []
    for card in game.get_hand(player).objects:
        _p = Action ()
        _p.object = card
        _p.text = "Discard " + str(card)
        actions.append (_p)

    _as = ActionSet (game, player, "Discard a card", actions)
    a = game.input.send (_as)

    game.doDiscard(player, a.object, cause)

def process_reveal_hand_and_discard_a_card(game, player, chooser, cardSelector, context):
    if len(game.get_hand(player).objects) == 0:
        return

    oldrevealed = game.revealed
    game.revealed = game.revealed[:]
     
    actions = []
    for card in game.get_hand(player).objects:

        game.revealed.append(card.get_id())
        
        if cardSelector.contains(game, context, card):
            _p = Action ()
            _p.object = card
            _p.text = "Choose " + str(card)
            actions.append (_p)

    evaluate(game)

    _as = ActionSet (game, chooser, "Choose a card", actions)
    a = game.input.send (_as)

    game.doDiscard(player, a.object, context)

    game.revealed = oldrevealed
    evaluate(game)

def process_reveal_cards(game, player, cards):
    oldrevealed = game.revealed
    game.revealed = game.revealed[:]

    for card in cards:
        game.revealed.append(card.get_id())

    evaluate(game)       

    p = player
    while True:
        _ok = PassAction(p)
        _ok.text = "OK"

        _as = ActionSet(game, p, "Player %s reveals cards" % p.name, [_ok])
        a = game.input.send(_as)

        p = game.get_next_player(p)
        if p.get_id() == player.get_id():
            break

    game.revealed = oldrevealed 

def process_look_at_cards(game, player, cards):
    oldlooked_at = game.looked_at
    game.looked_at = game.looked_at.copy()

    for card in cards:
        game.looked_at[player.id].append (card.get_id())

    evaluate(game)

    _ok = PassAction(player)
    _ok.text = "OK"

    _as = ActionSet(game, player, "Look at cards", [_ok])
    a = game.input.send(_as)

    game.looked_at = oldlooked_at

class CleanupStepProcess(Process):

    def __init__(self):
        self.state = 0
        self.repeat = True

    def next(self, game, action):
        if self.state == 0:
            self.state = 1
            game.process_push(self)
            game.process_push(PreStepProcess())
        elif self.state == 1:
            game.process_push(self)
            if game.get_active_player().maximum_hand_size != None and "no maximum hand size" not in game.get_active_player().get_state().tags and  len(game.get_hand(game.get_active_player()).objects) > game.get_active_player().maximum_hand_size:
                game.process_push(DiscardACardProcess(game.get_active_player()))
            else:
                self.state = 2
        elif self.state == 2:
            game.process_push(self)
            self.state = 3

            game.get_active_player().land_played = 0

            if len(game.triggered_abilities) > 0:
                game.process_push(PrioritySuccessionProcess(game.get_active_player()))
            else:
                self.repeat = False
        elif self.state == 3:
            game.process_push(self)
            game.process_push(PostStepProcess())

            if self.repeat:
                self.state = 0
            else:
                self.state = 4
        elif self.state == 4:
            selector = AllSelector ()
            for permanent in selector.all (game, None):
                permanent.damage = 0
                permanent.regenerated = False
                permanent.preventNextDamage = 0

            game.until_end_of_turn_effects = []


class EndPhaseProcess(Process):
    def next(self, game, action):
        game.current_phase = "end"
        game.process_push(PostPhaseProcess())
        game.process_push(CleanupStepProcess())
        game.process_push(EndOfTurnStepProcess())
        game.process_push(PrePhaseProcess())


class TurnProcess(Process):

    def __init__ (self, player):
        self.player_id = player.id
        self.state = 0
        self.additional_combat_phase_followed_by_an_additional_main_phase = False

    def next(self, game, action):
        if self.state == 0:
            # pre beginning phase
            game.active_player_id = self.player_id
            game.creature_that_attacked_this_turn_lkis = set()
            self.state = 1

            game.process_push(self)
            game.process_push(MainPhaseProcess("precombat main"))
            game.process_push(BeginningPhaseProcess())
        elif self.state == 1:
            # combat phase and additional combat and main phases
            self.additional_combat_phase_followed_by_an_additional_main_phase = game.additional_combat_phase_followed_by_an_additional_main_phase
            game.additional_combat_phase_followed_by_an_additional_main_phase = False

            self.state = 2
            game.process_push(self)
            game.process_push(MainPhaseProcess("postcombat main"))

            active_player = game.objects[game.active_player_id]
            if active_player.skip_next_combat_phase:
                active_player.skip_next_combat_phase = False
            else:
                game.process_push(CombatPhaseProcess())
        elif self.state == 2:
            game.process_push(self)
            # additional combat phase followed by an additional main phase?
            if not (self.additional_combat_phase_followed_by_an_additional_main_phase or game.additional_combat_phase_followed_by_an_additional_main_phase):
                self.state = 3
            else:
                self.state = 1
                game.additional_combat_phase_followed_by_an_additional_main_phase = False
        elif self.state == 3:
            game.process_push(EndPhaseProcess())

class DrawCardProcess(Process):
    def __init__ (self, player):
        self.player_id = player.id

    def next(self, game, action):
        game.doDrawCard(game.obj(self.player_id))

class GameTurnProcess(Process):

    def __init__ (self):
        self.player_index = 0

    def next(self, game, action):
        if not game.end:
            if self.player_index >= len(game.players):
                self.player_index = 0
                game.turn_number += 1

            player = game.players[self.player_index]
            self.player_index += 1
           
            game.process_push(self)
            game.process_push(TurnProcess(player))


class StartGameProcess(Process):
    def next(self, game, action):
        for player in game.players.__reversed__():
            game.process_push(DrawCardProcess(player))
            game.process_push(DrawCardProcess(player))
            game.process_push(DrawCardProcess(player))
            game.process_push(DrawCardProcess(player))
            game.process_push(DrawCardProcess(player))
            game.process_push(DrawCardProcess(player))
            game.process_push(DrawCardProcess(player))


class MainGameProcess(Process):
    def next(self, game, action):
        game.process_push(GameTurnProcess())
        game.process_push(StartGameProcess())


class TriggerEffectProcess(SandwichProcess):

    def __init__ (self, source, effect, slots):
        SandwichProcess.__init__ (self)

        self.source_id = source.id
        self.effect = effect
        self.slots = slots

    def pre(self, game):
        source = game.obj(self.source_id)
        e = game.create_effect_object (LastKnownInformation(game, source), source.controller_id, self.effect, self.slots)
        self.effect_object_id = e.id

        game.triggered_abilities.append (e)
        evaluate(game)

        print "XXX: TriggerEffectProcess: " + `e.rules.selectTargets`

        e.rules.selectTargets(game, game.objects[e.get_state().controller_id], e)

    def main(self, game):
        if not game.process_returns_pop():
            e = game.obj(self.effect_object_id)
            game.delete(e)
            game.triggered_abilities.remove(e)
        
def process_select_selector(game, player, source, selector, text, optional=False):
    actions = []
    _pass = PassAction(player)
    _pass.text = "Cancel"

    for obj in selector.all(game, source):
        _p = Action()
        _p.object = obj
        _p.text = str(obj)
        actions.append(_p)

    if len(actions) == 0 or optional:
        actions = [_pass] + actions

    _as = ActionSet(game, player, text, actions)
    a = game.input.send(_as)

    if a == _pass:
        return None

    return a.object

def process_select_source_of_damage(game, player, SELF, selector, text, optional=False):
    actions = []
    _pass = PassAction(player)
    _pass.text = "Cancel"

    sources = set([obj for obj in selector.all(game, SELF)])
    valid_sources = set()

    # permanents, spells on stack, card or permanent referred by an objecton stack,  creature assigning combat damage
    for permanent in AllPermanentSelector().all(game, SELF):
        if permanent in sources:
            valid_sources.add(permanent)

    for obj in game.get_stack_zone().objects:
        if "spell" in obj.get_state().tags and obj in sources and not isinstance(obj, EffectObject):
            valid_sources.add(obj)

        if isinstance(obj, EffectObject):
            source = obj.get_source_lki().get_object()
            if (not isinstance(source, EffectObject)) and source in sources:
                valid_sources.add(obj)

        elif isinstance(obj, DamageAssignment):
            for a, b, n in obj.damage_assignment_list:
                if a.get_object() in sources:
                    valid_sources.add(a.get_object())
        
        for target in obj.targets.values():
            if target.get_object() in sources and not isinstance(target.get_object(), EffectObject):
                valid_sources.add(target.get_object())

    for obj in valid_sources:
        _p = Action()
        _p.object = obj
        _p.text = str(obj)
        actions.append(_p)

    if len(actions) == 0 or optional:
        actions = [_pass] + actions

    _as = ActionSet(game, player, text, actions)
    a = game.input.send(_as)

    if a == _pass:
        return None

    return a.object
   

def _is_valid_target(game, source, target):
    # TODO: protections and stuff 

    if "shroud" in target.get_state().tags:
        return False

    return True

def is_valid_target(game, source, target):
    return _is_valid_target(game, source, target)

class SelectTargetProcess(Process):
    def __init__ (self, player, source, selector, optional=False):
        self.player_id = player.id
        self.source_id = source.id
        self.selector = selector
        self.optional = optional
        self.state = 0

    def next(self, game, action):
        if self.state == 0:

            player = game.obj(self.player_id)
            source = game.obj(self.source_id)

            self.state = 1

            actions = []

            _pass = PassAction (player)
            _pass.text = "Cancel"

            for obj in self.selector.all(game, source):
                if _is_valid_target(game, source, obj):
                    _p = Action ()
                    _p.object = obj
                    _p.text = "Target " + str(obj)
                    actions.append (_p)

            if len(actions) == 0 or self.optional:
                actions = [_pass] + actions

            _as = ActionSet (game, player, "Choose a target for " + str(source), actions)
            return _as

        elif self.state == 1:
            if isinstance(action, PassAction):
                game.process_returns_push(None)
            else:
                game.process_returns_push(action.object)


def process_select_targets(game, player, source, selector, n, optional=False):

    _pass = PassAction (player)
    _pass.text = "Cancel"

    _enough = PassAction(player)
    _enough.text = "Enough targets"
    # actions.append (_pass)

    targets = []

    for i in range(n):
        actions = []

        for obj in selector.all(game, source):
            if obj not in targets and _is_valid_target(game, source, obj):
                _p = Action ()
                _p.object = obj
                _p.text = "Target " + str(obj)
                actions.append (_p)

        if len(actions) == 0 and not optional:
            actions = [_pass] + actions

        if optional:
            actions = [_enough] + actions

        numberals = ["first", "second", "third", "fourth", "fifth", "sixth", "sevetnh", "eighth", "ninth"]
        if i <= 8:
            query = ("Choose the %s target for " % (numberals[i]))  + str(source)
        else:
            query = ("Choose the %dth target for " % i) + str(source)

        _as = ActionSet (game, player, query, actions)
        a = game.input.send (_as)

        if a == _pass:
            return None

        if a == _enough:
            break

        targets.append (a.object)

    return targets

# Special effect which causes something to be put into play under a player's control
def process_put_card_into_play(game, card, controller, cause, tapped=False):

    in_play_zone = game.get_in_play_zone()

    if "aura" in card.get_state().subtypes:
        if card.rules.selectTargets(game, controller, card):
            assert card.targets["target"] is not None

            card.enchanted_id = card.targets["target"].get_id()
            card.controller_id = controller.get_id()
            card.tapped = tapped
            game.doZoneTransfer(card, in_play_zone, cause)

        else:
            return False

    else:
        # else, just add it into play
        card.controller_id = controller.get_id()
        card.tapped = tapped
        game.doZoneTransfer(card, in_play_zone, cause)

    return True

class ValidateTargetProcess(Process):
    def __init__ (self, source, selector, target):
        assert isinstance(target, LastKnownInformation)
        self.source_id = source.id
        self.selector = selector
        self.target = target

    def next(self, game, action):

        source = game.obj(self.source_id)

        if self.target.is_moved():
            game.process_returns_push(False)
            return

        if not self.selector.contains(game, source, self.target):
            game.process_returns_push(False)
            return

        game.process_returns_push( _is_valid_target(game, source, self.target) )

# DONE?
def process_validate_target(game, source, selector, target):
    assert isinstance(target, LastKnownInformation)
    if target.is_moved():
        return False

    if not selector.contains(game, source, target):
        return False

    return _is_valid_target(game, source, target)

def process_ask_x(game, obj, player):
    _as = QueryNumber(game, player, "Choose X")
    a = game.input.send(_as)

    obj.x = a

    # convert number to mana string
    ret = ""
    while a > 9:
        ret += "9"
        a -= 9
    ret += str(a)

    return ret

def process_ask_option(game, obj, player, question, options):
    opts = []

    for o in options:
       p = Action ()
       p.text = o
       opts.append (p)

    _as = ActionSet (game, player, question, opts)
    a = game.input.send (_as)
    return a.text

