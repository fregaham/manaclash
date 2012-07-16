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
from objects import LastKnownInformation

class Cost:
    def __init__ (self):
        pass

    def get_text(self, game, obj, player):
        return "Pay Cost"

    def pay(self, game, obj, effect, player):
        return False

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
        return True

    def canPay(self, game, obj, player):
        return mana_greater_than(player.manapool, self.manacost)

    def __str__ (self):
        return self.manacost

class TapCost(Cost):
    def __init__ (self, obj_id):
        Cost.__init__(self)

    def __str__ (self):
        return "T"

class TapSelectorCost(Cost):
    def __init__ (self, selector):
        Cost.__init__ (self)
        self.selector = selector

    def get_text(self, game, obj, player):
        return "Tap %s" % self.selector

    def pay(self, game, obj, effect, player):
        actions = []
        for o in self.selector.all(game, obj):

            if o.tapped:
                continue

            _p = Action ()
            _p.object = o
            _p.text = "Tap %s" % str(o)
            actions.append (_p)

        if len(actions) > 0:
            _as = ActionSet (game, player, "Choose %s to tap" % self.selector, actions)
            a = game.input.send (_as)

            game.doTap(a.object)

            return True
        else:
            return False

    def canPay(self, game, obj, player):
        os = [x for x in self.selector.all(game, obj)]
        return len(os) > 0

    def __str__ (self):
        return "tap %s" % self.selector


class SacrificeSelectorCost(Cost):
    def __init__ (self, selector):
        Cost.__init__ (self)
        self.selector = selector

    def get_text(self, game, obj, player):
        return "Sacrifice %s" % self.selector

    def pay(self, game, obj, effect, player):
        actions = []
        for o in self.selector.all(game, obj):

            # we can't sacrifice something we don't control
            if o.get_controller_id() != player.get_id():
                continue

            _p = Action ()
            _p.object = o
            _p.text = "Sacrifice %s" % str(o)
            actions.append (_p)

        if len(actions) > 0:
            _as = ActionSet (game, player, "Choose %s to sacrifice" % self.selector, actions)
            a = game.input.send (_as)

            effect.slots["sacrificed"] = LastKnownInformation(game, a.object)

            game.doSacrifice(a.object)

            return True
        else:
            return False

    def __str__ (self):
        return "sacrifice %s" % self.selector

