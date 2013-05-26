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

import os
import sys
import random

from mcio import Output, input_generator
from game import Game
from process import MainGameProcess
from oracle import getParseableCards, createCardObject, parseOracle

def parse_deckfile(deckfile):
    f = open(deckfile, 'r')

    for line in f:
        line = line.decode("utf8").rstrip()
        n, name = line.split(None, 1)

        yield (int(n), name)

    f.close()

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print ("Usage:\n\n%s [DECKFILE1] [DECKFILE2]" % sys.argv[0])
        sys.exit(1)
    

    # read the oracle
    cards = {}
    for fname in os.listdir("oracle"):
        print ("reading %s " % fname)
        oracleFile = open(os.path.join("oracle", fname), "r")
        for card in parseOracle(oracleFile):
            print card.name
            cards[card.name] = card

        oracleFile.close()

    output = Output()
    g = Game(output)
    g.create()

#    ig = input_generator(g)

    c1 = []
    for count, name in parse_deckfile(sys.argv[1]):
        for i in range(count):
            card = cards.get(name)
            if card is not None:
                cardObject = createCardObject(g, card)
                c1.append(cardObject)
            else:
                print ("Card %s doesn't exist!" % name)

    random.shuffle(c1)
    g.create_player("Player1", c1)

    c2 = []
    for count, name in parse_deckfile(sys.argv[2]):
        for i in range(count):
            card = cards.get(name)
            if card is not None:
                cardObject = createCardObject(g, card)
                c2.append(cardObject)
            else:
                print ("Card %s doesn't exist!" % name)

    random.shuffle(c2)
    g.create_player("Player2", c2)

    g.process_push(MainGameProcess())

    input_generator(g)
    # process_game(g)


