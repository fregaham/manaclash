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

from objects import  *
from selectors import *

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

class OneShotEffect(Effect):
    def resolve(self, game, obj):
        pass

    def selectTargets(self, game, player, obj):
        return True

    def validateTargets(self, game, obj):
        return True

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

    def __str__ (self):
        return "PlayerLooseLifeEffect(%s, %s)" % (str(self.selector), str(self.count))

class PlayerGainLifeEffect(OneShotEffect):
    def __init__ (self, playerSelector, count):
        self.selector = playerSelector
        self.count = count
    def resolve(self, game, obj):
        if self.count == "X":
            count = obj.x
        else:
            count = self.count

        for player in self.selector.all(game, obj):
            game.doGainLife(player, count)

    def __str__ (self):
        return "PlayerGainLifeEffect(%s, %s)" % (self.selector, self.count)

class PlayerGainLifeForEachXEffect(OneShotEffect):
    def __init__ (self, playerSelector, count, eachSelector):
        self.selector = playerSelector
        self.count = count
        self.eachSelector = eachSelector

    def resolve(self, game, obj):
        if self.count == "X":
            count = obj.x
        else:
            count = self.count

        for player in self.selector.all(game, obj):
            eachcount = len([x for x in self.eachSelector.all(game, obj)])
            game.doGainLife(player, count * eachcount)

    def __str__ (self):
        return "PlayerGainLifeForEachXEffect(%s, %s, %s)" % (self.selector, self.count, self.eachSelector)

class PlayerDiscardsCardEffect(OneShotEffect):
    def __init__ (self, playerSelector, count):
        self.selector = playerSelector
        self.count = count

    def resolve(self, game, obj):
        for player in self.selector.all(game, obj):
            assert player is not None
            for i in range(self.count):
                from process import process_discard_a_card
                process_discard_a_card(game, player)

    def __str__ (self):
        return "PlayerDiscardsCardEffect(%s, %s)" % (self.selector, self.count)

class SingleTargetOneShotEffect(OneShotEffect):

    def __init__ (self, targetSelector):
        self.targetSelector = targetSelector    

    def resolve(self, game, obj):
        if self.validateTargets(game, obj):
            target = obj.targets["target"]
            self.doResolve(game, obj, target)

    def validateTargets(self, game, obj):
        from process import process_validate_target
        return process_validate_target(game, obj, self.targetSelector, obj.targets["target"])

    def selectTargets(self, game, player, obj):
        from process import process_select_target
        target = process_select_target(game, player, obj, self.targetSelector)        
        if target == None:
            return False

        obj.targets["target"] = LastKnownInformation(game, target)

        return True

    def doResolve(self, game, obj, target):
        pass

    def __str__ (self):
        return "SingleTargetOneShotEffect(%s)" % self.targetSelector

class XDealNDamageToTargetYEffect(SingleTargetOneShotEffect):
    def __init__ (self, sourceSelector, count, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.sourceSelector = sourceSelector
        self.count = count
           
    def doResolve(self, game, obj, target): 
        sources = [x for x in self.sourceSelector.all(game, obj)]
        assert len(sources) == 1

        source = sources[0]

        count = 0
        if self.count == "X":
            assert obj.x is not None
            count = obj.x
        else:
            count = int(self.count)

        game.doDealDamage([(source, target, count)])

    def __str__ (self):
        return "XDealNDamageToTargetYEffect(%s, %s, %s)" % (self.targetSelector, self.count, self.sourceSelector)

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
            o.state.power += power
            o.state.toughness += toughness

    def __str__ (self):
        return "XGetsNN(%s, %s, %s)" % (self.selector, self.power, self.toughness)

class TargetXGetsNNUntilEndOfTurn(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, power, toughness):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.power = power
        self.toughness = toughness

    def doResolve(self, game, obj, target):
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
        
        game.until_end_of_turn_effects.append ( (obj, XGetsNN(LKISelector(target), power, toughness)))

    def __str__ (self):
        return "TargetXGetsNNUntilEndOfTurn(%s, %s, %s)" % (self.targetSelector, self.power, self.toughness)

class DestroyTargetX(SingleTargetOneShotEffect):
    def __init__(self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.doDestroy(target)

    def __str__ (self):
        return "DestroyTargetX(%s)" % self.targetSelector

class BuryTargetX(SingleTargetOneShotEffect):
    def __init__(self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.doBury(target)

    def __str__ (self):
        return "BuryTargetX(%s)" % self.targetSelector
       
class DestroyTargetXYGainLifeEqualsToItsPower(SingleTargetOneShotEffect):
    def __init__(self, targetSelector, playerSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.playerSelector = playerSelector

    def doResolve(self, game, obj, target):
        game.doDestroy(target)

        count = target.get_state().power
        for player in self.playerSelector.all(game, obj):
            game.doGainLife(player, count)

    def __str__ (self):
        return "DestroyTargetXYGainLifeEqualsToItsPower(%s, %s)" % (self.targetSelector, self.playerSelector)

class DoXAtEndOfCombat(OneShotEffect):
    def __init__ (self, effect):
        self.effect = effect

    def resolve(self, game, obj):
        e = game.create_effect_object(obj.get_source_lki(), obj.get_controller_id(), self.effect, obj.get_slots())
        game.end_of_combat_triggers.append (e)

    def __str__ (self):
        return "DoXAtEndOfCombat(%s)" % self.effect

class DestroyX(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        for o in self.selector.all(game, obj):
            game.doDestroy(o)

    def __str__ (self):
        return "DestroyX(%s)" % self.selector

class XDontUntapDuringItsControllersUntapStep(ContinuousEffect):
    def __init__ (self, selector):
        self.selector = selector

    def apply(self, game, obj):
        for o in self.selector.all(game, obj):
            o.state.tags.add ("does not untap")

    def __str__ (self):
        return "XDontUntapDuringItsControllersUntapStep(%s)" % self.selector


