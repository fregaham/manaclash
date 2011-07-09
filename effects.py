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

class Effect:
    def setText(self):
        self.text = text

    def getText(self):
        return self.text

    def getSlots(self):
        return []

class ContinuousEffect(Effect):
    def __init__ (self, types):
        self.types = types
        self.timestamp = None

    def apply (self):
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
        for player in self.selector.all(game, obj):
            game.doLoseLife(player, self.count)

class PlayerGainLifeEffect(OneShotEffect):
    def __init__ (self, playerSelector, count):
        self.selector = playerSelector
        self.count = count

    def resolve(self, game, obj):
        for player in self.selector.all(game, obj):
            game.doGainLife(player, self.count)

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


class XDealNDamageToTargetYEffect(OneShotEffect):
    def __init__ (self, sourceSelector, count, targetSelector):
        self.sourceSelector = sourceSelector
        self.count = count
        self.targetSelector = targetSelector

    def resolve(self, game, obj):
        if self.validateTargets(game, obj):
            target = obj.targets["target"]
            
            sources = [x for x in self.sourceSelector.all(game, obj)]
            assert len(sources) == 1

            source = sources[0]

            game.doDealDamage([(source, target, self.count)])

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


