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

from selectors import *
from rules import *
from actions import *
from cost import *
from objects import *

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

def process_play_spell (game, ability, player, obj):
    zone_from = game.objects[obj.zone_id]
    zone_index = zone_from.objects.index(obj)

    # move to stack
    stack = game.get_stack_zone()
    obj.zone_id = stack.id
    zone_from.objects.remove(obj)
    stack.objects.append (obj)

    evaluate(game)

    if not obj.rules.selectTargets(game, player, obj):
        obj.zone_id = zone_from.id
        stack.objects.remove(obj)
        zone_from.objects.insert(zone_index, obj)
        return

    costs = ability.determineCost(game, obj, player)
    costs = costs[:]

    costs = game.replacePlayCost(ability, obj, player, costs)

    # cost = ability.get_cost(game, player, obj)
    if len(costs) > 0:
        if not process_pay_cost(game, player, obj, obj, costs):

            print("not payed, returning to previous state")

            # return the state of the game...
            obj.zone_id = zone_from.id
            stack.objects.remove(obj)
            zone_from.objects.insert(zone_index, obj)
            return

    game.onPlay(obj)

def process_activate_tapping_ability(game, ability, player, obj, effect):

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

    game.doTap(obj)
    game.onPlay(obj)

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


def process_priority_succession (game, player):

    game.current_player_priority = player
    first_passed = None
    while True:

        for ability in game.triggered_abilities:
            game.stack_push (ability)
        game.triggered_abilities = []

        evaluate(game)
        actions = []
        _pass = PassAction (game.current_player_priority)
        actions.append (_pass)

        actions.extend(get_possible_actions (game, game.current_player_priority))

        _as = ActionSet (game, game.current_player_priority, "You have priority", actions)
        a = game.input.send (_as)

        if a != _pass:
            first_passed = None
            do_action (game, game.current_player_priority, a)
        else:
            np = game.get_next_player (game.current_player_priority)
            if first_passed == np:
                if game.get_stack_length () == 0:
                    break
                else:
                    resolve (game, game.stack_top ())
                    first_passed = None
                    game.current_player_priority = player
            else:
                if first_passed == None:
                    first_passed = game.current_player_priority

                game.current_player_priority = np


def process_untap (game, permanent):
    game.doUntap(permanent)

def process_draw_card (game, player):
    game.doDrawCard(player)

def process_phase_pre (game):
    game.current_step = ""
    evaluate(game)

def process_phase_post (game):
    # 300.3
    for player in game.players:
        converted_mana = mana_converted_cost(player.manapool)
        if converted_mana > 0:
            howmuch = converted_mana
            print("manaburn %d" % (howmuch))
            player.manapool = ""
            game.doLoseLife(player, howmuch)

    evaluate(game)

def process_step_pre (game):
    evaluate(game)
    game.raise_event("step")

def process_step_post (game):
    evaluate(game)

def process_step_untap (game):
    game.current_step = "untap"
    process_step_pre (game)

    selector = PermanentPlayerControlsSelector (game.get_active_player())
    for permanent in selector.all (game, None):
        if "does not untap" not in permanent.state.tags:
            process_untap (game, permanent)

    process_step_post (game)


def process_step_upkeep (game):
    """ 303.1 """

    game.current_step = "upkeep"
    process_step_pre (game)

    for ability in game.triggered_abilities:
        game.stack_push (ability)
    game.triggered_abilities = []

    process_priority_succession (game, game.get_active_player())

    process_step_post (game)

def process_step_draw (game):
    """ 304.1 """
    game.current_step = "draw"
    process_step_pre (game)

    for i in range(game.get_active_player().draw_cards_count):
        process_draw_card (game, game.get_active_player())

    for ability in game.triggered_abilities:
        game.stack_push (ability)
    game.triggered_abilities = []

    process_priority_succession (game, game.get_active_player())

    process_step_post (game)

def process_phase_beginning (game):
    game.current_phase = "beginning"
    process_phase_pre(game)

    # remove the summoning sickness tag
    selector = PermanentPlayerControlsSelector (game.get_active_player())
    for permanent in selector.all (game, None):
        if "summoning sickness" in permanent.initial_state.tags:
            permanent.initial_state.tags.remove("summoning sickness")

    process_step_untap (game)
    process_step_upkeep (game)

    # 101.6a
    if not (game.turn_number == 0 and game.get_active_player() == game.players[0]):
        process_step_draw (game)

    process_phase_post(game)

def process_phase_main (game, which):
    game.current_phase = which
    process_phase_pre(game)

    for ability in game.triggered_abilities:
        game.stack_push (ability)
    game.triggered_abilities = []

    process_priority_succession (game, game.get_active_player())
    process_phase_post(game)

def process_step_beginning_of_combat (game):
    game.current_step = "beginning of combat"
    process_step_pre (game)
    for ability in game.triggered_abilities:
        game.stack_push (ability)
    game.triggered_abilities = []

    process_priority_succession (game, game.get_active_player())

    process_step_post (game)


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
                if "creature" in permanent.state.types and not permanent.tapped and ("haste" in permanent.state.tags or not "summoning sickness" in permanent.state.tags) and permanent not in attackers and "can't attack" not in permanent.state.tags and "can't attack or block" not in permanent.state.tags and "defender" not in permanent.state.tags:
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
        game.declared_attackers.add (LastKnownInformation(game, a))

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


