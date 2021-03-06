# Copyright 2012 Marek Schmidt
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

from objects import *

class NumberOf:
    def evaluate (self, game, context):
        return 0
    
    def __str__(self):
        return "number"

class SelectorsPower(NumberOf):
    def __init__ (self, selector):
        self.selector = selector

    def evaluate(self, game, context):
        obj = self.selector.only(game, context)
        return obj.get_state().power

    def __str__ (self):
        return "SelectorsPower(%s)" % (self.selector)

class EachSelectorNumber(NumberOf):
    def __init__ (self, selector):
        self.selector = selector

    def evaluate(self, game, context):
        ret = [x for x in self.selector.all(game, context)]
        return len(ret)

    def __str__ (self):
        return "EachSelector(%s)" % (self.selector)

class XNumber(NumberOf):

    def evaluate(self, game, context):
        return context.x

    def __str__ (self):
        return "XNumber()"

class NNumber(NumberOf):
    def __init__ (self, n):
        self.n = n

    def evaluate(self, game, context):
        count = 0
        if self.n == "X":
            assert context.x is not None
            count = context.x
        else:
            count = int(self.n)

        return count

    def __str__ (self):
        return "NNumber(%s)" % self.n

class NumberOfCardsInYourHand(NumberOf):
    def evaluate(self, game, context):
        player = game.objects[context.get_controller_id()]
        return len(game.get_hand(player).objects)

    def __str__ (self):
        return "number of cards in your hand"

class NumberOfCardsInTargetPlayersHand(NumberOf):
    def evaluate(self, game, context):
        player = context.get_targets()["target"].get_object()
        return len(game.get_hand(player).objects)

    def __str__ (self):
        return "number of cards in target player's hand"

class NumberOfCreatureCardsInAllGraveyards(NumberOf):

    def __init__ (self):
        from selectors import CreatureCardFromAnyGraveyardSelector
        self.n = EachSelectorNumber(CreatureCardFromAnyGraveyardSelector())

    def evaluate(self, game, context):
        return self.n.evaluate(game, context)

    def __str__ (self):
        return "number of creature cards in all graveyards"

class NumberSum(NumberOf):
    def __init__ (self, x, y):
        self.x = x
        self.y = y

    def evaluate(self, game, context):
        return self.x.evaluate(game, context) + self.y.evaluate(game, context)

    def __str__ (self):
        return "%s plus %s" % (self.x, self.y)

class ThatMuchNumber(NumberOf):
    def evaluate(self, game, context):
        return context.slots["that much"]

    def __str__ (self):
        return "that much"


