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
    def apply (self, game):
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

class XGetsNN(ContinuousEffect):
    def __init__ (self, source, selector, power, toughness):
        self.source = source
        self.selector = selector
        self.power = power
        self.toughness = toughness

    def apply(self, game):
        for obj in self.selector.all(game, self.source):
            obj.state.power += self.power
            obj.state.toughness += self.toughness

class TargetXGetsNNUntilEndOfTurn(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, power, toughness):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.power = power
        self.toughness = toughness

    def doResolve(self, game, obj, target):
        if self.power == "+X":
            self.power = obj.x
        elif self.power == "-X":
            self.power = - obj.x
        if self.toughness == "+X":
            self.toughness = obj.x
        elif self.toughness == "-X":
            self.toughness = - obj.x
        
        game.until_end_of_turn_effects.append (XGetsNN(obj, LKISelector(target), self.power, self.toughness))

class DestroyTargetX(SingleTargetOneShotEffect):
    def __init__(self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.doDestroy(target)

class BuryTargetX(SingleTargetOneShotEffect):
    def __init__(self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.doBury(target)
       
class DestroyTargetXYGainLifeEqualsToItsPower(SingleTargetOneShotEffect):
    def __init__(self, targetSelector, playerSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.playerSelector = playerSelector

    def doResolve(self, game, obj, target):
        game.doDestroy(target)

        count = target.get_state().power
        for player in self.playerSelector.all(game, obj):
            game.doGainLife(player, count)


