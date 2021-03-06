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

from cost import ManaCost, mana_diff
from objects import  *
from selectors import *
from actions import *
from functools import partial
from process import Process, SandwichProcess, SelectTargetProcess, PayCostProcess, TriggerEffectProcess

class Effect:
    def setText(self):
        self.text = text

    def getText(self):
        return self.text

    def getSlots(self):
        return []


class ContinuousEffect(Effect):
    def apply (self, game, obj):
        pass

    # does this effect handles self, or other? (if self, it is active all the time, not only when the object is in play)
    def isSelf(self):
        return False

    def getLayer(self):
        # "copy", "control", "text", "type", "other", "power_set", "power_switch", "power_modify", "power_other"
        return "other"

class OneShotEffect(Effect):
    def resolve(self, game, obj):
        game.process_returns_push(True)

    def selectTargets(self, game, player, obj):
        game.process_returns_push(True)

    def validateTargets(self, game, obj):
        game.process_returns_push(True)

class DamagePrevention(Effect):
    def canApply(self, game, damage, combat):
        return False

    def apply(self, game, damage, combat):
        return damage

    def getEffect(self):
        return None

    def setEffect(self, effect):
        pass    

class PlayerLooseLifeEffect(OneShotEffect):
    def __init__ (self, playerSelector, count):
        self.selector = playerSelector
        self.count = count

    def resolve(self, game, obj):
        if self.count == "X":
            count = obj.x
        else:
            count = self.count

        for player in self.selector.all(game, obj):
            game.doLoseLife(player, count)

        game.process_returns_push(True)

    def __str__ (self):
        return "PlayerLooseLifeEffect(%s, %s)" % (str(self.selector), str(self.count))

class PlayerGainLifeEffect(OneShotEffect):
    def __init__ (self, playerSelector, count):
        self.selector = playerSelector
        self.count = count

    def resolve(self, game, obj):

        n = self.count.evaluate(game, obj)

        for player in self.selector.all(game, obj):
            game.doGainLife(player, n)

        game.process_returns_push(True)

    def __str__ (self):
        return "PlayerGainLifeEffect(%s, %s)" % (self.selector, str(self.count))



class PlayerMayGainLifeEffectProcess(Process):
    def __init__ (self, player_id, n):
        self.player_id = player_id
        self.n = n

    def next(self, game, action):
        player = game.obj(self.player_id)

        if game.process_returns_pop():
            game.doGainLife(player, self.n)

class PlayerMayGainLifeEffect(OneShotEffect):
    def __init__ (self, playerSelector, count):
        self.selector = playerSelector
        self.count = count

    def resolve(self, game, obj):
        from process import AskOptionalProcess
        n = self.count.evaluate(game, obj)

        game.process_returns_push(True)

        for player in self.selector.all(game, obj):
            game.process_push(PlayerMayGainLifeEffectProcess(player.get_id(), n))
            game.process_push(AskOptionalProcess(obj, player, "Gain %d life?" % n, "Yes", "No"))

    def __str__ (self):
        return "PlayerMayGainLifeEffect(%s, %s)" % (self.selector, str(self.count))

class PlayerGainLifeForEachXEffect(OneShotEffect):
    def __init__ (self, playerSelector, count, eachSelector):
        self.selector = playerSelector
        self.count = count
        self.eachSelector = eachSelector

    def resolve(self, game, obj):

        n = self.count.evaluate(game, obj)

        for player in self.selector.all(game, obj):
            eachcount = len([x for x in self.eachSelector.all(game, obj)])
            game.doGainLife(player, n * eachcount)

        game.process_returns_push(True)

    def __str__ (self):
        return "PlayerGainLifeForEachXEffect(%s, %s, %s)" % (self.selector, self.count, self.eachSelector)

class PlayerDiscardsCardEffect(OneShotEffect):
    def __init__ (self, playerSelector, count):
        self.selector = playerSelector
        self.count = count

    def resolve(self, game, obj):

        game.process_returns_push(True)

        n = self.count.evaluate(game, obj)
        for player in self.selector.all(game, obj):
            assert player is not None
            for i in range(n):
                from process import DiscardACardProcess
                game.process_push(DiscardACardProcess(player.get_object(), obj))

    def __str__ (self):
        return "PlayerDiscardsCardEffect(%s, %s)" % (self.selector, self.count)

class XDealNDamageToY(OneShotEffect):
    def __init__ (self, x_selector, y_selector, n):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.count = n

    def resolve(self, game, obj):
        game.process_returns_push(True)

        sources = [x for x in self.x_selector.all(game, obj)]
        assert len(sources) == 1

        source = sources[0]

        count = self.count.evaluate(game, obj)

        damage = []
        for y in self.y_selector.all(game, obj):
            if not y.is_moved():
                damage.append ( (game.create_lki(source), game.create_lki(y), count) )

        game.doDealDamage(damage)

    def __str__ (self):
        return "XDealNDamageToY(%s, %s, %s)" % (self.x_selector, self.y_selector, self.count)

class SingleTargetOneShotEffectSelectTargetsProcess(SandwichProcess):
    def __init__ (self, effect, player, obj):
        SandwichProcess.__init__(self)

        self.effect = effect
        self.player_id = player.id
        self.obj_id = obj.id
        self.state = 0

    def pre(self, game):
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        game.process_push(SelectTargetProcess(player, obj, self.effect.targetSelector, self.effect.optional))

    def main(self, game):
        target_id = game.process_returns_pop()
        if target_id == None:
            game.process_returns_push(False)
            # TODO: return game state
            return

        target = game.obj(target_id)

        obj = game.obj(self.obj_id)
        obj.targets["target"] = game.create_lki(target)
        game.raise_event ("target", obj, target)

    def post(self, game):
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        self.effect.doModal(game, player, obj)

class SingleTargetOneShotEffectResolveProcess(SandwichProcess):
    def __init__ (self, effect, obj):
        SandwichProcess.__init__ (self)
        self.effect = effect
        self.obj_id = obj.id

    def pre(self, game):
        self.effect.validateTargets(game, game.obj(self.obj_id))

    def main(self, game):
        if game.process_returns_pop():
            obj = game.obj(self.obj_id)
            target = obj.targets["target"]
            self.effect.doResolve(game, obj, game.lki(target))
        else:
            game.process_returns_push(False)

class SingleTargetOneShotEffect(OneShotEffect):

    def __init__ (self, targetSelector, optional = False):
        self.targetSelector = targetSelector    
        self.optional = optional

    def resolve(self, game, obj):
        game.process_push(SingleTargetOneShotEffectResolveProcess(self, obj))

    def validateTargets(self, game, obj):
        from process import ValidateTargetProcess
        game.process_push(ValidateTargetProcess(obj, self.targetSelector, obj.targets["target"]))

    def selectTargets(self, game, player, obj):
        game.process_push(SingleTargetOneShotEffectSelectTargetsProcess(self, player, obj))
    
    def doModal(self, game, player, obj):
        game.process_returns_push(True)

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)

    def __str__ (self):
        return "SingleTargetOneShotEffect(%s)" % self.targetSelector

class MutlipleTargetsOneShotEffectResolveProcess(SandwichProcess):
    def __init__ (self, effect, obj):
        SandwichProcess.__init__ (self)
        self.effect = effect
        self.obj_id = obj.id

    def pre(self, game):
        self.effect.validateTargets(game, game.obj(self.obj_id))

    def main(self, game):
        if game.process_returns_pop():
            obj = game.obj(self.obj_id)
            targets = obj.targets
            self.effect.doResolve(game, obj, targets)
        else:
            game.process_returns_push(False)

class MutlipleTargetsOneShotEffectValidateTargetsProcess(SandwichProcess):
    def __init__ (self, effect, obj):
        SandwichProcess.__init__ (self)
        self.effect = effect
        self.obj_id = obj.id

    def pre(self, game):
        from process import ValidateTargetProcess
        obj = game.obj(self.obj_id)
        for target in obj.targets.values():
            game.process_push(ValidateTargetProcess(obj, self.effect.targetSelector, target))

    def main(self, game):
        obj = game.obj(self.obj_id)

        valid = True

        # we only care about the number of targets, returns are in the opposite order
        for target in obj.targets.values():
            if not game.process_returns_pop():
                valid = False

        game.process_returns_push(valid)

class MultipleTargetOneShotEffectSelectTargetsProcess(SandwichProcess):
    def __init__ (self, effect, player, obj):
        SandwichProcess.__init__ (self)
        self.effect = effect
        self.player_id = player.id
        self.obj_id = obj.id

    def pre(self, game):
        from process import SelectTargetsProcess
        obj = game.obj(self.obj_id)
        player = game.obj(self.player_id)

        self.n = self.effect.number.evaluate(game, obj)

        game.process_push(SelectTargetsProcess(player, obj, self.effect.targetSelector, self.n, self.effect.optional))

    def main(self, game):
        obj = game.obj(self.obj_id)
        player = game.obj(self.player_id)
        targets = game.process_returns_pop()

        self.cancelled = False

        if targets is None or len(targets) == 0:
            self.cancelled = True
            game.process_returns_push(False)
        elif not self.effect.optional and len(targets) != self.n:
            self.cancelled = True
            game.process_returns_push(False)
        else:
            for i in range(len(targets)):
                obj.targets[i] = game.create_lki(game.obj(targets[i]))
                game.raise_event ("target", obj, targets[i])

    def post(self, game):
        obj = game.obj(self.obj_id)
        player = game.obj(self.player_id)

        if not self.cancelled:
            self.effect.doModal(game, player, obj)

class MultipleTargetOneShotEffect(OneShotEffect):

    def __init__ (self, targetSelector, number, optional = False):
        self.targetSelector = targetSelector    
        self.optional = optional
        self.number = number

    def resolve(self, game, obj):
        game.process_push(MutlipleTargetsOneShotEffectResolveProcess(self, obj))

    def validateTargets(self, game, obj):
        game.process_push(MutlipleTargetsOneShotEffectValidateTargetsProcess(self, obj))

    def selectTargets(self, game, player, obj):
        game.process_push(MultipleTargetOneShotEffectSelectTargetsProcess(self, player, obj))
    
    def doModal(self, game, player, obj):
        game.process_returns_push(True)

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)

    def __str__ (self):
        return "MultipleTargetOneShotEffect(%s, %s)" % (self.targetSelector, self.number)

