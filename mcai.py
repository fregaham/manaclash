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

from actions import ActionSet, QueryNumber, QueryString, Action

import ai

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
    p1 = g.create_player("Player1", c1)

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
    p2 = g.create_player("Player2", c2)

    g.process_push(MainGameProcess())

    _as = g.next(None) 
#    root = ai.TreeNode(g, None, None, actions, 0)

#    ai.expand_to_depth(root, 7)

#    print root.leaves_count()

#    score = root.score(ai.default_scoring_fn, p1.id)
#    print "score: %f" % (score)

#    input_generator(g)
    # process_game(g)

    game = g

    while True:

        player = game.obj(_as.player_id)

        print ("player %s: %s" % (player.name, _as.text))
        print ("turn %s, phase: %s, step: %s" % (game.get_active_player().name, game.current_phase, game.current_step))
        print ("battlefield: \n%s" % ("\n".join(map(lambda x:str(x), game.get_in_play_zone().objects))))
        print ("stack: %s" % (" ".join(map(lambda x:"["+str(x)+"]",game.get_stack_zone().objects))))
        print ("library: %d graveyard: %d" % (len(game.get_library(player).objects), len(game.get_graveyard(player).objects) ))
#        print ("hand: %s" % (" ".join(map(lambda x:"["+str(x)+"]",game.get_hand(player).objects))))
        print ("manapool: %s" % (player.manapool))
        print ("life: %d" % (player.life))

        if game.end:
            break

        if isinstance(_as, ActionSet):

            if len(_as.actions) == 0:
                break

#            i = 0
#            for a in _as.actions:
#                print ("%d: %s"  % (i, a.text))
#                i += 1
        elif isinstance(_as, QueryNumber):
            print("Enter number: ")
        elif isinstance(_as, QueryString):
            print("Enter answer: ")

        print

        if isinstance(_as, ActionSet)and len(_as.actions) == 1:
            action = _as.actions[0]
        else:    

            hand1 = len(game.get_hand(game.obj(p1.id)).objects)
            hand2 = len(game.get_hand(game.obj(p2.id)).objects)

            action = ai.choose_action(game, _as, 7)

            hand1_ = len(game.get_hand(game.obj(p1.id)).objects)
            hand2_ = len(game.get_hand(game.obj(p2.id)).objects)

            assert hand1 == hand1_
            assert hand2 == hand2_

        print 
        print action.text if isinstance(action, Action) else `action`
        print

        _as = game.next(action)


