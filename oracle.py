# -*- coding: utf-8 -*-

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


from ManaClash import *
from game import *
from process import *
from rules import *
from mcio import *

import sys

class Card:
    def __init__ (self):
        self.name = None
        self.cost = None
        self.supertypes = set()
        self.subtypes = set()
        self.types = set()
        self.power = None
        self.toughness = None
        self.rules = None
        self.sets = set()

def parseOracle(f):
    n = 0
    state = 0
    card = Card()
    rules = ""

    for line in f:
        #line = line.decode("utf8")
        n += 1
        if state == 0:
            if line.startswith("Name:"):
                card.name = line[len("Name:"):].strip()
                state = 1
            elif line.strip() == "":
                pass
            else:
                raise Exception("Expecting 'Name:' on line %d" % n)
        elif state == 1:
            if line.startswith("Cost:"):
                card.cost = line[len("Cost:"):].strip()
                state = 2
            else:
                raise Exception("Expecting 'Cost:' on line %d" % n)
        elif state == 2:
            if line.startswith("Type:"):
                types = line[len("Type:"):].strip().lower()
                if "—" in types:
                    types, subtypes = types.split("—", 1)
                    typesSplit = types.split()
                    if len(typesSplit) == 1:
                        card.types = set([typesSplit[0]])
                    elif len(typesSplit) == 2:
                        card.supertypes = set([typesSplit[0]])
                        card.types = set([typesSplit[1]])
                    card.subtypes = set(subtypes.split())
                else:
                    card.types = set(types.split())
                
                state = 3
            else:
                raise Exception("Expecting 'Type:' on line %d" % n)
        elif state == 3:
            if line.startswith("Pow/Tgh:"):
                pt = line[len("Pow/Tgh:"):].strip()
                if pt == "":
                    card.power = None
                    card.toughness = None
                else:
                    if pt[0] != "(":
                        raise Exception("Expecting '(' on line %d" % n)
                    if pt[-1] != ")":
                        raise Exception("Expecting ')' on line %d" % n)
                    power, toughness = pt[1:-1].split("/")
                    card.power = power
                    card.toughness = toughness

                state = 4
            else:
                raise Exception("Expecting 'Pow/Tgh:' on line %d" % n)
        elif state == 4:
            if line.startswith("Rules Text:"):
                rules = line[len("Rules Text:"):].strip()
                state = 5
            else:
                raise Exception("Expecting 'Rules Text:' on line %d" % n) 

        elif state == 5:
            if line.startswith("Set/Rarity:"):
                card.rules = rules

                sets = line[len("Set/Rarity:"):]
                card.sets = set(map(lambda x:x.strip(), sets.split(",")))

                state = 6
            else:
                rules += "\n" + line.strip()
            
        elif state == 6:
            if line.strip() == "":
                state = 0
                yield card
                card = Card()
            else:
                card.sets = card.sets.union(set(map(lambda x:x.strip(), line.split(","))))

def getParseableCards(f):
    ig = test_input_generator([])
    n = ig.next()
    o = NullOutput()
    g = Game(ig, o)
    g.create()

    for card in parseOracle(f):
        if (isParseable(g, card)):
            yield card

def isParseable(game, card):

    r = card.rules.replace(card.name, "<<self>>").lower().replace("<<self>>", "SELF").replace("\n", ";").replace("—", "-")

    obj = game.create_card(card.name, card.cost, card.supertypes, card.types, card.subtypes, set(), r, card.power, card.toughness)
    obj.state = obj.initial_state.copy()

    try:
        rules = parse(obj)
        if rules is not None:
            return True
    except:
        pass

    return False

def createCardObject(game, card):
    r = card.rules.replace(card.name, "<<self>>").lower().replace("<<self>>", "SELF").replace("\n", ";").replace("—", "-")

    power = card.power
    toughness = card.toughness

    if power != None:
        if power == "*":
            power = 0
        else:
            power = int(power)

    if toughness != None:
        if toughness == "*":
            toughness = 0
        else:
            toughness = int(toughness)

    obj = game.create_card(card.name, card.cost, card.supertypes, card.types, card.subtypes, set(), r, power, toughness)

    return obj

if __name__ == "__main__":
    ig = test_input_generator([])
    n = ig.next()
    o = NullOutput()
    g = Game(ig, o)
    g.create()

    parsed = 0
    total = 0

    for card in parseOracle(sys.stdin):

        # create_card (u"Hasty Moggie Bird", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying",u"haste"]), "when SELF comes into play, each player loses 1 life.", 1, 1)
        r = card.rules.replace(card.name, "<<self>>").lower().replace("<<self>>", "SELF").replace("\n", ";").replace("—", "-")
        obj = g.create_card(card.name, card.cost, card.supertypes, card.types, card.subtypes, set(), r, card.power, card.toughness)
        obj.state = obj.initial_state.copy()

        #print obj.state.title

        total += 1

        try:
            rules = parse(obj)
            if rules is not None:
                print(obj.state.title)
                print(obj.state.text)
                print(rules)

                parsed += 1
        except Exception as x:
            print (repr(x))
            print (("Cannot parse %s\n%s" % (obj.state.title, obj.state.text)).encode("utf8"))

    print ("Parsed %d/%d" % (parsed, total))