class XDealNDamageToTargetYEffect(SingleTargetOneShotEffect):
    def __init__ (self, sourceSelector, number, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.sourceSelector = sourceSelector
        self.number = number
           
    def doResolve(self, game, obj, target): 
        game.process_returns_push(True)

        sources = [x for x in self.sourceSelector.all(game, obj)]
        assert len(sources) == 1

        source = sources[0]

        count = self.number.evaluate(game, obj)

        game.doDealDamage([(game.create_lki(source), target.get_lki_id(), count)])


    def __str__ (self):
        return "XDealNDamageToTargetYEffect(%s, %s, %s)" % (self.sourceSelector, self.number, self.targetSelector)

class XDealNDamageToTargetYAndMDamageToZEffect(SingleTargetOneShotEffect):
    def __init__ (self, sourceSelector, number, targetSelector, number2, otherSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.sourceSelector = sourceSelector
        self.number = number
        self.number2 = number2
        self.otherSelector = otherSelector
           
    def doResolve(self, game, obj, target): 
        game.process_returns_push(True)

        sources = [x for x in self.sourceSelector.all(game, obj)]
        assert len(sources) == 1

        source = sources[0]

        count = self.number.evaluate(game, obj)
        count2 = self.number2.evaluate(game, obj)

        dlist = []
        dlist.append ( (game.create_lki(source), game.create_lki(target), count) )

        for obj in self.otherSelector.all(game, obj):
            dlist.append ( (game.create_lki(source), game.create_lki(obj), count2) )
        game.doDealDamage(dlist)

    def __str__ (self):
        return "XDealNDamageToTargetYAndMDamageToZEffect(%s, %s, %s, %s, %s)" % (self.targetSelector, self.number, self.sourceSelector, self.number2, self.otherSelector)

class XGetsNN(ContinuousEffect):
    def __init__ (self, selector, power, toughness):
        self.selector = selector
        self.power = power
        self.toughness = toughness

    def apply(self, game, obj):
        power = self.power
        toughness = self.toughness
        if power == "+X":
            power = obj.x
        elif power == "-X":
            power = - obj.x
        if toughness == "+X":
            toughness = obj.x
        elif toughness == "-X":
            toughness = - obj.x

        for o in self.selector.all(game, obj):
            if not o.is_moved():
                o.get_state().power += power
                o.get_state().toughness += toughness

    def getLayer(self):
        return "power_modify"

    def __str__ (self):
        return "XGetsNN(%s, %s, %s)" % (self.selector, self.power, self.toughness)

class XGetsNNForEachY(ContinuousEffect):
    def __init__ (self, x_selector, power, toughness, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.power = power
        self.toughness = toughness

    def apply(self, game, obj):
        power = self.power
        toughness = self.toughness
        if power == "+X":
            power = obj.x
        elif power == "-X":
            power = - obj.x
        if toughness == "+X":
            toughness = obj.x
        elif toughness == "-X":
            toughness = - obj.x

        mult = len([x for x in self.y_selector.all(game, obj)])

        for o in self.x_selector.all(game, obj):
            if not o.is_moved():
                o.get_state().power += power * mult
                o.get_state().toughness += toughness * mult

    def getLayer(self):
        return "power_modify"

    def __str__ (self):
        return "XGetsNNForEachY(%s, %s, %s, %s)" % (self.x_selector, self.power, self.toughness, self.y_selector)

class XGetsNNForEachOtherCreatureInPlayThatSharesAtLeastOneCreatureTypeWithIt(ContinuousEffect):
    def __init__ (self, x_selector, power, toughness):
        self.x_selector = x_selector
        self.power = power
        self.toughness = toughness

    def apply(self, game, obj):
        power = self.power
        toughness = self.toughness
        if power == "+X":
            power = obj.x
        elif power == "-X":
            power = - obj.x
        if toughness == "+X":
            toughness = obj.x
        elif toughness == "-X":
            toughness = - obj.x

        creature_selector = CreatureSelector()

        for o in self.x_selector.all(game, obj):
            if not o.is_moved():

                mult = 0
                for creature in creature_selector.all(game, obj):
                    if creature.get_id() != o.get_id():
                        for otype in o.get_state().subtypes:
                            if otype in creature.get_state().subtypes:
                                mult += 1
                                break

                o.get_state().power += power * mult
                o.get_state().toughness += toughness * mult

    def getLayer(self):
        return "power_modify"

    def __str__ (self):
        return "XGetsNNForEachOtherCreatureInPlayThatSharesAtLeastOneCreatureTypeWithIt(%s, %s, %s)" % (self.x_selector, self.power, self.toughness)


class XGetsTag(ContinuousEffect):
    def __init__ (self, selector, tag):
        self.selector = selector
        self.tag = tag

    def apply(self, game, obj):
        for o in self.selector.all(game, obj):
            if not o.is_moved():
                o.get_state().tags.add (self.tag)

    def isSelf(self):
        return isinstance(self.selector, SelfSelector)

    def __str__ (self):
        return "XGetsTag(%s, %s)" % (self.selector, self.tag)

    def getLayer(self):
        return "other"

class IfCXGetsTag(ContinuousEffect):
    def __init__ (self, condition, selector, tag):
        self.condition = condition
        self.selector = selector
        self.tag = tag

    def apply(self, game, obj):
        if self.condition.evaluate(game, obj):
            for o in self.selector.all(game, obj):
                if not o.is_moved():
                    o.get_state().tags.add (self.tag)

    def isSelf(self):
        return isinstance(self.selector, SelfSelector)

    def __str__ (self):
        return "IfCXGetsTag(%s, %s, %s)" % (self.condition, self.selector, self.tag)

    def getLayer(self):
        return "other"

class IfXWouldDealDamageToYPreventNOfThatDamageDamagePrevention(DamagePrevention):
    def __init__ (self, context, x_selector, y_selector, n):
        self.context_id = context.id
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.n = n

        self.text = "If " + str(self.x_selector) + " would deal damage to " + str(self.y_selector) + ", prevent " + str(n) + " of that damage."

    def canApply(self, game, damage, combat):
        context = game.obj(self.context_id)
        source, dest, n = damage
        if self.x_selector.contains_lki(game, context, source) and self.y_selector.contains_lki(game, context, dest):
            return True

        return False

    def apply(self, game, damage, combat):
        source, dest, n = damage
        return (source, dest, n - self.n)

class IfXWouldDealDamageToYPreventNOfThatDamage(ContinuousEffect):
    def __init__ (self, x_selector, y_selector, n):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.n = n

    def apply(self, game, obj):

        n = self.n
        if self.n == "X":
            n = obj.x

        game.damage_preventions.append(IfXWouldDealDamageToYPreventNOfThatDamageDamagePrevention(obj, self.x_selector, self.y_selector, n))

    def __str__ (self):
        return "IfXWouldDealDamageToYPreventNOfThatDamage(%s, %s, %s)" % (self.x_selector, self.y_selector, self.n)

class IfXWouldDealDamageToYItDealsDoubleThatDamageToThatYInstead(ContinuousEffect):
    def __init__ (self, x_selector, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector

    def apply(self, game, obj):
        game.add_volatile_event_handler("damage_replacement", partial(self.onDamageReplacement, obj.id))

    def isSelf(self):
        return isinstance(self.x_selector, SelfSelector) or isinstance(self.y_selector, SelfSelector)

    def onDamageReplacement(self, SELF_id, game, dr):
        SELF = game.obj(SELF_id)

        list = []
        for a,b,n in dr.list:
            if self.x_selector.contains_lki(game, SELF, a) and self.y_selector.contains_lki(game, SELF, b):
                list.append ( (a,b,n*2) )
            else:
                list.append ( (a,b,n) )

        dr.list = list

class TargetXGetsNNUntilEndOfTurn(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, power, toughness):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.power = power
        self.toughness = toughness

    def doResolve(self, game, obj, target):

        game.process_returns_push(True)

        power = self.power
        toughness = self.toughness
        if power == "+X":
            power = obj.x
        elif power == "-X":
            power = - obj.x
        if toughness == "+X":
            toughness = obj.x
        elif toughness == "-X":
            toughness = - obj.x
        
        game.until_end_of_turn_effects.append ( (obj, XGetsNN(LKISelector(target.get_lki_id()), power, toughness)))

    def __str__ (self):
        return "TargetXGetsNNUntilEndOfTurn(%s, %s, %s)" % (self.targetSelector, self.power, self.toughness)

class XGetsNNUntilEndOfTurn(OneShotEffect):
    def __init__(self, selector, power, toughness):
        self.selector = selector
        self.power = power
        self.toughness = toughness

    def resolve(self, game, obj):
        game.process_returns_push(True)
        game.until_end_of_turn_effects.append ( (obj, XGetsNN(self.selector, self.power, self.toughness)))

    def __str__ (self):
        return "XGetsNNUntilEndOfTurn(%s, %s, %s)" % (self.selector, self.power, self.toughness)

class XGetsTagUntilEndOfTurn(OneShotEffect):
    def __init__ (self, selector, tag):
        self.selector = selector
        self.tag = tag

    def resolve(self, game, obj):
        game.process_returns_push(True)
        game.until_end_of_turn_effects.append ( (obj, XGetsTag(self.selector, self.tag)) )

    def __str__ (self):
        return "XGetsTagUntilEndOfTurn(%s, %s)" % (self.selector, self.tag)

class TargetXGetsTagUntilEndOfTurn(SingleTargetOneShotEffect):
    def __init__ (self, selector, tag):
        SingleTargetOneShotEffect.__init__(self, selector)
        self.tag = tag

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
        game.until_end_of_turn_effects.append ( (obj, XGetsTag(LKISelector(target.get_lki_id()), self.tag)) )

    def __str__ (self):
        return "TargetXGetsTagUntilEndOfTurn(%s, %s)" % (self.targetSelector, self.tag)

class UpToNTargetXGetTagUntilEndOfTurn(MultipleTargetOneShotEffect):
    def __init__ (self, number, selector, tag):
        MultipleTargetOneShotEffect.__init__(self, selector, number, True)
        self.tag = tag

    def doResolve(self, game, obj, targets):
        game.process_returns_push(True)
        for target in targets.values():
            game.until_end_of_turn_effects.append ( (obj, XGetsTag(LKISelector(target), self.tag)) )

    def __str__ (self):
        return "UpToNTargetXGetTagUntilEndOfTurn(%s, %s, %s)" % (self.number, self.targetSelector, self.tag)

class DestroyTargetX(SingleTargetOneShotEffect):
    def __init__(self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
        game.doDestroy(target, obj)

    def __str__ (self):
        return "DestroyTargetX(%s)" % self.targetSelector

class BuryTargetX(SingleTargetOneShotEffect):
    def __init__(self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
        game.doBury(target, obj)

    def __str__ (self):
        return "BuryTargetX(%s)" % self.targetSelector
       
class DestroyTargetXYGainLifeEqualsToItsPower(SingleTargetOneShotEffect):
    def __init__(self, targetSelector, playerSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.playerSelector = playerSelector

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)

        game.doDestroy(target, obj)

        count = target.get_state().power
        for player in self.playerSelector.all(game, obj):
            game.doGainLife(player, count)

    def __str__ (self):
        return "DestroyTargetXYGainLifeEqualsToItsPower(%s, %s)" % (self.targetSelector, self.playerSelector)

class BuryTargetXYGainLifeEqualsToItsToughness(SingleTargetOneShotEffect):
    def __init__(self, targetSelector, playerSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.playerSelector = playerSelector

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)

        game.doBury(target, obj)

        count = target.get_state().toughness
        for player in self.playerSelector.all(game, obj):
            game.doGainLife(player, count)

    def __str__ (self):
        return "BuryTargetXYGainLifeEqualsToItsToughness(%s, %s)" % (self.targetSelector, self.playerSelector)

class DoXAtEndOfCombat(OneShotEffect):
    def __init__ (self, effect):
        self.effect = effect

    def resolve(self, game, obj):
        game.process_returns_push(True)

        e = game.create_effect_object(obj.get_source_lki().get_lki_id(), obj.get_controller_id(), self.effect, obj.get_slots())
        game.end_of_combat_triggers.append (e)

    def __str__ (self):
        return "DoXAtEndOfCombat(%s)" % self.effect

class DestroyX(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for o in self.selector.all(game, obj):
            if not o.is_moved():
                game.doDestroy(o, obj)

    def __str__ (self):
        return "DestroyX(%s)" % self.selector

class BuryX(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for o in self.selector.all(game, obj):
            if not o.is_moved():
                game.doBury(o, obj)

    def __str__ (self):
        return "BuryX(%s)" % self.selector

class TargetXDiscardsACard(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, count):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.count = count
    
    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
        from process import DiscardACardProcess
        n = self.count.evaluate(game, obj)
        for i in range(n):
            game.process_push(DiscardACardProcess(target.get_object(), obj))

    def __str__ (self):
        return "TargetXDiscardsACard(%s, %s)" % (self.targetSelector, self.count)

class TargetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, cardSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.cardSelector = cardSelector

    def doResolve(self, game, obj, target):
        from process import RevealHandAndDiscardACardProcess
        game.process_returns_push(True)
        game.process_push(RevealHandAndDiscardACardProcess(target.get_object(), game.objects[obj.get_state().controller_id], self.cardSelector, obj))

    def __str__ (self):
        return "TargetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard(%s, %s)" % (self.targetSelector, self.cardSelector)

class ChooseColorTargetXDiscardsCardsOfThatColorResolveProcess(SandwichProcess):
    def __init__ (self, player, obj):
        SandwichProcess.__init__ (self)
        self.player_id = player.id
        self.obj_id = obj.id

    def pre(self, game):
        player = game.obj(self.player_id)
        cards = game.get_hand(player).objects[:]
        from process import RevealCardsProcess
        game.process_push(RevealCardsProcess(player, cards))

    def main(self, game):
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)
        cards = game.get_hand(player).objects[:]

        for card in cards:
            if obj.modal in card.get_state().tags:
                game.doDiscard(player, card, obj)

class ChooseColorTargetXDiscardsCardsOfThatColorDoModalProcess:
    def __init__ (self, player, obj):
        self.player_id = player.id
        self.obj_id = obj.id

    def next(self, game, action):

        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        if action is None:
            colors = ["black", "blue", "green", "red", "white"]

            actions = []
            for name in colors:
                a = Action()
                a.text = name
                actions.append(a)

            return ActionSet (player.id, ("Choose a color"), actions)
        else:
            obj.modal = action.text.lower()
            game.process_returns_push(True)


class ChooseColorTargetXDiscardsCardsOfThatColor(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
    
    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
        game.process_push(ChooseColorTargetXDiscardsCardsOfThatColorResolveProcess(target.get_object(), obj))

    def doModal(self, game, player, obj):
        game.process_push(ChooseColorTargetXDiscardsCardsOfThatColorDoModalProcess(player, obj))

    def __str__ (self):
        return "ChooseColorTargetXDiscardsCardsOfThatColor(%s)" % (self.targetSelector)

class XMayPutYFromHandIntoPlayResolveProcess:
    def __init__ (self, obj, player, selector, tapped):
        self.obj_id = obj.id
        self.player_id = player.id
        self.selector = selector
        self.tapped = tapped

    def next(self, game, action):
        obj = game.obj(self.obj_id)
        player = game.obj(self.player_id)
        
        if action is None:
            actions = []
            for card in game.get_hand(player).objects:
                if self.selector.contains(game, obj, card):
                    _p = Action ()
                    _p.object_id = card.id
                    _p.text = "Put " + str(card) + " into play"
                    actions.append (_p)

            if len(actions) > 0:
                _pass = PassAction (player.id)
                _pass.text = "Pass"

                actions = [_pass] + actions

                return ActionSet (player.id, "Choose a card to put into play", actions)
        else:
            if action.object_id is not None:
                a_obj = game.obj(action.object_id)
                a_obj.tapped = self.tapped
                game.doZoneTransfer (a_obj, game.get_in_play_zone(), obj)
            

class XMayPutYFromHandIntoPlay(OneShotEffect):
    def __init__ (self, x_selector, y_selector, tapped = False):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.tapped = tapped

    def resolve(self, game, obj):
        game.process_returns_push(True)
        for player in self.x_selector.all(game, obj):
            game.process_push(XMayPutYFromHandIntoPlayResolveProcess(obj, player, self.y_selector, self.tapped))

    def __str__ (self):
        return "XMayPutYFromHandIntoPlay(%s, %s)" % (self.x_selector, self.y_selector)

class YouMayTapTargetX(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector, True)

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
        game.doTap(target.get_object())

    def __str__ (self):
        return "YouMayTapTargetX(%s)" % self.targetSelector

class TapTargetX(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector, False)

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
        game.doTap(target.get_object())

    def __str__ (self):
        return "TapTargetX(%s)" % self.targetSelector

class YouMayPayCostIfYouDoResolveProcess:
    def __init__ (self, player, obj, cost, effectText):
        self.player_id = player.id
        self.obj_id = obj.id
        self.cost = cost
        self.effectText = effectText
        self.state = 0

    def next(self, game, action):
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        if self.state == 0:
            if action is None:
                _pay = Action()
                _pay.text = "Yes"

                _notpay = Action()
                _notpay.text = "No"

                return ActionSet (player.id, ("Pay %s to %s?" % (", ".join(map(str, self.cost)), self.effectText)), [_pay, _notpay])

            else:
                if action.text == "Yes":
                    self.state = 1
                    game.process_push(self)
                    game.process_push(PayCostProcess(player, obj, obj, self.cost))
                else:
                    game.process_returns_push(True)

        elif self.state == 1:
            if game.process_returns_pop():
                game.process_returns_push(True)
                game.process_push(TriggerEffectProcess(obj, self.effectText, {}))
            else:
                game.process_returns_push(False)
            

class YouMayPayCostIfYouDoY(OneShotEffect):
    def __init__ (self, cost, effectText):
        self.cost = cost
        self.effectText = effectText

    def resolve(self, game, obj):
        controller = game.objects[obj.get_state().controller_id]
        game.process_push(YouMayPayCostIfYouDoResolveProcess(controller, obj, self.cost, self.effectText))

    def __str__ (self):
        return "YouMayPayCostIfYouDoY(%s, %s)" % (self.cost, self.effectText)

class PreventNextNDamageThatWouldBeDealtToXDamagePrevention(DamagePrevention):

    def __init__ (self, obj, effect):
        self.obj_id = obj.id
        self.effect = effect

    def canApply(self, game, damage, combat):
        source_lki, dest_lki, n = damage
        if self.effect.n <= 0:
            return False

        return self.effect.selector.contains_lki(game, game.obj(self.obj_id), dest_lki)

    def apply(self, game, damage, combat):
        source, dest, n = damage

        if n <= self.effect.n:
            self.effect.n -= n
            return (source, dest, 0)

        nd = self.effect.n
        self.effect.n = 0
        return (source, dest, n - nd)

    def getText(self):
        return "Prevent next " + str(self.effect.n) + " damage that would be dealt to " + str(self.effect.selector)

    def getEffect(self):
        return self.effect

    def setEffect(self, effect):
        self.effect = effect

class PreventNextNDamageThatWouldBeDealtToX(ContinuousEffect):
    def __init__ (self, selector, n):
        self.selector = selector
        self.n = n

    def apply(self, game, obj):
        game.damage_preventions.append(PreventNextNDamageThatWouldBeDealtToXDamagePrevention(obj, self))

class PreventNextNDamageThatWouldBeDealtToTargetXThisTurn(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, n):
        SingleTargetOneShotEffect.__init__(self, targetSelector, True)
        self.n = n

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)

        n = self.n
        if n == "X":
            n = obj.x

        game.until_end_of_turn_effects.append ( (obj, PreventNextNDamageThatWouldBeDealtToX(LKISelector(target.get_lki_id()), n)))

    def __str__ (self):
        return "PreventNextNDamageThatWouldBeDealtToTargetXThisTurn(%s, %s)" % (self.targetSelector, str(self.n))

class TheNextTimeXWouldDealDamageToYPreventThatDamageDamagePrevention(DamagePrevention):
    def __init__ (self, obj_id, effect):
        self.obj_id = obj_id
        self.effect = effect

    def canApply(self, game, damage, combat):
        source_lki_id, dest_lki_id, n = damage

        if self.effect.used_up:
            return False

        obj = game.obj(self.obj_id)

        return self.effect.x_selector.contains_lki(game, obj, source_lki_id) and self.effect.y_selector.contains_lki(game, obj, dest_lki_id)

    def apply(self, game, damage, combat):
        source, dest, n = damage

        self.effect.used_up = True

        return (source, dest, 0)

    def getText(self):
        return "Prevent damage that " + str(self.effect.x_selector) + " would deal to " + str(self.effect.y_selector) + "."

    def getEffect(self):
        return self.effect

    def setEffect(self, effect):
        self.effect = effect 

class TheNextTimeXWouldDealDamageToYPreventThatDamage(ContinuousEffect):
    def __init__ (self, x_selector, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.used_up = False

    def apply(self, game, obj):
        print `obj`
        assert game.obj(obj.get_id()) is not None
        game.damage_preventions.append(TheNextTimeXWouldDealDamageToYPreventThatDamageDamagePrevention(obj.get_id(), self))

class TheNextTimeSourceOfYourChoiceWouldDealDamageToYThisTurnPreventThatDamageResolveProcess(SandwichProcess):
    def __init__(self, obj, x_selector, y_selector):
        SandwichProcess.__init__ (self)
        self.obj_id = obj.id
        self.x_selector = x_selector
        self.y_selector = y_selector

    def pre(self, game):
        obj = game.obj(self.obj_id)
        from process import SelectSourceOfDamageProcess
        game.process_push(SelectSourceOfDamageProcess(game.objects[obj.get_controller_id()], obj, self.x_selector, "Choose a damage source", True))

    def main(self, game):
        obj = game.obj(self.obj_id)
        source = game.process_returns_pop()
        if source is not None:
            source = game.obj(source)
            game.until_end_of_turn_effects.append ( (obj, TheNextTimeXWouldDealDamageToYPreventThatDamage(LKISelector(game.create_lki(source)), self.y_selector)))

        game.process_returns_push(True)

class TheNextTimeSourceOfYourChoiceWouldDealDamageToYThisTurnPreventThatDamage(OneShotEffect):
    def __init__ (self, x_selector, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector

    def resolve(self, game, obj):
        game.process_push(TheNextTimeSourceOfYourChoiceWouldDealDamageToYThisTurnPreventThatDamageResolveProcess(obj, self.x_selector, self.y_selector))

    def __str__(self):
        return "TheNextTimeXWouldDealDamageToYThisTurnPreventThatDamage(%s, %s)" % (self.x_selector, self.y_selector) 

class PreventAllCombatDamagePrevention(DamagePrevention):
    def canApply(self, game, damage, combat):
        return combat

    def apply(self, game, damage, combat):
        source, dest, n = damage
        return (source, dest, 0)

    def getText(self):
        return "Prevent all combat damage."

class PreventAllCombatDamage(ContinuousEffect):
    def apply(self, game, obj):
        game.damage_preventions.append(PreventAllCombatDamagePrevention())

class PreventAllCombatDamageThatWouldBeDealtThisTurn(OneShotEffect):
    def resolve(self, game, obj):
        game.process_returns_push(True)
        game.until_end_of_turn_effects.append ( (obj, PreventAllCombatDamage()) )

    def __str__(self):
        return "PreventAllCombatDamageThatWouldBeDealtThisTurn()"

class XAddXToYourManaPool(OneShotEffect):
    def __init__ (self, selector, mana):
        self.selector = selector
        self.mana = mana

    def resolve(self, game, obj):
        game.process_returns_push(True)
        for player in self.selector.all(game, obj):
            player.get_object().manapool += self.mana

    def __str__ (self):
        return "XAddXToYourManaPool(%s, %s)" % (self.selector, self.mana)

class XAddXToYourManaPoolIfCAddYToYourManaPoolInstead(OneShotEffect):
    def __init__ (self, selector, m1, c, m2):
        self.selector = selector
        self.m1 = m1
        self.c = c
        self.m2 = m2

    def resolve(self, game, obj):
        game.process_returns_push(True)

        if self.c.evaluate(game, obj):
            for player in self.selector.all(game, obj):
                player.get_object().manapool += self.m2
        else:
            for player in self.selector.all(game, obj):
                player.get_object().manapool += self.m1

    def __str__ (self):
        return "XAddXToYourManaPoolIfCAddYToYourManaPoolInstead(%s, %s, %s, %s)" % (self.selector, self.m1, self.c, self.m2)


class RegenerateX(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for o in self.selector.all(game, obj):
            if not o.is_moved():
                game.doRegenerate(o)

    def __str__ (self):
        return "RegenerateX(%s)" % self.selector

class SearchLibraryForXProcess:
    def __init__ (self, player, owner, obj, selector, selectCardText, actionSetText):
        self.owner_id = owner.id
        self.player_id = player.id
        self.obj_id = obj.id
        self.selector = selector
        self.selectCardText = selectCardText
        self.actionSetText = actionSetText

    def next(self, game, action):
        from process import evaluate

        owner = game.obj(self.owner_id)
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        if action is None:
            self.old_looked_at = game.looked_at
            game.looked_at = game.looked_at.copy()

            actions = []
            for card in game.get_library(owner).objects:

                game.looked_at[player.id].append (card.get_id())
                
                if self.selector.contains(game, obj, card):
                    _p = Action ()
                    _p.object_id = card.id
                    _p.text = self.selectCardText % str(card)
                    actions.append (_p)

            if len(actions) > 0:
                _pass = PassAction (player.id)
                _pass.text = "Pass"

                actions = [_pass] + actions

                evaluate(game)

                return ActionSet (player.id, self.actionSetText, actions)
               
            else:
                game.looked_at = self.old_looked_at
                game.process_returns_push(None)

        else:
            game.looked_at = self.old_looked_at
            evaluate(game)

            if isinstance(action, PassAction):
                game.process_returns_push(None)
            else:
                game.process_returns_push(action.object_id)
           
class PutCardIntoPlayProcess:
    def __init__ (self, tapped, cause):
        self.tapped = tapped
        self.cause_id = cause.id

    def next(self, game, action):
        card_id = game.process_returns_pop()
        if card_id is not None:
            obj = game.obj(card_id)
            obj.tapped = self.tapped
            game.doZoneTransfer (obj, game.get_in_play_zone(), game.obj(self.cause_id))

class PutCardIntoPlayUnderPlayersControlProcess:
    def __init__ (self, controller, tapped, cause):
        self.tapped = tapped
        self.cause_id = cause.id
        self.controller_id = controller.id

    def next(self, game, action):
        card_id = game.process_returns_pop()
        if card_id is not None:
            obj = game.obj(card_id)
            obj.controller_id = self.controller_id
            obj.tapped = self.tapped
            game.doZoneTransfer (obj, game.get_in_play_zone(), game.obj(self.cause_id))

class PutCardIntoHandProcess:
    def __init__ (self, player, cause, reveal):
        self.player_id = player.id
        self.cause_id = cause.id
        self.reveal = reveal

    def next(self, game, action):
        player = game.obj(self.player_id)
        card_id = game.process_returns_pop()
        cause = game.obj(self.cause_id)

        if card_id is not None:
            card = game.obj(card_id)
            if self.reveal:
                from process import RevealCardsProcess

                self.reveal = False
                game.process_push(self)
                game.process_returns_push(card_id)
                game.process_push(RevealCardsProcess(player, [card]))
            else:
                game.doZoneTransfer (card, game.get_hand(player), cause)
           

class ShuffleLibraryProcess:
    def __init__ (self, player):
        self.player_id = player.id

    def next(self, game, action):
        player = game.obj(self.player_id)
        game.doShuffle(game.get_library(player))

class XSearchLibraryForXAndPutThatCardIntoPlay(OneShotEffect):
    def __init__ (self, x_selector, y_selector, tapped = False):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.tapped = tapped

    def resolve(self, game, obj):
        game.process_returns_push(True)
        for player in self.x_selector.all(game, obj):
            game.process_push(ShuffleLibraryProcess(player))
            game.process_push(PutCardIntoPlayProcess(self.tapped, obj))
            game.process_push(SearchLibraryForXProcess(player, player, obj, self.y_selector, "Put %s into play", "Choose a card to put into play"))

    def __str__ (self):
        return "XSearchLibraryForXAndPutThatCardIntoPlay(%s, %s)" % (self.x_selector, self.y_selector)

    

class XSearchLibraryForXAndPutItIntoHand(OneShotEffect):
    def __init__ (self, x_selector, y_selector, reveal = False):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.reveal = reveal

    def resolve(self, game, obj):
        game.process_returns_push(True)
        for player in self.x_selector.all(game, obj):
            game.process_push(ShuffleLibraryProcess(player))
            game.process_push(PutCardIntoHandProcess(player, obj, self.reveal))
            game.process_push(SearchLibraryForXProcess(player, player, obj, self.y_selector, "Put %s into your hand", "Choose a card to put into hand"))

    def __str__ (self):
        return "XSearchLibraryForXAndPutItIntoHand(%s, %s)" % (self.x_selector, self.y_selector)


class XRevealTopCardOfHisLibraryIfItIsYPutItInPlayOtherwisePutItIntoGraveyard(OneShotEffect):
    def __init__ (self, x_selector, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for player in self.x_selector.all(game, obj):

            library = game.get_library(player)
            graveyard = game.get_graveyard(player)
            in_play = game.get_in_play_zone()
            if len(library.objects) > 0:
                card = library.objects[-1]

                if self.y_selector.contains(game, obj, card):
                    game.doZoneTransfer(card, in_play, obj)
                else:
                    game.doZoneTransfer(card, graveyard, obj)


    def __str__ (self):
        return "XRevealTopCardOfHisLibraryIfItIsYPutItInPlayOtherwisePutItIntoGraveyard(%s, %s)" % (self.x_selector, self.y_selector)


class SearchTargetXsLibraryForYAndPutThatCardInPlayUnderYourControl(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, cardSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector, True)
        self.cardSelector = cardSelector

    def doResolve(self, game, obj, target):

        player = game.obj(obj.get_controller_id())
        libraryOwner = target.get_object()

        game.process_returns_push(True)
        game.process_push(ShuffleLibraryProcess(libraryOwner))
        game.process_push(PutCardIntoPlayUnderPlayersControlProcess(player, False, obj))
        game.process_push(SearchLibraryForXProcess(player, libraryOwner, obj, self.cardSelector, "Put %s into play", "Choose a card to put into play under your control"))

    def __str__ (self):
        return "SearchTargetXsLibraryForYAndPutThatCardInPlayUnderYourControl(%s,%s)" % (self.targetSelector, self.cardSelector)


class AbstractDoXUnlessYouCostProcess:
    def __init__ (self, controller, obj, costs, alternative_text):
        self.controller_id = controller.id
        self.obj_id = obj.id
        self.costs = costs
        self.alternative_text = alternative_text
        self.state = 0

    def next(self, game, action):
        controller = game.obj(self.controller_id)
        obj = game.obj(self.obj_id)

        if self.state == 0:
            if action is None:
                _pay = Action()
                _pay.text = "Pay %s" % str(map(str, self.costs))

                _notpay = Action()
                _notpay.text = self.alternative_text

                return ActionSet (controller.id, "Choose", [_pay, _notpay])
            else:
                if action.text == self.alternative_text:
                    self.state = 2
                    game.process_push(self)
                else:
                    self.state = 1
                    game.process_push(self)
                    game.process_push(PayCostProcess(controller, obj, obj, self.costs))

        elif self.state == 1:
            if not game.process_returns_pop():
                # costs not paid, doing the alternative
                self.state = 2
                game.process_push(self)
            else:
                # costs paid, exit
                pass

        elif self.state == 2:
            self.doAlternative(game, controller, obj)

    def doAlternative(self, game, controller, obj):
        pass

class SacrificeAllXUnlessYouCostProcess(AbstractDoXUnlessYouCostProcess):
    def __init__ (self, controller, selector, obj, costs):
        AbstractDoXUnlessYouCostProcess.__init__(self, controller, obj, costs, "Sacrifice %s" % selector)
        self.selector = selector

    def doAlternative(self, game, controller, obj):
        for o in self.selector.all(game, obj):
            if o.get_controller_id() == controller.id:
                # only controlled objects can be sacrificed
                game.doSacrifice(o, obj)
        

class SacrificeAllXUnlessYouCost(OneShotEffect):
    def __init__ (self, selector, costs):
        self.selector = selector
        self.costs = costs

    def resolve(self, game, obj):
        controller = game.objects[obj.get_state().controller_id]
        game.process_returns_push(True)
        game.process_push(SacrificeAllXUnlessYouCostProcess(controller, self.selector, obj, self.costs))
        
    def __str__ (self):
        return "SacrificeXUnlessYouCost(%s, %s)" % (self.selector, str(map(str,self.costs)))

class SacrificeAllX(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for o in self.selector.all(game, obj):
            if obj.get_controller_id() == o.get_controller_id():
                game.doSacrifice(o, obj)
        
    def __str__ (self):
        return "SacrificeX(%s)" % (self.selector)

class SacrificeYProcess:
    def __init__ (self, player, obj, selector):
        self.obj_id = obj.id
        self.player_id = player.id
        self.selector = selector

    def next(self, game, action):

        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        if action is None:
            _as = []
            for o in self.selector.all(game, obj):
                if o.get_controller_id() == player.get_id():
                    a = Action()
                    a.object_id = o.id
                    a.text = "Sacrifice %s" % str(o)
                    _as.append (a)

            if len(_as) > 0:
                return ActionSet (player.id, "Sacrifice %s" % self.selector, _as)

        else:
            game.doSacrifice(game.obj(action.object_id), obj)


class XSacrificeY(OneShotEffect):
    def __init__ (self, x_selector, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector

    def resolve(self, game, obj):
        game.process_returns_push(True)
        for player in self.x_selector.all(game, obj):
            game.process_push(SacrificeYProcess(player, obj, self.y_selector))
        
    def __str__ (self):
        return "XSacrificeY(%s)" % (self.x_selector, self.y_selector)

class ChooseEffectSelectProcess:
    def __init__ (self, player, obj, effect1, effect1text, effect2, effect2text):
        self.player_id = player.id
        self.obj_id = obj.id
        self.effect1 = effect1
        self.effect1text = effect1text
        self.effect2 = effect2
        self.effect2text = effect2text

    def next(self, game, action):

        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        if action is None:
            _option1 = Action()
            _option1.text = str(self.effect1text)

            _option2 = Action()
            _option2.text = str(self.effect2text)

            return ActionSet (player.id, "Choose", [_option1, _option2])

        else:
            if action.text == str(self.effect1text):
                obj.modal = 1
                effect = self.effect1
            else:
                obj.modal = 2
                effect = self.effect2

            effect.selectTargets(game, player, obj)

class ChooseEffect(Effect):

    def __init__ (self, effect1text, effect2text):
        self.effect1text = effect1text
        self.effect2text = effect2text

        from rules import effectRules
        self.effect1 = effectRules(effect1text).effect
        self.effect2 = effectRules(effect2text).effect

    def resolve(self, game, obj):
        if obj.modal == 1:
            self.effect1.resolve(game, obj)
        elif obj.modal == 2:
            self.effect2.resolve(game, obj)
        else:
            raise Exception("Not modal")

    def selectTargets(self, game, player, obj):
        game.process_push(ChooseEffectSelectProcess(player, obj, self.effect1, self.effect1text, self.effect2, self.effect2text))

    def validateTargets(self, game, obj):
        if obj.modal == 1:
            self.effect1.validateTargets(game, obj)
        elif obj.modal == 2:
            self.effect2.validateTargets(game, obj)
        else:
            raise Exception("Not modal")

    def __str__ (self):
        return "ChooseEffect(%s, %s)" % (self.effect1text, self.effect2text)

class TargetXGainLife(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, count):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.count = count
    
    def doResolve(self, game, obj, target):
        game.process_returns_push(True)

        n = self.count.evaluate(game, obj)
        game.doGainLife(target.get_object(), n)

    def __str__ (self):
        return "TargetXGainLife(%s, %s)" % (self.targetSelector, str(self.count))

class TargetXLoseLife(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, count):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.count = count
    
    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
   
        n = self.count.evaluate(game, obj)
        game.doLoseLife(target.get_object(), n)

    def __str__ (self):
        return "TargetXLoseLife(%s, %s)" % (self.targetSelector, str(self.count))

class AbstractPutCardsIntoLibraryProcess:
    def __init__ (self, player_id, card_ids):
        self.player_id = player_id
        self.card_ids = card_ids[:]
        self.message = None

    def next(self, game, action):
        from process import evaluate

        player = game.obj(self.player_id)
        library = game.get_library(player) 

        if len(self.card_ids) > 0:
            if action is None:
                self.old_looked_at = game.looked_at
                game.looked_at = game.looked_at.copy()

                options = []
                for card_id in self.card_ids:
                    card = game.obj(card_id)
                    _option = Action()
                    _option.text = str(card)
                    _option.object_id = card.id
                    options.append (_option)

                    game.looked_at[player.id].append(card.get_id())
        
                evaluate(game)

                return ActionSet (player.id, self.message, options)
            else:
                card = game.obj(action.object_id)
                self.card_ids.remove (card.id)
                
                self.putSelectedCard(game, library, card)

                game.looked_at = self.old_looked_at

                game.process_push(self) 
               
        else:
            evaluate(game)

    def putSelectedCard(self, library, card):
        pass

    def _copy(self, src):
        self.player_id = src.player_id
        self.card_ids = src.card_ids[:]
        self.mesage = src.message

    def __copy__ (self):
        raise Exception("not implemented")

class LookAtTopNCardsOfYourLibraryPutThemBackInAnyOrderResolveProcess(AbstractPutCardsIntoLibraryProcess):
    def __init__ (self, player_id, card_ids):
        AbstractPutCardsIntoLibraryProcess.__init__ (self, player_id, card_ids)
        self.message = "Put card on top of your library"

    def putSelectedCard(self, game, library, card):
        library.objects.remove(card)
        library.objects.append(card)

        # put the other cards we are looking at on top of the library
        for card_id in self.card_ids:
            card = game.obj(card_id)
            library.objects.remove(card)
            library.objects.append(card)

    def __copy__ (self):
        ret = LookAtTopNCardsOfYourLibraryPutThemBackInAnyOrderResolveProcess(self.player_id, self.card_ids)
        ret._copy(self)

        return ret


class LookAtTopNCardsOfYourLibraryPutThemBackInAnyOrder(OneShotEffect):
    def __init__ (self, n):
        self.n = n

    def resolve(self, game, obj):
        from process import evaluate

        player = game.objects[obj.get_controller_id()]
        library = game.get_library(player)

        if self.n == "X":
            n = obj.x
        else:
            n = self.n

        n = int(n)

        card_ids = []
        for i in range(n):
           if i < len(library.objects):
                card_ids.append(library.objects[-i-1].id)

        game.process_returns_push(True)
        game.process_push(LookAtTopNCardsOfYourLibraryPutThemBackInAnyOrderResolveProcess(player.get_id(), card_ids))

    def __str__ (self):
        return "LookAtTopNCardsOfYourLibraryPutThemBackInAnyOrder(%s)" % self.n


class PutCardsIntoHandProcess:
    def __init__ (self, player, obj, card_ids):
        self.player_id = player.id
        self.obj_id = obj.id
        self.card_ids = card_ids

    def next(self, game, action):
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)
        hand = game.get_hand(player)

        for card_id in self.card_ids:
            card = game.obj(card_id)
            game.doZoneTransfer(card, hand, obj)

# Process of moving cards from library or own hand to the bottom of the library
class PutCardsToTheBottomOfYourLibraryProcess(AbstractPutCardsIntoLibraryProcess):
    def __init__ (self, player_id, card_ids):
        AbstractPutCardsIntoLibraryProcess.__init__ (self, player_id, card_ids)
        self.message = "Put card to the bottom of your library"

    def putSelectedCard(self, game, library, card):
        zone = game.obj(card.zone_id)
        if zone.id == library.id:
            library.objects.remove(card)
            library.objects.insert(0, card)
        else:
            # moving objects from in play is more difficult
            assert zone.type != "in play"
            card.zone_id = library.id
            zone.objects.remove(card)
            library.objects.insert(0, card)

    def __copy__ (self):
        ret = PutCardsToTheBottomOfYourLibraryProcess(self.player_id, self.card_ids)
        ret._copy(self)

        return ret


class RevealTopNCardsOfYourLibraryPutAllXIntoYourHandAndTheRestOnTheBottomOfYourLibraryInAnyOrder(OneShotEffect):
    def __init__ (self, n, selector):
        self.n = n
        self.selector = selector

    def resolve(self, game, obj):

        from process import RevealCardsProcess

        player = game.objects[obj.get_controller_id()]
        library = game.get_library(player)

        if self.n == "X":
            n = obj.x
        else:
            n = self.n

        n = int(n)

        cards = []
        card_ids = []
        for i in range(n):
           if i < len(library.objects):
                card = library.objects[-i-1]
                cards.append(card)
                card_ids.append(card.id)

        card_ids_to_hand = []
        for card in cards[:]:
            if self.selector.contains(game, obj, card):
                card_ids_to_hand.append(card.id)
                card_ids.remove(card.id)

        game.process_returns_push(True)
        game.process_push(PutCardsToTheBottomOfYourLibraryProcess(player.get_id(), card_ids))
        game.process_push(PutCardsIntoHandProcess(player, obj, card_ids_to_hand))
        game.process_push(RevealCardsProcess(player, cards))

    def __str__ (self):
        return "LookAtTopNCardsOfYourLibraryPutThemBackInAnyOrder(%s)" % self.n

class XPutsTheCardsInHandOnTheBottomOfLibraryInAnyOrderThenDrawsThatManyCards(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        from process import DrawCardProcess

        player = self.selector.only(game, obj).get_object()
        hand = game.get_hand(player)
        library = game.get_library(player)

        n = len(hand.objects)
        card_ids = []
        for card in hand.objects:
            card_ids.append(card.id)

        game.process_returns_push(True)

        for i in range(n):
            game.process_push(DrawCardProcess(player))

        game.process_push(PutCardsToTheBottomOfYourLibraryProcess(player.get_id(), card_ids))

    def __str__ (self):
        return "XPutsTheCardsInHandOnTheBottomOfLibraryInAnyOrderThenDrawsThatManyCards(%s)" % self.selector

class CounterXUnlessYouCostProcess(AbstractDoXUnlessYouCostProcess):
    def __init__ (self, controller, target, obj, costs):
        AbstractDoXUnlessYouCostProcess.__init__(self, controller, obj, costs, "Counter %s" % target)
        self.target_id = target.get_id()

    def doAlternative(self, game, controller, obj):
        target = game.obj(self.target_id)
        game.doCounter(target)

class CounterTargetXUnlessItsControllerPaysCost(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, costs):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.costs = costs
    
    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
        controller = game.objects[target.get_state().controller_id]
        game.process_push(CounterXUnlessYouCostProcess(controller, target, obj, self.costs))

    def __str__ (self):
        return "CounterTargetXUnlessItsControllerPaysCost(%s, %s)" % (self.targetSelector, str(map(str,self.costs)))

class CounterTargetX(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.process_returns_push(game.doCounter(target))

    def __str__ (self):
        return "CounterTargetX(%s)" % (self.targetSelector)

class ReturnXToOwnerHands(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for o in self.selector.all(game, obj):
            if not o.is_moved():
                owner = game.objects[o.get_object().owner_id]
                hand = game.get_hand(owner)
                game.doZoneTransfer(o.get_object(), hand, obj)

    def __str__ (self):
        return "ReturnXToOwnerHands(%s)" % self.selector

class ReturnTargetXToOwnerHands(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, optional = False):
        SingleTargetOneShotEffect.__init__(self, targetSelector, optional)

    def doResolve(self, game, obj, target):

        game.process_returns_push(True)

        owner = game.objects[target.get_object().owner_id]
        hand = game.get_hand(owner)
        game.doZoneTransfer(target.get_object(), hand, obj)

    def __str__ (self):
        return "ReturnTargetXToOwnerHands(%s)" % self.targetSelector

class ReturnXToPlay(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for o in self.selector.all(game, obj):
            if not o.is_moved():
                in_play = game.get_in_play_zone()
                game.doZoneTransfer(o.get_object(), in_play, obj)

    def __str__ (self):
        return "ReturnXToPlay(%s)" % self.selector

class ReturnTargetXToPlay(SingleTargetOneShotEffect):
    def __init__ (self, selector):
        SingleTargetOneShotEffect.__init__(self, selector)

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)

        if not target.is_moved():
            in_play = game.get_in_play_zone()
            game.doZoneTransfer(target.get_object(), in_play, obj)

    def __str__ (self):
        return "ReturnTargetXToPlay(%s)" % self.targetSelector

class YouMayTapOrUntapTargetXResolveProcess:
    def __init__ (self, player_id, obj, target_lki):
        self.player_id = player_id
        self.obj_id = obj.id
        self.target_lki = target_lki

    def next(self, game, action):
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)
        if action is None:
            _pass = PassAction(player.id)

            _tap = Action()
            _tap.text = "Tap"

            _untap = Action()
            _untap.text = "Untap"

            return ActionSet (player.id, "You may tap or untap target", [_pass, _tap, _untap])
        else:
            game.process_returns_push(True)
            if action.text == "Tap":
                game.doTap(game.lki(self.target_lki))
            elif action.text == "Untap":
                game.doUntap(game.lki(self.target_lki))


class YouMayTapOrUntapTargetX(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        controller_id = obj.get_controller_id()
        game.process_push(YouMayTapOrUntapTargetXResolveProcess(controller_id, obj, target.get_lki_id()))

    def __str__ (self):
        return "YouMayTapOrUntapTargetX(%s)" % (self.targetSelector)

class UntapAllX(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for o in self.selector.all(game, obj):
            game.doUntap(o)

    def __str__ (self):
        return "UntapAllX(%s)" % (self.selector)

class TapAllX(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for o in self.selector.all(game, obj):
            game.doTap(o)

    def __str__ (self):
        return "TapAllX(%s)" % (self.selector)

class UntapUpToNXProcess:
    def __init__ (self, player, obj, number, selector):
        self.player_id = player.id
        self.obj_id = obj.id
        self.number = number
        self.selector = selector
        self.i = 0

    def next(self, game, action):
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        if self.i < self.number:
            if action is None:
                actions = []
                _pass = PassAction(player.id)
                actions.append (_pass)
                for o in self.selector.all(game, obj):
                    if o.tapped:
                        a = Action()
                        a.text = "Untap %s" % (str(o))
                        a.object_id = o.id
                        actions.append (a)

                return ActionSet(player.id, "Untap up to %d %s" % (self.number - self.i, str(self.selector)), actions)
            else:
                if not isinstance(action, PassAction):
                    self.i += 1
                    game.process_push(self)
                    game.doUntap(game.obj(action.object_id))

class UntapUpToNX(OneShotEffect):
    def __init__ (self, number, selector):
        self.number = number
        self.selector = selector

    def resolve(self, game, obj):
        n = self.number.evaluate(game, obj)

        player = game.objects[obj.get_controller_id()]
        
        game.process_returns_push(True)
        game.process_push(UntapUpToNXProcess(player, obj, n, self.selector))

    def __str__ (self):
        return "UntapUpToNX(%s, %s)" % (self.number, self.selector)
  
class PlayerMayDrawACardResolveProcess(Process):
    def __init__ (self, player):
        self.player_id = player.id

    def next(self, game, action):
        player = game.obj(self.player_id)
        if action == None:
            _yes = Action()
            _yes.text = "Yes"

            _no = Action()
            _no.text = "No"

            _as = ActionSet (player.id, ("Draw a card?"), [_yes, _no])
            return _as
        else:
            game.process_returns_push(True)
            if action.text == "Yes":
                game.doDrawCard(player)
        

class XMayDrawACard(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        player = self.selector.only(game, obj)
        game.process_push(PlayerMayDrawACardResolveProcess(player))

    def __str__ (self):
        return "XMayDrawACard(%s)" % self.selector

class DrawCards(OneShotEffect):
    def __init__ (self, selector, number):
        self.selector = selector
        self.number = number

    def resolve(self, game, obj):
        game.process_returns_push(True)

        n = self.number.evaluate(game, obj)
        for o in self.selector.all(game, obj):
            for i in range(n):
                game.doDrawCard(o)
        
    def __str__ (self):
        return "DrawCards(%s, %s)" % (self.selector, str(self.number))

class TargetXDrawCards(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, number):
        SingleTargetOneShotEffect.__init__(self, targetSelector, False)
        self.number = number

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)

        n = self.number.evaluate(game, obj)
        for i in range(n):
            game.doDrawCard(target.get_object())

    def __str__ (self):
        return "TargetXDrawCards(%s, %s)" % (self.targetSelector, self.number)

class AndProcess(Process):
    def next(self, game, action):
        first = game.process_returns_pop()
        second = game.process_returns_pop()
        game.process_returns_push(first and second)

class XAndY(OneShotEffect):
    def __init__ (self, x, y):
        self.x = x
        self.y = y

    def resolve(self, game, obj):
        game.process_push(AndProcess())
        self.x.resolve(game, obj)
        self.y.resolve(game, obj)

    def selectTargets(self, game, player, obj):
        game.process_push(AndProcess())
        self.x.selectTargets(game, player, obj)
        self.y.selectTargets(game, player, obj)

    def validateTargets(self, game, obj):
        game.process_push(AndProcess())
        self.x.validateTargets(game, obj)
        self.y.validateTargets(game, obj)

    def __str__(self):
        return "XAndY(%s, %s)" % (self.x, self.y)

class XCostsNLessToCast(ContinuousEffect):
    def __init__ (self, selector, n):
        self.selector = selector
        self.n = n

    def apply(self, game, obj):
        game.play_cost_replacement_effects.append (partial(self.replace, obj.id))

    def replace(self, context_id, game, ability, obj, player, costs):
        context = game.obj(context_id)

        if self.selector.contains(game, context, obj):
            ret = []
            for c in costs:
                if isinstance(c, ManaCost):
                    manacost = mana_diff(c.manacost, self.n)
                    rc = ManaCost(manacost)
                    ret.append(rc)
                else:
                    ret.append(c)

            return ret

        return costs

    def __str__ (self):
        return "XCostsNLessToCast(%s, %s)" % (self.selector, self.n)

    def isSelf(self):
        return isinstance(self.selector, SelfSelector)

class XCostsNMoreToCastExceptDuringItsControllersTurn(ContinuousEffect):
    def __init__ (self, selector, n):
        self.selector = selector
        self.n = n

    def apply(self, game, obj):
        # TODO: 
        game.play_cost_replacement_effects.append (partial(self.replace, obj.id))

    def isSelf(self):
        return isinstance(self.selector, SelfSelector)

    def replace(self, context_id, game, ability, obj, player, costs):
        context = game.obj(context_id)

        if self.selector.contains(game, context, obj) and player.id != game.active_player_id:
            ret = []
            replaced = False
            for c in costs:
                if isinstance(c, ManaCost):
                    c.manacost += self.n
                    ret.append(c)
                    replaced = True
                else:
                    ret.append(c)

            if not replaced:
                ret.append(ManaCost(self.n))

            return ret

        return costs

    def __str__ (self):
        return "XCostsNMoreToCastExceptDuringItsControllersTurn(%s, %s)" % (self.selector, self.n)

class IfTargetPlayerHasMoreCardsInHandThanYouDrawCardsEqualToTheDifference(SingleTargetOneShotEffect):
    def __init__(self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)

        for you in YouSelector().all(game, obj):
            for player in self.targetSelector.all(game, obj):
                you_hand = game.get_hand(you)
                player_hand = game.get_hand(player)

                if len(player_hand.objects) > len(you_hand.objects):
                    for i in range(len(player_hand.objects) - len(you_hand.objects)):
                        game.doDrawCard(you)

    def __str__ (self):
        return "IfTargetPlayerHasMoreCardsInHandThanYouDrawCardsEqualToTheDifference(%s)" % (self.targetSelector)

class XPowerAndToughnessAreEachEqualToN(ContinuousEffect):
    def __init__ (self, x_selector, n):
        self.x_selector = x_selector
        self.n = n

    def apply(self, game, obj):

        n = self.n.evaluate(game, obj)

        for o in self.x_selector.all(game, obj):
            o.get_state().power = n
            o.get_state().toughness = n

    def __str__ (self):
        return "XPowerAndToughnessAreEachEqualToN(%s, %s)" % (self.x_selector, self.n)

    def isSelf(self):
        return isinstance(self.x_selector, SelfSelector)

    def getLayer(self):
        return "power_set"

class XPowerIsNAndToughnessIsM(ContinuousEffect):
    def __init__ (self, selector, powerNumber, toughnessNumber):
        self.selector = selector
        self.powerNumber = powerNumber
        self.toughnessNumber = toughnessNumber

    def apply(self, game, obj):

        power = self.powerNumber.evaluate(game, obj)
        toughness = self.toughnessNumber.evaluate(game, obj)

        for o in self.selector.all(game, obj):
            o.get_state().power = power
            o.get_state().toughness = toughness

    def __str__ (self):
        return "XPowerIsNAndToughnessIsM(%s, %s, %s)" % (self.selector, self.powerNumber, self.toughnessNumber)

    def isSelf(self):
        return isinstance(self.selector, SelfSelector)

    def getLayer(self):
        return "power_set"

class XPowerIsN(ContinuousEffect):
    def __init__ (self, selector, powerNumber):
        self.selector = selector
        self.powerNumber = powerNumber

    def apply(self, game, obj):

        power = self.powerNumber.evaluate(game, obj)

        for o in self.selector.all(game, obj):
            o.get_state().power = power

    def __str__ (self):
        return "XPowerIsN(%s, %s)" % (self.selector, self.powerNumber)

    def isSelf(self):
        return isinstance(self.selector, SelfSelector)

    def getLayer(self):
        return "power_set"

class XAddNManaOfAnyColorToYourManapoolResolveProcess(Process):
    def __init__ (self, player):
        self.player_id = player.id

    def next(self, game, action):

        player = game.obj(self.player_id)
        colors = ["W","R","B","U","G"]
        names = ["White", "Red", "Black", "Blue", "Green"] 

        if action is None:
            actions = []
            for name in names:
                a = Action()
                a.text = name
                actions.append(a)

            _as = ActionSet (player.id, ("Choose a color"), actions)
            return _as
        else:
            color = colors[names.index(action.text)]
            player.manapool += color

class XAddNManaOfAnyColorToYourManapool(OneShotEffect):
    def __init__ (self, selector, n):
        self.selector = selector
        self.n = n

    def resolve(self, game, obj):
        game.process_returns_push(True)
        for player in self.selector.all(game, obj):
            for i in range(self.n):
                game.process_push(XAddNManaOfAnyColorToYourManapoolResolveProcess(player))

    def __str__ (self):
        return "XAddNManaOfAnyColorToYourManapool(%s, %s)" % (self.selector, str(self.n))

class XAddOneOfTheseManaToYourManaPoolProcess:
    def __init__ (self, player, options):
        self.player_id = player.id
        self.options = options

    def next(self, game, action):
        player = game.obj(self.player_id)
        if action is None:
            actions = []
            for o in self.options:
                a = Action()
                a.text = o
                actions.append(a)

            return ActionSet (player.id, ("Choose mana"), actions)
        else:
            mana = action.text
            player.manapool += mana

class XAddOneOfTheseManaToYourManaPool(OneShotEffect):
    def __init__ (self, selector, options):
        self.options = options
        self.selector = selector

    def resolve(self, game, obj):

        game.process_returns_push(True)

        for player in self.selector.all(game, obj):
            game.process_push(XAddOneOfTheseManaToYourManaPoolProcess(player, self.options))

    def __str__ (self):
        return "XAddOneOfTheseManaToYourManaPool(%s, %s)" % (self.selector, str(self.options))

class AddNManaOfAnyColorBasicLandControlsCouldProduceToYourManapool(OneShotEffect):
    def __init__ (self, n):
        self.n = n

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for player in YouSelector().all(game, obj):
            producable = []
            for land in BasicLandYouControlSelector().all(game, obj):
                if "mountain" in land.get_state().subtypes:
                    producable.append ("R")
                if "island" in land.get_state().subtypes:
                    producable.append ("U")
                if "plains" in land.get_state().subtypes:
                    producable.append ("W")
                if "forest" in land.get_state().subtypes:
                    producable.append ("G")
                if "swamp" in land.get_state().subtypes:
                    producable.append ("B")

            if len(producable) > 0:
                for i in range(self.n):
                    game.process_push(XAddOneOfTheseManaToYourManaPoolProcess(player, producable))

    def __str__ (self):
        return "AddNManaOfAnyColorBasicLandControlsCouldProduceToYourManapool(%s)" % (str(self.n))

class PlayerSkipsNextCombatPhase(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for player in self.selector.all(game, obj):
            player.get_object().skip_next_combat_phase = True

    def __str__ (self):
        return "PlayerSkipsNextCombatPhase(%s)" % (self.selector)

class XIsBasicLandType(ContinuousEffect):
    def __init__ (self, selector, subtype):
        self.selector = selector
        self.subtype = subtype

    def apply(self, game, obj):
        for o in self.selector.all(game, obj):
            o.get_state().subtypes.add(self.subtype)

            # remove any rule-based abilities
            for ability in o.get_object().rules.abilities:
                o.get_state().abilities.remove(ability)

    def __str__ (self):
        return "XIsBasicLandType(%s, %s)" % (self.selector, self.subtype)

    def isSelf(self):
        return isinstance(self.selector, SelfSelector)

    def getLayer(self):
        return "type"

class XControlsY(ContinuousEffect):
    def __init__ (self, x_selector, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector

    def apply(self, game, obj):

        controller = self.x_selector.only(game, obj)

        for o in self.y_selector.all(game, obj):
            if controller.id != o.get_state().controller_id:
                o.get_state().controller_id = controller.id

    def __str__ (self):
        return "XControlsY(%s, %s)" % (self.x_selector, self.y_selector)

    def getLayer(self):
        return "control"

class ChangeTargetOfTargetX(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        target.get_object().rules.selectTargets(game, game.objects[obj.get_controller_id()], target.get_object())

    def __str__ (self):
        return "ChangeTargetOfTargetX(%s)" % (self.targetSelector)

class TargetXBecomesTheColorOfYourChoiceUntilEndOfTurnProcess:
    def __init__(self, player, obj, target_lki_id):
        self.obj_id = obj.id
        self.player_id = player.id
        self.target_lki_id = target_lki_id

    def next(self, game, action):
        obj = game.obj(self.obj_id)
        player = game.obj(self.player_id)
        if action is None:
            actions = []
            for name in ["White", "Red", "Black", "Blue", "Green"] :
                a = Action()
                a.text = name
                actions.append(a)

            return ActionSet (player.id, ("Choose a color"), actions)
        else:
            color = action.text.lower()
            game.until_end_of_turn_effects.append ( (obj, XGetsTag(LKISelector(self.target_lki_id), color)))

class TargetXBecomesTheColorOfYourChoiceUntilEndOfTurn(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        controller = game.objects[obj.get_controller_id()]

        game.process_returns_push(True)
        game.process_push(TargetXBecomesTheColorOfYourChoiceUntilEndOfTurnProcess(controller, obj, target.get_lki_id()))

    def __str__ (self):
        return "TargetXBecomesTheColorOfYourChoiceUntilEndOfTurn(%s)" % (self.targetSelector)

class PutXCounterOnY(OneShotEffect):
    def __init__ (self, counter, selector):
        self.counter = counter
        self.selector = selector

    def resolve(self, game, obj):
        game.process_returns_push(True)

        for o in self.selector.all(game, obj):
            if not o.is_moved():
                o.get_object().counters.append (self.counter)

    def __str__ (self):
        return "PutXCounterOnY(%s, %s)" % (self.counter, self.selector)

class AtTheBeginningOfEachPlayerDrawStepIfXThatPlayerDrawsAnAdditionalCard(ContinuousEffect):
    def __init__ (self, condition):
        self.condition = condition

    def apply(self, game, obj):
        if game.current_step == "draw" and self.condition.evaluate(game, obj):
            game.get_active_player().draw_cards_count += 1

    def __str__ (self):
        return "AtTheBeginningOfEachPlayerDrawStepIfXThatPlayerDrawsAnAdditionalCard(%s)" % (self.condition)

class XIsANNCTCreature(ContinuousEffect):
    def __init__ (self, selector, powerNumber, toughnessNumber, color, type):
        self.selector = selector
        self.powerNumber = powerNumber
        self.toughnessNumber = toughnessNumber
        self.color = color
        self.type = type

    def apply(self, game, obj):
        power = self.powerNumber.evaluate(game, obj)
        toughness = self.toughnessNumber.evaluate(game, obj)

        for o in self.selector.all(game, obj):
            o.get_state().power = power
            o.get_state().toughness = toughness
            o.get_state().tags.add(self.color)
            o.get_state().types.add("creature")
            o.get_state().subtypes.add(self.type)

    def __str__ (self):
        return "XIsANNCTCreature(%s, %s, %s, %s, %s)" % (self.selector, self.powerNumber, self.toughnessNumber, self.color, self.type)

    def getLayer(self):
        # TODO: should be multiple
        return "type"

class XIsANNCreature(ContinuousEffect):
    def __init__ (self, selector, powerNumber, toughnessNumber):
        self.selector = selector
        self.powerNumber = powerNumber
        self.toughnessNumber = toughnessNumber

    def apply(self, game, obj):
        power = self.powerNumber.evaluate(game, obj)
        toughness = self.toughnessNumber.evaluate(game, obj)

        for o in self.selector.all(game, obj):
            o.get_state().power = power
            o.get_state().toughness = toughness
            o.get_state().types.add("creature")

    def __str__ (self):
        return "XIsANNCreature(%s, %s, %s)" % (self.selector, self.powerNumber, self.toughnessNumber)

    def getLayer(self):
        # TODO: should be multiple
        return "type"

class AllXBecomeNNCreaturesUntilEndOfTurn(OneShotEffect):
    def __init__ (self, selector, powerNumber, toughnessNumber):
        self.selector = selector
        self.powerNumber = powerNumber
        self.toughnessNumber = toughnessNumber

    def resolve(self, game, obj):
        game.process_returns_push(True)

        power = self.powerNumber.evaluate(game, obj)
        toughness = self.toughnessNumber.evaluate(game, obj)

        from numberof import NNumber

        for o in self.selector.all(game, obj):
            game.until_end_of_turn_effects.append ( (o, XIsANNCreature(LKISelector(game.create_lki(o)), NNumber(power), NNumber(toughness))))

    def __str__ (self):
        return "AllXBecomeNNCreaturesUntilEndOfTurn(%s, %s, %s)" % (self.selector, self.powerNumber, self.toughnessNumber)

class YouAndXEachFlipCoinSELFDealsNDamageToEachPlayerWhoseCoinComesUpTailsRepeatThisProcessUntilBothPlayersCoinsComeUpHeadsOnTheSameFlipProcess:
    def __init__ (self, obj, player, target, n):
        self.obj_id = obj.id
        self.player_id = player.id
        self.target_id = target.get_id()
        self.state = 0
        self.n = n

    def next(self, game, action):

        from process import CoinFlipProcess

        obj = game.obj(self.obj_id)
        player = game.obj(self.player_id)
        target = game.obj(self.target_id)

        if self.state == 0:
            self.state = 1
            game.process_push(self) 

            game.process_push(CoinFlipProcess(target))
            game.process_push(CoinFlipProcess(player))

        elif self.state == 1:
            targetflip = game.process_returns_pop()
            playerflip = game.process_returns_pop()

            damage = []
            if playerflip == "tails":
                damage.append ( (game.create_lki(obj.get_source_lki()), game.create_lki(player), self.n) )
            if targetflip == "tails":
                damage.append ( (game.create_lki(obj.get_source_lki()), game.create_lki(target), self.n) )

            if playerflip == "heads" and targetflip == "heads":
                pass
            else:
                self.state = 0
                game.process_push(self)
                game.doDealDamage(damage)


class YouAndTargetXEachFlipCoinSELFDealsNDamageToEachPlayerWhoseCoinComesUpTailsRepeatThisProcessUntilBothPlayersCoinsComeUpHeadsOnTheSameFlip(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, n):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.n = n

    def doResolve(self, game, obj, target):
        you = YouSelector().only(game, obj)

        n = self.n.evaluate(game, obj)

        game.process_returns_push(True)
        game.process_push(YouAndXEachFlipCoinSELFDealsNDamageToEachPlayerWhoseCoinComesUpTailsRepeatThisProcessUntilBothPlayersCoinsComeUpHeadsOnTheSameFlipProcess(obj, you, target, n))

    def __str__ (self):
        return "YouAndTargetXEachFlipCoinSELFDealsNDamageToEachPlayerWhoseCoinComesUpTailsRepeatThisProcessUntilBothPlayersCoinsComeUpHeadsOnTheSameFlip(%s, %s)" % (self.targetSelector, self.n)
 
class TargetXPutsTheTopNCardsOfLibraryIntoGraveyard(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, number):
        SingleTargetOneShotEffect.__init__(self, targetSelector, False)
        self.number = number

    def doResolve(self, game, obj, target):

        game.process_returns_push(True)

        n = self.number.evaluate(game, obj)
        library = game.get_library(target.get_object())
        graveyard = game.get_graveyard(target.get_object())
        for i in range(n):
            if len(library.objects) == 0:
                game.doLoseGame(target.get_object())
            else:
                card = library.objects[-1]
                game.doZoneTransfer(card, graveyard, obj)

    def __str__ (self):
        return "TargetXPutsTheTopNCardsOfLibraryIntoGraveyard(%s, %s)" % (self.targetSelector, self.number)

class ChangeTheTextOfXByReplacingAllInstancesOfAWithB(ContinuousEffect):
    def __init__ (self, selector, a, b):
        self.selector = selector
        self.a = a
        self.b = b

    def apply(self, game, obj):
        for o in self.selector.all(game, obj):
            o.get_state().text = o.get_state().text.replace(self.a, self.b)

    def __str__ (self):
        return "ChangeTheTextOfXByReplacingAllInstancesOfAWithB(%s, %s, %s)" % (self.selector, self.a, self.b)

    def getLayer(self):
        return "text"

class ChangeTheTextOfTargetXByReplacingAllInstancesOfOneColorWordWithAnotherOrOneBasicLandTypeWithAnotherProcess:
    def __init__(self, player, obj):
        self.player_id = player.id
        self.obj_id = obj.id

        self.what = None

    def next(self, game, action):
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        colors = ["black", "blue", "green", "red", "white"]
        lands = ["forest", "island", "mountain", "plains", "swamp"]

        options = colors + lands

        if self.what is None:
            if action is None:
                actions = []
                for name in options:
                    a = Action()
                    a.text = name
                    actions.append(a)

                return ActionSet (player.id, ("Choose a color or a basic land type"), actions)
            else:
                self.what = action.text.lower()
                if self.what in colors:
                    subset = colors
                else:
                    subset = lands

                actions = []
                for name in subset:
                    if name != self.what:
                        a = Action()
                        a.text = name
                        actions.append(a)

                return ActionSet (player.id, ("Change '%s' to..." % self.what), actions)
        else:
            to = action.text.lower()
            obj.modal = (self.what, to)
            

class ChangeTheTextOfTargetXByReplacingAllInstancesOfOneColorWordWithAnotherOrOneBasicLandTypeWithAnother(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doModal(self, game, player, obj):
        game.process_returns_push(True)
        game.process_push(ChangeTheTextOfTargetXByReplacingAllInstancesOfOneColorWordWithAnotherOrOneBasicLandTypeWithAnotherProcess(player, obj))

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
        game.indefinite_effects.append ( (obj, target, ChangeTheTextOfXByReplacingAllInstancesOfAWithB(LKISelector(target.get_lki_id()), obj.modal[0], obj.modal[1])))

    def __str__ (self):
        return "ChangeTheTextOfTargetXByReplacingAllInstancesOfOneColorWordWithAnotherOrOneBasicLandTypeWithAnother(%s)" % (self.targetSelector)


class ConditionalEffect(ContinuousEffect):
    def __init__ (self, condition, effect):
        self.condition = condition
        self.effect = effect

    def apply(self, game, obj):
        if self.condition.evaluate(game, obj):
            self.effect.apply(game, obj)

    def isSelf(self):
        return self.effect.isSelf()

    def __str__ (self):
        return "ConditionalEffect(%s, %s)" % (self.condition, self.effect)

    def getLayer(self):
        return self.effect.getLayer()

class AllDamageThatWouldBeDealtToXByYIsDealtToZInstead(ContinuousEffect):
    def __init__ (self, x_selector, y_selector, z_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.z_selector = z_selector

    def apply(self, game, obj):
        game.add_volatile_event_handler("damage_replacement", partial(self.onDamageReplacement, obj.id))

    def isSelf(self):
        return isinstance(self.x_selector, SelfSelector) or isinstance(self.y_selector, SelfSelector) or isinstance(self.z_selector, SelfSelector)

    def onDamageReplacement(self, SELF_id, game, dr):
        SELF = game.obj(SELF_id)

        list = []

        # TODO: make an selector api for that 
        if isinstance(self.z_selector, LKISelector):
            c = self.z_selector.lki_id
        else:
            c = self.z_selector.only(game, SELF)
            c = game.create_lki(c)

        for a,b,n in dr.list:
            if self.x_selector.contains_lki(game, SELF, b) and self.y_selector.contains_lki(game, SELF, a):
                list.append ( (a,c,n) )
            else:
                list.append ( (a,b,n) )

        dr.list = list

class SetReturnedObjectAsModalLKIProcess:
    def __init__ (self, obj):
        self.obj_id = obj.id

    def next(self, game, action):
        obj = game.obj(self.obj_id)
        s_id = game.process_returns_pop()
        if s_id is not None:
            s_lki = game.create_lki(game.obj(s_id))
            obj.modal = s_lki
            game.process_returns_push(True)
        else:
            game.process_returns_push(False)

class AllDamageThatWouldBeDealtToTargetXThisTurnByAYOfYourChoiceIsDealtToZInstead(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, y_selector, z_selector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.y_selector = y_selector
        self.z_selector = z_selector

    def doModal(self, game, player, obj):
        from process import SelectSourceOfDamageProcess
        game.process_push(SetReturnedObjectAsModalLKIProcess(obj))
        game.process_push(SelectSourceOfDamageProcess(player, obj, self.y_selector, "Choose a source of damage", False))

    def doResolve(self, game, obj, target):

        game.process_returns_push(True)

        z_lki = game.create_lki(self.z_selector.only(game, obj))
        if obj.modal is not None:
            game.until_end_of_turn_effects.append ( (obj, AllDamageThatWouldBeDealtToXByYIsDealtToZInstead(LKISelector(target.get_lki_id()), LKISelector(obj.modal), LKISelector(z_lki)) ) )

    def __str__ (self):
        return "AllDamageThatWouldBeDealtToTargetXThisTurnByASourceOfYourChoiceIsDealtToYInstead(%s, %s, %s)" % (self.targetSelector, self.y_selector, self.z_selector)


class LookAtTheTopNCardsOfTargetPlayersLibrary(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, number):
        SingleTargetOneShotEffect.__init__(self, targetSelector, False)
        self.number = number

    def doResolve(self, game, obj, target):
        n = self.number.evaluate(game, obj)
        you = YouSelector().only(game, obj)
        library = game.get_library(target.get_object())

        card_ids = []

        for i in range(n):
            if len(library.objects) > i:
                card_ids.append (library.objects[-i - 1].id)

        from process import LookAtCardsProcess
        game.process_returns_push(True)
        game.process_push(LookAtCardsProcess(you, card_ids))

    def __str__ (self):
        return "LookAtTheTopNCardsOfTargetPlayersLibrary(%s, %s)" % (self.targetSelector, self.number)

class PutNTargetXOnTopOfOwnersLibraries(MultipleTargetOneShotEffect):
    def __init__ (self, number, selector):
        MultipleTargetOneShotEffect.__init__(self, selector, number, False)

    def doResolve(self, game, obj, targets):
        game.process_returns_push(True)

        for target_lki in targets.values():
            target = game.lki(target_lki)
            library = game.get_library(game.objects[target.get_state().owner_id])
            if not target.is_moved():
                game.doZoneTransfer(target.get_object(), library, obj)

    def __str__ (self):
        return "PutNTargetXOnTopOfOwnersLibraries(%s, %s)" % (self.number, self.targetSelector)

class DealsNDamageDividedAsYouChooseAmongAnyNumberOfTargetXSelectTargetsProcess(SandwichProcess):
    def __init__ (self, effect, player, obj):
        SandwichProcess.__init__ (self)
        self.effect = effect
        self.player_id = player.id
        self.obj_id = obj.id

    def pre(self, game):

        from process import SelectTargetsProcess

        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        n = self.effect.number.evaluate(game, obj)

        game.process_push(SelectTargetsProcess(player, obj, self.effect.targetSelector, n, True, True))

    def main(self, game):

        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        targets = game.process_returns_pop()
        if targets is None or len(targets) == 0:
            game.process_returns_push(False)
        else:

            game.process_returns_push(True)

            target_damage_map = {}
            for target_id in targets:
                d = target_damage_map.get(target_id, 0)
                target_damage_map[target_id] = d + 1

            obj.targets = {}
            i = 0
            obj.modal = []
            for target_id, damage in target_damage_map.items():
                target = game.obj(target_id)
                obj.targets[i] = game.create_lki(target)
                obj.modal.append (damage)
                i += 1
                game.raise_event ("target", obj, target)
        

class DealsNDamageDividedAsYouChooseAmongAnyNumberOfTargetX(OneShotEffect):

    def __init__ (self, targetSelector, number):
        self.targetSelector = targetSelector    
        self.number = number

    def resolve(self, game, obj):
        if self._validateTargets(game, obj):

            game.process_returns_push(True)

            targets = obj.targets
            modal = obj.modal

            damage_list = []          
 
            assert len(modal) == len(targets)
            for i, target in targets.items():
                damage = modal[i]

                if not game.lki(target).is_moved():
                    damage_list.append ( (game.create_lki(obj.get_source_lki()), target, damage) )

            game.doDealDamage(damage_list)

        else:
            game.process_returns_push(False)

    def _validateTargets(self, game, obj):
        from process import validate_target

        for target in obj.targets.values():
            if not validate_target(game, obj, self.targetSelector, game.lki(target)):
                return False

        return True

    def validateTargets(self, game, obj):
        game.process_returns_push(self._validateTargets(game, obj))

    def selectTargets(self, game, player, obj):
        game.process_push(DealsNDamageDividedAsYouChooseAmongAnyNumberOfTargetXSelectTargetsProcess(self, player, obj))
    
    def __str__ (self):
        return "DealsNDamageDividedAsYouChooseAmongAnyNumberOfTargetX(%s, %s)" % (self.targetSelector, self.number)

class PreventAllDamageThatWouldBeDealtToXDamagePrevention(DamagePrevention):

    def __init__ (self, obj, effect):
        self.obj = obj
        self.selector = effect.selector

    def canApply(self, game, damage, combat):
        source, dest, n = damage
        return self.selector.contains_lki(game, self.obj, dest)

    def apply(self, game, damage, combat):
        source, dest, n = damage
        return (source, dest, 0)

    def getText(self):
        return "Prevent all damage that would be dealt to " + str(self.selector)

class PreventAllDamageThatWouldBeDealtToX(ContinuousEffect):
    def __init__ (self, selector):
        self.selector = selector

    def apply(self, game, obj):
        game.damage_preventions.append(PreventAllDamageThatWouldBeDealtToXDamagePrevention(obj, self))

class PreventAllDamageThatWouldBeDealtToTargetXThisTurn(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector, True)

    def doResolve(self, game, obj, target):
        game.process_returns_push(True)
        game.until_end_of_turn_effects.append ( (obj, PreventAllDamageThatWouldBeDealtToX(LKISelector(target))))

    def __str__ (self):
        return "PreventAllDamageThatWouldBeDealtToTargetXThisTurn(%s, %s)" % (self.targetSelector)

class PreventAllDamageThatWouldBeDealtThisTurnToUpToNTargetX(MultipleTargetOneShotEffect):
    def __init__ (self, number, selector):
        MultipleTargetOneShotEffect.__init__(self, selector, number, True)

    def doResolve(self, game, obj, targets):
        game.process_returns_push(True)

        for target in targets.values():
            game.until_end_of_turn_effects.append ( (obj, PreventAllDamageThatWouldBeDealtToX(LKISelector(target))))

    def __str__ (self):
        return "PreventAllDamageThatWouldBeDealtThisTurnToUpToNTargetX(%s, %s)" % (self.number, self.targetSelector)

class AfterThisMainPhaseThereIsAnAdditionalCombatPhaseFollowedByAnAdditionalMainPhase(OneShotEffect):
    def __init__ (self):
        pass

    def resolve(self, game, obj):
        game.process_returns_push(True)
        game.additional_combat_phase_followed_by_an_additional_main_phase = True

    def __str__ (self):
        return "AfterThisMainPhaseThereIsAnAdditionalCombatPhaseFollowedByAnAdditionalMainPhase()"


class PutNNCTCreatureTokenWithTOntoTheBattlefieldAtTheBeginningOfTheNextEndStepEventHandler():
    def __init__ (self, controller_id, power, toughness, color, typ, tag):
        self.controller_id = controller_id
        self.power = power
        self.toughness = toughness
        self.color = color
        self.typ = typ
        self.tag = tag
        self.active = True

    def handle(self, SELF_id, game):
        SELF = game.obj(SELF_id)

        if self.active and game.current_step == "end of turn":
            game.create_token(self.controller_id, set(), set(["creature"]), set([self.typ]), set([self.color, self.tag]), "", self.power, self.toughness)
            self.active = False


class PutNNCTCreatureTokenWithTOntoTheBattlefieldAtTheBeginningOfTheNextEndStep(OneShotEffect):
    def __init__(self, power, toughness, color, typ, tag):
        self.power = power
        self.toughness = toughness
        self.color = color
        self.typ = typ
        self.tag = tag

    def resolve(self, game, obj):

        game.process_returns_push(True)

        power = self.power.evaluate(game, obj)
        toughness = self.toughness.evaluate(game, obj)

        handler = PutNNCTCreatureTokenWithTOntoTheBattlefieldAtTheBeginningOfTheNextEndStepEventHandler(obj.get_controller_id(), power, toughness, self.color, self.typ, self.tag)

        game.add_event_handler("step", partial(handler.handle, obj.id))

    def __str__(self):
        return "PutNNCTCreatureTokenWithTOntoTheBattlefieldAtTheBeginningOfTheNextEndStep(%s, %s, %s, %s, %s)" % (self.power, self.toughness, self.color, self.typ, self.tag)

class XCantAttackUnlessDefendingPlayerControlsAY(ContinuousEffect):
    def __init__ (self, x_selector, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector

    def apply(self, game, obj):
        game.add_volatile_event_handler("validate_attacker", partial(self.onCanAttack, obj.id))

    def isSelf(self):
        return isinstance(self.x_selector, SelfSelector)

    def onCanAttack(self, SELF_id, game, av):
        SELF = game.obj(SELF_id)

        if av.can and self.x_selector.contains(game, SELF, av.attacker):
            for o in self.y_selector.all(game, SELF):
                if o.get_controller_id() == game.defending_player_id:
                    return
            av.can = False

    def __str__ (self):
        return "XCantAttackUnlessDefendingPlayerControlsAY(%s, %s)" % (self.x_selector, self.y_selector)

class XCantBlockOrBeBlockerByY(ContinuousEffect):
    def __init__ (self, x_selector, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector

    def apply(self, game, obj):
        game.add_volatile_event_handler("validate_blocker", partial(self.onCanBlock, obj.id))

    def isSelf(self):
        return isinstance(self.x_selector, SelfSelector) or isinstance(self.y_selector, SelfSelector)

    def onCanBlock(self, SELF_id, game, bv):
        SELF = game.obj(SELF_id)

        if bv.can and ((self.x_selector.contains(game, SELF, bv.attacker) and self.y_selector.contains(game, SELF, bv.blocker)) or (self.x_selector.contains(game, SELF, bv.blocker) and self.y_selector.contains(game, SELF, bv.attacker))):
            bv.can = False

    def __str__ (self):
        return "XCantBlockOrBeBlockerByY(%s, %s)" % (self.x_selector, self.y_selector)

class XCantBlockY(ContinuousEffect):
    def __init__ (self, x_selector, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector

    def apply(self, game, obj):
        game.add_volatile_event_handler("validate_blocker", partial(self.onCanBlock, obj.id))

    def isSelf(self):
        return isinstance(self.x_selector, SelfSelector) or isinstance(self.y_selector, SelfSelector)

    def onCanBlock(self, SELF_id, game, bv):
        SELF = game.obj(SELF_id)

        if bv.can and (self.x_selector.contains(game, SELF, bv.blocker) and self.y_selector.contains(game, SELF, bv.attacker)):
            bv.can = False

    def __str__ (self):
        return "XCantBlockY(%s, %s)" % (self.x_selector, self.y_selector)

class XAreChosenColor(ContinuousEffect):
    def __init__ (self, selector):
        self.selector = selector

    def apply(self, game, obj):
        if obj.modal is not None:
            for o in self.selector.all(game, obj):
                if not o.is_moved():
                    o.get_state().tags.add (obj.modal)

    def isSelf(self):
        return isinstance(self.selector, SelfSelector)

    def __str__ (self):
        return "XAreChosenColor(%s)" % (self.selector)

    def getLayer(self):
        return "other"

class XPlayWithHandRevealed(ContinuousEffect):
    def __init__ (self, x_selector):
        self.x_selector = x_selector

    def apply(self, game, obj):

        for player in self.x_selector.all(game, obj):
            hand = game.get_hand(player)
            for card in hand.objects:
                # reveal to all players
                for p in game.players:
                    if p.get_id() not in card.get_state().show_to:
                        card.get_state().show_to.append(p.get_id())

    def __str__ (self):
        return "XPlayWithHandRevealed(%s)" % (self.x_selector)

class ExileAllXStartingWithYouEachPlayerChoosesOneOfTheExiledCardsAndPutsItOntoTheBattlefieldTappedUnderHisOrHerControlRepeatThisProcessUntilAllCardsExiledThisWayHaveBeenChosenProcess:
    def __init__ (self, selector, obj):
        self.obj_id = obj.id
        self.state = 0
        self.selector = selector

    def next(self, game, action):
        from process import PutCardIntoPlayProcess

        obj = game.obj(self.obj_id)
        removed_zone = game.get_removed_zone()

        if self.state == 0:

            self.state = 1
            game.process_push(self)

            self.card_ids = []
            self.player_id = game.obj(obj.get_controller_id()).id

            for card in self.selector.all(game, obj):
                self.card_ids.append (card.id)
                game.doZoneTransfer(card, removed_zone, obj)

        elif self.state == 1:
            if len(self.card_ids) == 0:
                game.process_returns_push(True)
            else:
                player = game.obj(self.player_id)
                if action is None:
                    options = []
                    for card_id in self.card_ids:
                        card = game.obj(card_id)
                        _p = Action ()
                        _p.object_id = card.id
                        _p.text = "Choose " + str(card)
                        options.append (_p)

                    return ActionSet (player.id, "Choose a card to return to the battlefield.", options)

                else:
                    card = game.obj(action.object_id)
                    self.card_id = card.id

                    self.state = 2
                    game.process_push(self)

                    game.process_push(PutCardIntoPlayProcess(card, player, obj, True))

        elif self.state == 2:
            cardPut = game.process_returns_pop()
            # TODO: if card cannot be put into play, other players should get a chance, until all players fail to put this card

            self.card_ids.remove(self.card_id)
            self.player_id = game.get_next_player(game.obj(self.player_id)).id

            self.state = 1
            game.process_push(self)


class ExileAllXStartingWithYouEachPlayerChoosesOneOfTheExiledCardsAndPutsItOntoTheBattlefieldTappedUnderHisOrHerControlRepeatThisProcessUntilAllCardsExiledThisWayHaveBeenChosen(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        game.process_push(ExileAllXStartingWithYouEachPlayerChoosesOneOfTheExiledCardsAndPutsItOntoTheBattlefieldTappedUnderHisOrHerControlRepeatThisProcessUntilAllCardsExiledThisWayHaveBeenChosenProcess(self.selector, obj))

    def __str__ (self):
        return "ExileAllXStartingWithYouEachYChoosesOneOfTheExiledCardsAndPutsItOntoTheBattlefieldTappedUnderHisOrHerControlRepeatThisProcessUntilAllCardsExiledThisWayHaveBeenChosen(%s)" % (self.selector)

class TargetPlayerNamesCardThenRevealsTopCardOfLibraryIfItsTheNamedCardThePlayerPutsItIntoHisHandOtherwiseThePlayerPutsItIntoGraveyardAndXDealsNDamageToHimOrHerProcess:
    def __init__ (self, player, obj, n):
        self.player_id = player.id
        self.obj_id = obj.id
        self.n = n
        self.state = 0

    def next(self, game, action):
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)

        library = game.get_library(player)
        hand = game.get_hand(player)
        graveyard = game.get_graveyard(player)

        if self.state == 0:
            self.state = 1
            return QueryString(player.id, "Name a Card")
        elif self.state == 1:
            self.title = action.lower().strip()

            if len(library.objects) == 0:
                game.doLoseGame(player)
            else:
                top_card = library.objects[-1]
                from process import RevealCardsProcess

                self.state = 2
                game.process_push(self)
                game.process_push(RevealCardsProcess(player, [top_card]))

        elif self.state == 2:
            top_card = library.objects[-1]
            if self.title == top_card.get_state().title.lower():
                game.doZoneTransfer(top_card, hand, obj)
            else:
                count = self.n.evaluate(game, obj)

                damage = []
                damage.append ( (game.create_lki(obj), game.create_lki(player), count) )
                game.doDealDamage(damage)

                game.doZoneTransfer(top_card, graveyard, obj)
                
    

class TargetPlayerNamesCardThenRevealsTopCardOfLibraryIfItsTheNamedCardThePlayerPutsItIntoHisHandOtherwiseThePlayerPutsItIntoGraveyardAndXDealsNDamageToHimOrHer(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, n):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.n = n
           
    def doResolve(self, game, obj, target):

        player = target.get_object()

        game.process_returns_push(True)
        game.process_push(TargetPlayerNamesCardThenRevealsTopCardOfLibraryIfItsTheNamedCardThePlayerPutsItIntoHisHandOtherwiseThePlayerPutsItIntoGraveyardAndXDealsNDamageToHimOrHerProcess(player, obj, self.n))

    def __str__ (self):
        return "TargetPlayerNamesCardThenRevealsTopCardOfLibraryIfItsTheNamedCardThePlayerPutsItIntoHisHandOtherwiseThePlayerPutsItIntoGraveyardAndXDealsNDamageToHimOrHer(%s, %s)" % (self.targetSelector, self.n)

class IfAPlayerWouldDrawACardHeOrSheRevealsItInsteadThenAnyOtherPlayerMayPayCIfAPlayerDoesPutThatCardIntoItsOwnersGraveyardOtherwiseThatPlayerDrawsACardProcess:
    def __init__ (self, interceptable, player, SELF, cost):
        self.interceptable = interceptable
        self.player_id = player.id
        self.next_player_id = None
        self.SELF_id = SELF.id
        self.cost = cost

        self.state = 0

    def next(self, game, action):
        player = game.obj(self.player_id)

        if self.next_player_id is None:
            self.next_player_id = game.get_next_player(player).id

        next_player = game.obj(self.next_player_id)

        SELF = game.obj(self.SELF_id)
        library = game.get_library(player)
        hand = game.get_hand(player)
        graveyard = game.get_graveyard(player)

        top_card = library.objects[-1]

        if self.state == 0:
            if self.next_player_id != self.player_id:
                if action is None:
                    _pay = Action()
                    _pay.text = "Yes"
        
                    _notpay = Action()
                    _notpay.text = "No"

                    return ActionSet (next_player.id, ("Pay %s to put %s into its owner's graveyard?" % (", ".join(map(str, self.cost)), top_card.get_state().title)), [_pay, _notpay])
                else:
                    if action.text == "Yes":
                        self.state = 1
                        game.process_push(self)

                        from process import PayCostProcess
                        game.process_push(PayCostProcess(next_player, SELF, SELF, self.cost))

                    else:
                        self.next_player_id = game.get_next_player(next_player).id
                        game.process_push(self)

            else:
                self.interceptable.proceed(game, player)

        elif self.state == 1:
            # payed cost?
            if game.process_returns_pop():
                # move the card to graveyard and end
                self.interceptable.cancel()
                game.doZoneTransfer(top_card, graveyard, SELF)
            else:
                self.state = 0
                self.next_player_id = game.get_next_player(next_player).id
                game.process_push(self)



class IfAPlayerWouldDrawACardHeOrSheRevealsItInsteadThenAnyOtherPlayerMayPayCIfAPlayerDoesPutThatCardIntoItsOwnersGraveyardOtherwiseThatPlayerDrawsACard(ContinuousEffect):
    def __init__ (self, x_selector, cost):
        self.x_selector = x_selector
        self.cost = cost

    def apply(self, game, obj):
        game.interceptable_draw.add(partial(self.interceptDraw, obj.id))

    def interceptDraw(self, SELF_id, interceptable, game, player):
        SELF = game.obj(SELF_id)
        from process import RevealCardsProcess

        if self.x_selector.contains(game, SELF, player):
            library = game.get_library(player)
            hand = game.get_hand(player)
            graveyard = game.get_graveyard(player)

            if len(library.objects) == 0:
                self.doLoseGame(player)
            else:
                top_card = library.objects[-1]

                game.process_push(IfAPlayerWouldDrawACardHeOrSheRevealsItInsteadThenAnyOtherPlayerMayPayCIfAPlayerDoesPutThatCardIntoItsOwnersGraveyardOtherwiseThatPlayerDrawsACardProcess(interceptable, player, SELF, self.cost))
                game.process_push(RevealCardsProcess(player, [top_card]))

        else:
            return interceptable.proceed(game, player)
             

    def isSelf(self):
        return False

    def __str__ (self):
        return "IfAPlayerWouldDrawACardHeOrSheRevealsItInsteadThenAnyOtherPlayerMayPayCIfAPlayerDoesPutThatCardIntoItsOwnersGraveyardOtherwiseThatPlayerDrawsACard(%s, %s)" % (self.x_selector, self.cost)

