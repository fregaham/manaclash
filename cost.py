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

from actions import *

class Cost:
    def __init__ (self):
        pass

    def get_text(self, game, obj, player):
        return "Pay Cost"

    def pay(self, game, obj, effect, player):
        game.process_returns_push(False)

    def canPay(self, game, obj, player):
        return True

    def __str__ (self):
        return "Cost"

def mana_parse(m):
    cs = "WGRUB"
    ret = {}

    ret[None] = 0
    for c in cs:
        ret[c] = 0

    for c in m:
        if c in cs:
            ret[c] = ret[c] + 1
        elif c in "0123456789":
            ret[None] = ret[None] + int(c)

    return ret


def mana_converted_cost(m):
    cs = "WGRUB"
    ret = 0
    for c in m:
        if c in cs:
            ret += 1
        elif c in "0123456789":
            ret += int(c)
    return ret

def mana_format(mp):
    cs = "WGRUB"
    ret = ""

    for c in cs:
        ret += c * mp[c]

    colorless = mp[None]
    while colorless > 9:
        ret += "9"
        colorless -= 9

    ret += str(colorless)

    if ret == "0":
        ret = ""

    return ret

def mana_greater_than(m1, m2):
    mp1 = mana_parse(m1)
    mp2 = mana_parse(m2)

    excess = 0
    for c in "WGRUB":
        if mp1[c] >= mp2[c]:
            excess += mp1[c] - mp2[c]
        else:
            return False

    return excess + mp1[None] >= mp2[None]


def mana_diff (m1, m2):
    mp1 = mana_parse(m1)
    mp2 = mana_parse(m2)

    ret = {}

    excess = 0
    for c in "WGRUB":
        ret[c] = mp1[c] - mp2[c]

    if mp1[None] >= mp2[None]:
        ret[None] = mp1[None] - mp2[None]
    else:
        ret[None] = 0
        x = mp2[None] - mp1[None]
        for c in "WGRUB":
            if ret[c] >= x:
                ret[c] -= x
                x = 0
            else:
                x -= ret[c]
                ret[c] = 0

        assert x == 0

    return mana_format(ret)

class ManaCost(Cost):
    def __init__ (self, manacost):
        Cost.__init__(self)
        self.manacost = manacost

    def get_text(self, game, obj, player):
        return "Pay " + self.manacost

    def pay(self, game, obj, effect, player):
        print("paying cost, manapool: %s, manacost: %s" % (player.manapool, self.manacost))
        player.manapool = mana_diff (player.manapool, self.manacost)
        print("after payed: manapool: %s" % (player.manapool))
        game.process_returns_push(True)

    def canPay(self, game, obj, player):
        return mana_greater_than(player.manapool, self.manacost)

    def __str__ (self):
        return self.manacost

class TapCost(Cost):
    def __init__ (self, obj_id):
        Cost.__init__(self)

    def __str__ (self):
        return "T"

class TapSelectorCostProcess:
    def __init__ (self, selector, obj, player):
        self.selector = selector
        self.obj_id = obj.id
        self.player_id = player.id

    def next(self, game, action):

        obj = game.obj(self.obj_id)
        player = game.obj(self.player_id)

        if action is None:
            actions = []
            for o in self.selector.all(game, obj):

                if o.tapped:
                    continue

                _p = Action ()
                _p.object = o
                _p.text = "Tap %s" % str(o)
                actions.append (_p)

            if len(actions) > 0:
                return ActionSet (game, player, "Choose %s to tap" % self.selector, actions)
            else:
                game.process_returns_push(False)
        else:
            game.doTap(action.object)
            game.process_returns_push(True)
        

class TapSelectorCost(Cost):
    def __init__ (self, selector):
        Cost.__init__ (self)
        self.selector = selector

    def get_text(self, game, obj, player):
        return "Tap %s" % self.selector

    def pay(self, game, obj, effect, player):
        game.process_push(TapSelectorCostProcess(self.selector, obj, player))

    def canPay(self, game, obj, player):
        os = [x for x in self.selector.all(game, obj)]
        return len(os) > 0

    def __str__ (self):
        return "tap %s" % self.selector

class SacrificeSelectorCostProcess:
    def __init__ (self, selector, obj, effect, player):
        self.selector = selector
        self.obj_id = obj.id
        self.effect_id = effect.id
        self.player_id = player.id

    def next(self, game, action):

        obj = game.obj(self.obj_id)
        player = game.obj(self.player_id)
        effect = game.obj(self.effect_id)

        if action is None:
            actions = []
            for o in self.selector.all(game, obj):
                if o.get_controller_id() != player.get_id():
                    continue

                _p = Action ()
                _p.object = o
                _p.text = "Sacrifice %s" % str(o)
                actions.append (_p)

            if len(actions) > 0:
                return ActionSet (game, player, "Choose %s to sacrifice" % self.selector, actions)
            else:
                game.process_returns_push(False)
        else:
            effect.slots["sacrificed"] = game.create_lki(action.object)
            game.doSacrifice(action.object)
            game.process_returns_push(True)

class SacrificeSelectorCost(Cost):
    def __init__ (self, selector):
        Cost.__init__ (self)
        self.selector = selector

    def get_text(self, game, obj, player):
        return "Sacrifice %s" % self.selector

    def pay(self, game, obj, effect, player):
        game.process_push(SacrificeSelectorCostProcess(self.selector, obj, effect, player))

    def __str__ (self):
        return "sacrifice %s" % self.selector

class DiscardXProcess:
    def __init__ (self, selector, obj, effect, player):
        self.selector = selector
        self.obj_id = obj.id
        self.effect_id = effect.id
        self.player_id = player.id

    def next(self, game, action):

        obj = game.obj(self.obj_id)
        player = game.obj(self.player_id)
        effect = game.obj(self.effect_id)

        if action is None:
            actions = []

            hand = game.get_hand(player)
            for o in hand.objects:
                if self.selector.contains(game, obj, o):
                    _p = Action ()
                    _p.object = o
                    _p.text = "Discard %s" % str(o)
                    actions.append (_p)

            if len(actions) > 0:
                return ActionSet (game, player, "Discard %s" % self.selector, actions)
            else:
                game.process_returns_push(False)
        else:
            game.doDiscard(player, action.object, obj)
            game.process_returns_push(True)

class DiscardX(Cost):
    def __init__ (self, selector):
        Cost.__init__(self)
        self.selector = selector

    def get_text(self, game, obj, player):
        return "Discard " + str(self.selector)

    def pay(self, game, obj, effect, player):
        game.process_push(DiscardXProcess(self.selector, obj, effect, player))

    def __str__ (self):
        return "discard " + str(self.selector)

class PayLifeCost(Cost):
    def __init__ (self, n):
        Cost.__init__ (self)
        self.n = n

    def get_text(self, game, obj, player):
        return "Pay %d life" % self.n

    def pay(self, game, obj, effect, player):
        game.process_returns_push(True)
        game.doPayLife(player, self.n)

    def __str__ (self):
        return "pay %d life" % self.n

class PayHalfLifeRoundedUpCost(Cost):
    def __init__ (self):
        Cost.__init__ (self)

    def get_text(self, game, obj, player):
        return "Pay half your life rounded up"

    def pay(self, game, obj, effect, player):
        game.process_returns_push(True)
        if (player.life % 2) == 0:
            n = player.life / 2
        else:
            n = (player.life + 1) / 2

        game.doPayLife(player, n)

    def __str__ (self):
        return "pay half your life rounded up"

