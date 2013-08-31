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

from mcio import Output, input_generator
from game import Game
from process import GameTurnProcess, TurnProcess, MainPhaseProcess, evaluate
from oracle import getParseableCards, createCardObject, parseOracle
from abilities import PlayLandAbility, PlaySpell
from actions import AbilityAction, PassAction

import unittest

# read the oracle
cards = {}
for fname in os.listdir("oracle"):
    print ("reading %s " % fname)
    oracleFile = open(os.path.join("oracle", fname), "r")
    for card in parseOracle(oracleFile):
        print card.name
        cards[card.name] = card

    oracleFile.close()

def createCard(g, name):
    return createCardObject(g, cards[name])

def createCardToHand(g, name, player):
    cardObject = createCard(g, name)
    zone = g.get_hand(player)
    cardObject.zone_id = zone.id
    cardObject.owner_id = player.id
    cardObject.controller_id = player.id
    zone.objects.append (cardObject)

def createGameInMainPhase(cards1, cards2):

    output = Output()
    g = Game(output)
    g.create()

    library1 = []
    for i in range(10):
        cardObject = createCard(g, "Plains")
        library1.append(cardObject)

    library2 = []
    for i in range(10):
        cardObject = createCard(g, "Plains")
        library2.append(cardObject)


    player1 = g.create_player("Player1", library1)
    player2 = g.create_player("Player2", library2)

    for c in cards1:
        createCardToHand(g, c, player1)
        
    for c in cards2:
        createCardToHand(g, c, player2)

    g.process_push(GameTurnProcess())
    turnProcess = TurnProcess(player1)
    turnProcess.state = 1
    g.active_player_id = player1.id
    g.process_push(turnProcess)
    g.process_push(MainPhaseProcess("precombat main"))

    evaluate(g)

    return g

def _pass(g, ax):
    printState(g, ax)
    for a in ax.actions:
        if isinstance(a, PassAction):
            return g.next(a)

    assert False    

def playSpell(g, ax, name):
    printState(g, ax)
    for a in ax.actions:
        if isinstance(a, AbilityAction):
            if isinstance(a.ability, PlaySpell):
                if a.object.get_state().title == name:
                    return g.next(a)

    assert False

def playLand(g, ax, name):
    printState(g, ax)
    for a in ax.actions:
        if isinstance(a, AbilityAction):
            if isinstance(a.ability, PlayLandAbility):
                if a.object.get_state().title == name:
                    return g.next(a)

    assert False


def printState(g, a):
    print ("player %s: %s" % (a.player.name, a.text))
    print ("turn %s, phase: %s, step: %s" % (a.game.get_active_player().name, a.game.current_phase, a.game.current_step))
    print ("battlefield: %s" % (" ".join(map(lambda x:str(x),a.game.get_in_play_zone().objects))))
    print ("stack: %s" % (" ".join(map(lambda x:"["+str(x)+"]",a.game.get_stack_zone().objects))))
    print ("library: %d graveyard: %d" % (len(a.game.get_library(a.player).objects), len(a.game.get_graveyard(a.player).objects) ))
    print ("hand: %s" % (" ".join(map(lambda x:"["+str(x)+"]",a.game.get_hand(a.player).objects))))
    print ("manapool: %s" % (a.player.manapool))
    print ("life: %d" % (a.player.life))

    for _ in a.actions:
        print `_` + " " + _.text

def endOfTurn(g, ax):
    turn_id = g.get_active_player().id
    while g.get_active_player().id == turn_id:
        ax = _pass(g, ax)

    return ax

def precombatMainPhase(g, ax):
    turn_id = g.get_active_player().id
    while g.current_phase != "precombat main" or ax.text != "You have priority":
        ax = _pass(g, ax)

    return ax

def postcombatMainPhase(g, ax):
    turn_id = g.get_active_player().id
    while g.current_phase != "postcombat main" or ax.text != "You have priority":
        ax = _pass(g, ax)

    return ax

def declareAttackersStep(g, ax):
    while g.current_phase != "combat" or g.current_step != "declare attackers":
        ax = _pass(g, ax)
    return ax

def declareAttackers(g, ax, lst):
    for attacker in lst:
        assert ax.text == "Select attackers"
        for a in ax.actions:
            if a.object != None and a.object.get_state().title == attacker:
                ax = g.next(a)

    assert ax.text == "Select attackers"
    return _pass(g, ax)

def activateAbility(g, ax, name, player_id):
    while ax.text != "You have priority" or ax.player.id != player_id:
        ax = _pass(g, ax)

    for a in ax.actions:
        if isinstance(a, AbilityAction):
            if a.text.startswith("Activate") and a.object.get_state().title == name:
                return g.next(a)

    assert False

def selectTarget(g, ax, name):
    printState(g, ax)
    assert ax.text.startswith("Choose a target")
    for a in ax.actions:
        if a.object is not None:
            if a.object.get_state().title == name:
                return g.next(a)

    assert False

def findObjectInPlay(g, name):
    zone = g.get_in_play_zone()
    for o in zone.objects:
        if o.get_state().title == name:
            return o

    assert False

class ManaClashTest(unittest.TestCase):

    def testAngelicPage(self):
        g = createGameInMainPhase(["Plains", "Angelic Page"], ["Mountain", "Raging Goblin"])
        p1 = g.players[0].id
        p2 = g.players[1].id

        a = g.next(None)
        a = playLand(g, a, "Plains")
        a = playSpell(g, a, "Angelic Page")
        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)
        a = playLand(g, a, "Mountain")
        a = playSpell(g, a, "Raging Goblin")

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])
        a = activateAbility(g, a, "Angelic Page", p1)
        a = selectTarget(g, a, "Raging Goblin")
        a = postcombatMainPhase(g, a)

        goblin = findObjectInPlay(g, "Raging Goblin")
        assert g.obj(p1).life == 18
        assert goblin.get_state().power == 2
        assert goblin.get_state().toughness == 2

        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)
        goblin = findObjectInPlay(g, "Raging Goblin")
        assert goblin.get_state().power == 1
        assert goblin.get_state().toughness == 1

        a = activateAbility(g, a, "Angelic Page", p1)
        assert len(a.actions) == 1


if __name__ == "__main__":
    unittest.main()