def validate_attack(game, attackers):

    for attacker in attackers:
        if "can't attack unless a creature with greater power also attacks" in attacker.get_state().tags:
            isSuch = False
            for other_attacker in attackers:
                if attacker != other_attacker:
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

    # lure
    # warning, this can turn into a recursive hell, if not taken care
    if "lure" not in attacker.get_state().tags:
        for a2 in game.declared_attackers:
            if "lure" in a2.get_state().tags:
                if is_valid_block(game, a2, blocker):
                    print("%s cannot block %s because there is a valid lure %s" % (blocker, attacker, a2))
                    return False

    return True

def validate_block(game, blockers, blockers_map):
    # evasion abilities
    for blocker_id, attackers in blockers_map.items():
        blocker = game.objects[blocker_id]

        # we normally allow only one attacker per blocker
        if len(attackers) > 1 and "can block any number of creatures" not in blocker.state.tags:
            return False

        for attacker in attackers:
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

    # check for lures and that all creature able to block are blocking them are blocking something
    for attacker in game.declared_attackers:
        if "lure" in attacker.get_state().tags:
            selector = PermanentPlayerControlsSelector(game.get_defending_player())
            for permanent in selector.all(game, None):
                if "creature" in permanent.state.types and not permanent.tapped and (permanent not in blockers or "can block any number of creatures" in permanent.state.tags):
                    if is_valid_block(game, attacker, permanent):
                        print("Invalid block, %s not blocking a lure" % permanent)
                        return False

    return True

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
                if "creature" in permanent.state.types and not permanent.tapped and (permanent not in blockers or "can block any number of creatures" in permanent.state.tags):
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

                    _as = ActionSet (game, game.get_blocking_player(), "Assign 1 damage from %s to what attacking creature?" % (b_lki.get_object()), actions)
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


def process_step_end_of_turn(game):
    game.current_step = "end of turn"
    process_step_pre (game)
    # 313.1
    for ability in game.triggered_abilities:
        game.stack_push (ability)
    game.triggered_abilities = []

    process_priority_succession (game, game.get_active_player())

    process_step_post (game)

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

def process_step_cleanup(game):

    repeat = True
    while repeat:
        process_step_pre (game)
        # 314.1
        if game.get_active_player().maximum_hand_size != None:
            while len(game.get_hand(game.get_active_player()).objects) > game.get_active_player().maximum_hand_size:
                #actions = []
                #for card in game.get_hand(game.get_active_player()).objects:
                #    _p = Action ()
                #    _p.object = card
                #    _p.text = "Discard " + card.state.title
                #    actions.append (_p)

                #_as = ActionSet (game, game.get_active_player(), "Discard a card", actions)
                #a = game.input.send (_as)

                #game.doDiscard(game.get_active_player(), a.object)
                process_discard_a_card(game, game.get_active_player())


        game.get_active_player().land_played = 0

        if len(game.triggered_abilities) > 0:
            process_priority_succession (game, game.get_active_player())
        else:
            repeat = False

        process_step_post(game)


    selector = AllSelector ()
    for permanent in selector.all (game, None):
        permanent.damage = 0
        permanent.regenerated = False
        permanent.preventNextDamage = 0

    game.until_end_of_turn_effects = []

def process_phase_end (game):
    game.current_phase = "end"
    process_phase_pre(game)

    # 312.1.
    process_step_end_of_turn(game)
    process_step_cleanup(game)

    process_phase_post(game)



def process_turn (game, player):
    game.active_player_id = player.id

    process_phase_beginning (game)
    process_phase_main (game, "precombat main")

    active_player = game.objects[game.active_player_id]
    if active_player.skip_next_combat_phase:
        active_player.skip_next_combat_phase = False
    else:
        process_phase_combat (game)

    process_phase_main (game, "postcombat main")
    process_phase_end (game)


def process_game (game):

    for player in game.players:
        for i in range(7):
            game.doDrawCard(player)

    while True:
        for player in game.players:
            try:
                process_turn (game, player)
            except StopIteration:
                return
            except GameEndException, x:
                game.output.gameEnds(x.player)
                return

        game.turn_number += 1

def process_trigger_effect(game, source, effect, slots):
    e = game.create_effect_object (LastKnownInformation(game, source), source.controller_id, effect, slots)

    game.triggered_abilities.append (e)

    evaluate(game)

    if not e.rules.selectTargets(game, game.objects[e.get_state().controller_id], e):
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

def process_select_target(game, player, source, selector, optional=False):
    actions = []

    _pass = PassAction (player)
    _pass.text = "Cancel"
    # actions.append (_pass)

    for obj in selector.all(game, source):
        if _is_valid_target(game, source, obj):
            _p = Action ()
            _p.object = obj
            _p.text = "Target " + str(obj)
            actions.append (_p)

    if len(actions) == 0 or optional:
        actions = [_pass] + actions

    _as = ActionSet (game, player, "Choose a target for " + str(source), actions)
    a = game.input.send (_as)

    if a == _pass:
        return None

    return a.object

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

