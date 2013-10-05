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
from abilities import PlayLandAbility, PlaySpell, BasicManaAbility
from actions import AbilityAction, PassAction, PayCostAction, QueryNumber, QueryString, ActionSet

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

def createCardToPlay(g, name, player):
    cardObject = createCard(g, name)
    zone = g.get_in_play_zone()
    cardObject.zone_id = zone.id
    cardObject.owner_id = player.id
    cardObject.controller_id = player.id
    zone.objects.append (cardObject)

def createCardToLibrary(g, name, player):
    cardObject = createCard(g, name)
    zone = g.get_library(player)
    cardObject.zone_id = zone.id
    cardObject.owner_id = player.id
    cardObject.controller_id = player.id
    zone.objects.append (cardObject)

def createGameInMainPhase(inPlay1, cards1, inPlay2, cards2):

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

    for c in inPlay1:
        createCardToPlay(g, c, player1)
        
    for c in inPlay2:
        createCardToPlay(g, c, player2)

    g.process_push(GameTurnProcess())
    turnProcess = TurnProcess(player1)
    turnProcess.state = 1
    g.active_player_id = player1.id
    g.process_push(turnProcess)
    g.process_push(MainPhaseProcess("precombat main"))

    evaluate(g)
    p1 = g.players[0].id
    p2 = g.players[1].id
    a = g.next(None)

    return g, a, p1, p2

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

    if isinstance(a, ActionSet):
        for _ in a.actions:
            print `_` + " " + _.text

    else:
        print `a`

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

def declareBlockersStep(g, ax):
    while g.current_phase != "combat" or g.current_step != "declare blockers":
        ax = _pass(g, ax)
    return ax

def combatDamageStep(g, ax):
    while g.current_phase != "combat" or g.current_step != "combat damage":
        ax = _pass(g, ax)
    return ax

def declareAttackers(g, ax, lst):

    for attacker in lst:
        found = False
        assert ax.text == "Select attackers"
        for a in ax.actions:
            if a.object != None and a.object.get_state().title == attacker:
                found = True
                ax = g.next(a)
                break

        assert found

    assert ax.text == "Select attackers"
    return _pass(g, ax)

def declareBlockers(g, ax, blockers, attackers):

    assert len(blockers) == len(attackers)
    for i in range(len(blockers)):
        blocker = blockers[i]
        attacker = attackers[i]
        foundBlocker = False
        assert ax.text == "Select blockers"
        for b in ax.actions:
            if b.object != None and b.object.get_state().title == blocker:
                foundBlocker = True
                ax = g.next(b)

                printState(g, ax)

                foundAttacker = False
                assert ax.text.startswith("Block which")
                for a in ax.actions:
                    if a.object != None and a.object.get_state().title == attacker:
                        foundAttacker = True
                        ax = g.next(a)
                        break

                assert foundAttacker
                break

        assert foundBlocker

    printState(g, ax)
    assert ax.text == "Select blockers"
    return _pass(g, ax)


def emptyStack(g, ax):
    # passes until everything on stack resolves
    while len(g.get_stack_zone().objects) > 0:
        ax = _pass(g, ax)

    return ax

def activateAbility(g, ax, name, player_id):
    while ax.text != "You have priority" or ax.player.id != player_id:
        ax = _pass(g, ax)

    for a in ax.actions:
        if isinstance(a, AbilityAction):
            if a.object.get_state().title == name:
                return g.next(a)

    assert False

def basicManaAbility(g, ax, name, player_id):
    for a in ax.actions:
        if isinstance(a, AbilityAction):
            if isinstance(a.ability, BasicManaAbility) and a.object.get_state().title == name:
                return g.next(a) 

    assert False

def payCosts(g, ax):
    while True:
        isCost = False
        for a in ax.actions:
            if isinstance(a, PayCostAction):
                ax = g.next(a)
                isCost = True
                break
        if not isCost:
            break

    assert not (len(ax.actions) == 1 and ax.actions[0].text == "Cancel" and ax.text == "Play Mana Abilities")
    return ax

def payCost(g, ax, cost):
    assert ax.text == "Play Mana Abilities"
    for a in ax.actions:
        if isinstance(a, PayCostAction):
            if a.text.startswith(cost):
                return g.next(a)

    assert False

def discardACard(g, ax, name):
    printState(g, ax)
    assert ax.text == "Discard a card"
    for a in ax.actions:
        if a.text.startswith("Discard") and a.object.get_state().title == name:
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

def selectObject(g, ax, name):
    printState(g, ax)
    for a in ax.actions:
        if a.object is not None:
            if a.object.get_state().title == name:
                return g.next(a)

    assert False

def answerQuestion(g, ax, question, answer):
    assert ax.text.startswith(question)
    for a in ax.actions:
        if a.text.startswith(answer):
            return g.next(a)
    assert False

def answerStringQuery(g, ax, question, answer):
    assert isinstance(ax, QueryString)
    assert ax.text.startswith(question)
    return g.next(answer)

def chooseX(g, ax, answer):
    assert isinstance(ax, QueryNumber)
    assert ax.text.startswith("Choose X")
    return g.next(answer)

def findObjectInPlay(g, name):
    zone = g.get_in_play_zone()
    for o in zone.objects:
        if o.get_state().title == name:
            return o

    assert False

def findObjectInGraveyard(g, player_id, name):
    player = g.obj(player_id)
    zone = g.get_graveyard(player)
    for o in zone.objects:
        if o.get_state().title == name:
            return o

    assert False

def findObjectInHand(g, player_id, name):
    player = g.obj(player_id)
    zone = g.get_hand(player)
    for o in zone.objects:
        if o.get_state().title == name:
            return o

    assert False

def assertNoSuchObjectInPlay(g, name):
    zone = g.get_in_play_zone()
    for o in zone.objects:
        assert o.get_state().title != name

def assertCardInOptions(g, ax, name):
    for a in ax.actions:
        if a.object is not None:
            if a.object.get_state().title == name:
                return True

    assert False

class ManaClashTest(unittest.TestCase):

    def testAbyssalSpecter(self):
        g, a, p1, p2 = createGameInMainPhase(["Abyssal Specter"], [], [], ["Plains", "Mountain"])

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Abyssal Specter"])
        
        a = combatDamageStep(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = discardACard(g, a, "Plains")
        assert len(g.get_hand(g.obj(p2)).objects) == 1

    def testAngelicPage(self):
        g, a, p1, p2 = createGameInMainPhase(["Plains", "Plains"], ["Angelic Page"], [], ["Mountain", "Raging Goblin"])

        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)
        a = playSpell(g, a, "Angelic Page")
        a = payCosts(g, a)

        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)
        a = playLand(g, a, "Mountain")
        a = basicManaAbility(g, a, "Mountain", p2)
        a = playSpell(g, a, "Raging Goblin")
        a = payCosts(g, a)

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

    def testArchivist(self):
        g, a, p1, p2 = createGameInMainPhase(["Archivist"], [], [], [])

        a = precombatMainPhase(g, a)

        assert len(g.get_hand(g.obj(p1)).objects) == 0
        a = activateAbility(g, a, "Archivist", p1)
        a = emptyStack(g, a)
        assert len(g.get_hand(g.obj(p1)).objects) == 1

    def testAvatarOfHope(self):
        g, a, p1, p2 = createGameInMainPhase(["Plains", "Plains"], ["Avatar of Hope"], [], [])

        g.obj(p1).life = 3

        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)
        a = playSpell(g, a, "Avatar of Hope")
        a = payCosts(g, a)

        a = emptyStack(g, a) 

        findObjectInPlay(g, "Avatar of Hope")

    def testAvenCloudchaser(self):
        g, a, p1, p2 = createGameInMainPhase(["Plains", "Plains"], ["Pacifism"], ["Plains", "Plains", "Plains", "Plains", "Raging Goblin"], ["Aven Cloudchaser"])

        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)
        a = playSpell(g, a, "Pacifism")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)

        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)
        a = basicManaAbility(g, a, "Plains", p2)
        a = basicManaAbility(g, a, "Plains", p2)
        a = basicManaAbility(g, a, "Plains", p2)
        a = basicManaAbility(g, a, "Plains", p2)

        a = playSpell(g, a, "Aven Cloudchaser")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = selectTarget(g, a, "Pacifism")

        a = emptyStack(g, a)
        assertNoSuchObjectInPlay(g, "Pacifism")
        findObjectInPlay(g, "Aven Cloudchaser")
       
    def testAvenFisher (self):
        g, a, p1, p2 = createGameInMainPhase(["Island", "Island", "Island", "Island"], ["Aven Fisher"], ["Mountain"], ["Shock"])

        a = basicManaAbility(g, a, "Island", p1)
        a = basicManaAbility(g, a, "Island", p1)
        a = basicManaAbility(g, a, "Island", p1)
        a = basicManaAbility(g, a, "Island", p1)
        a = playSpell(g, a, "Aven Fisher")
        a = payCosts(g, a)

        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        a = basicManaAbility(g, a, "Mountain", p2)
        a = playSpell(g, a, "Shock")
        a = selectTarget(g, a, "Aven Fisher")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = answerQuestion(g, a, "Draw a card?", "Yes")

        assert len(g.get_hand(g.obj(p1)).objects) == 1
       
    def testAvenFlock (self):
        g, a, p1, p2 = createGameInMainPhase(["Plains", "Plains", "Plains", "Aven Flock"], [], [], [])

        flock = findObjectInPlay(g, "Aven Flock")
        assert flock.get_state().power == 2
        assert flock.get_state().toughness == 3

        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)

        a = activateAbility(g, a, "Aven Flock", p1)
        a = payCosts(g, a)
        a = activateAbility(g, a, "Aven Flock", p1)
        a = payCosts(g, a)
        a = activateAbility(g, a, "Aven Flock", p1)
        a = payCosts(g, a)

        a = emptyStack(g, a)

        flock = findObjectInPlay(g, "Aven Flock")
        assert flock.get_state().power == 2
        assert flock.get_state().toughness == 6

        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        flock = findObjectInPlay(g, "Aven Flock")
        assert flock.get_state().power == 2
        assert flock.get_state().toughness == 3

    def testBalanceOfPower(self):
        g, a, p1, p2 = createGameInMainPhase([], ["Balance of Power", "Island"], [], ["Plains", "Plains", "Plains"])
  
        g.obj(p1).manapool = "UUUUU"
        a = playSpell(g, a, "Balance of Power")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a) 
        a = emptyStack(g, a)

        assert len(g.get_hand(g.obj(p1)).objects) == 3
        assert len(g.get_hand(g.obj(p2)).objects) == 3

    def testBirdsOfParadise(self):
        g, a, p1, p2 = createGameInMainPhase(["Birds of Paradise"], [], [], [])

        a = activateAbility(g, a, "Birds of Paradise", p1)
        a = answerQuestion(g, a, "Choose a color", "White")
        a = emptyStack(g, a)
        assert g.obj(p1).manapool == "W"
        a = endOfTurn(g, a)
        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        a = activateAbility(g, a, "Birds of Paradise", p1)
        a = answerQuestion(g, a, "Choose a color", "Black")
        a = emptyStack(g, a)
        assert g.obj(p1).manapool == "B"

    def testBlanchwoodArmor(self):
        g, a, p1, p2 = createGameInMainPhase(["Raging Goblin", "Forest", "Forest", "Forest"], ["Blanchwood Armor"], [], [])

        a = basicManaAbility(g, a, "Forest", p1)
        a = basicManaAbility(g, a, "Forest", p1)
        a = basicManaAbility(g, a, "Forest", p1)
       
        a = playSpell(g, a, "Blanchwood Armor")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])

        a = postcombatMainPhase(g, a)

        goblin = findObjectInPlay(g, "Raging Goblin")
        assert g.obj(p2).life == 16
        assert goblin.get_state().power == 4
        assert goblin.get_state().toughness == 4
       
    def testBlaze(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain", "Mountain", "Mountain", "Mountain"], ["Blaze"], [], [])

        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)

        a = playSpell(g, a, "Blaze")
        a = selectTarget(g, a, "Player2")
        a = chooseX(g, a, 3)
        a = payCosts(g, a)
        a = emptyStack(g, a)

        assert g.obj(p2).life == 17

    def testBlessedReversal(self):
        g, a, p1, p2 = createGameInMainPhase(["Raging Goblin", "Canyon Wildcat"], [], ["Plains", "Plains"], ["Blessed Reversal"])

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin", "Canyon Wildcat"])
        a = _pass(g, a)

        a = basicManaAbility(g, a, "Plains", p2)
        a = basicManaAbility(g, a, "Plains", p2)
        a = playSpell(g, a, "Blessed Reversal")
        a = payCosts(g, a)
        a = emptyStack(g, a)
        assert g.obj(p2).life == 26
        a = postcombatMainPhase(g, a)
        assert g.obj(p2).life == 23

    def testBlindingAngel(self):
        g, a, p1, p2 = createGameInMainPhase(["Blinding Angel"], [], [], [])

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Blinding Angel"])
        a = postcombatMainPhase(g, a)
        assert g.obj(p2).life == 18
        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        assert g.current_phase == "postcombat main"
        a = endOfTurn(g, a)
        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        assert g.current_phase == "combat"

    def testBloodMoon(self):
        g, a, p1, p2 = createGameInMainPhase(["Blood Moon", "City of Brass"], [], [], [])
        a = activateAbility(g, a, "City of Brass", p1)
        assert g.obj(p1).manapool == "R"        

    def testBloodshotCyclops(self):
        g, a, p1, p2 = createGameInMainPhase(["Bloodshot Cyclops", "Raging Goblin"], [], [], [])
        a = activateAbility(g, a, "Bloodshot Cyclops", p1) 
        a = selectTarget(g, a, "Player2")
        a = payCost(g, a, "Sacrifice")
        a = selectObject(g, a, "Raging Goblin")        
        a = emptyStack(g, a)

        assert g.obj(p2).life == 19
        assert findObjectInPlay(g, "Bloodshot Cyclops").tapped

        a = endOfTurn(g, a)
        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        a = activateAbility(g, a, "Bloodshot Cyclops", p1)
        a = selectTarget(g, a, "Player2")
        a = payCost(g, a, "Sacrifice")
        a = selectObject(g, a, "Bloodshot Cyclops")
        a = emptyStack(g, a)

        assert g.obj(p2).life == 15
        assertNoSuchObjectInPlay(g, "Bloodshot Cyclops")

    def testBrassHerald(self):
        g, a, p1, p2 = createGameInMainPhase(["Plains", "Plains", "Plains", "Plains", "Plains", "Plains", "Mountain"], ["Brass Herald"], [], [])
        createCardToLibrary(g, "Raging Goblin", g.obj(p1))
        createCardToLibrary(g, "Goblin Chariot", g.obj(p1))
        createCardToLibrary(g, "Bloodshot Cyclops", g.obj(p1))
        createCardToLibrary(g, "Plains", g.obj(p1))

        for _ in range(6):
           a = basicManaAbility(g, a, "Plains", p1)

        a = playSpell(g, a, "Brass Herald")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
       
        printState(g, a) 
        a = answerStringQuery(g, a, "Choose Creature Type", "goblin")
        a = _pass(g, a)
        a = _pass(g, a)
        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")
        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")
        
        assert a.text == "Put card to the bottom of your library"
        assert len(a.actions) == 2
        assertCardInOptions(g, a, "Plains")
        assertCardInOptions(g, a, "Bloodshot Cyclops")
        a = selectObject(g, a, "Plains")
        a = selectObject(g, a, "Bloodshot Cyclops")

        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Raging Goblin")
        a = payCosts(g, a)       
 
        a = declareAttackersStep(g, a)
        printState(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])
        a = postcombatMainPhase(g, a)

        assert g.obj(p2).life == 18
        findObjectInHand(g, p1, "Goblin Chariot")


    def testBribery(self):
        g, a, p1, p2 = createGameInMainPhase(["Island", "Island", "Island", "Island", "Island"], ["Bribery"], [], [])
        createCardToLibrary(g, "Raging Goblin", g.obj(p2))

        for _ in range(5):
           a = basicManaAbility(g, a, "Island", p1)
        
        a = playSpell(g, a, "Bribery")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        assert a.player.id == p1
        printState(g, a)

        a = selectObject(g, a, "Raging Goblin")
       
        a = declareAttackersStep(g, a)
        printState(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])
        printState(g, a)
        a = postcombatMainPhase(g, a)
        printState(g, a)
        assert g.obj(p2).life == 19

    def testCallOfTheWild(self):
        g, a, p1, p2 = createGameInMainPhase(["Forest", "Forest", "Forest", "Forest", "Call of the Wild"], [], [], [])
        createCardToLibrary(g, "Raging Goblin", g.obj(p1))

        for _ in range(4):
           a = basicManaAbility(g, a, "Forest", p1)

        a = activateAbility(g, a, "Call of the Wild", p1)
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        assert findObjectInPlay(g, "Raging Goblin") is not None


    def testCircleOfProtectionRed(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain"], ["Shock"], ["Plains", "Circle of Protection: Red"], [])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Shock")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)
        a = _pass(g, a) 

        a = basicManaAbility(g, a, "Plains", p2)
        a = activateAbility(g, a, "Circle of Protection: Red", p2)
        printState(g, a)
        a = payCosts(g, a)
        printState(g, a)
        a = _pass(g, a)
        printState(g, a)
        a = _pass(g, a)
        printState(g, a)

        a = selectObject(g, a, "Shock")
        a = emptyStack(g, a)

        assert g.obj(p2).life == 20

    def testCoastalTower(self):
        g, a, p1, p2 = createGameInMainPhase(["Coastal Tower"], [], [], [])
        a = activateAbility(g, a, "Coastal Tower", p1)
        a = answerQuestion(g, a, "Choose mana", "W")
        assert g.obj(p1).manapool == "W"

    def testCoercion(self):
        g, a, p1, p2 = createGameInMainPhase(["Swamp", "Swamp", "Swamp"], ["Coercion"], [], ["Raging Goblin", "Plains", "Seismic Assault"])
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = playSpell(g, a, "Coercion")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = selectObject(g, a, "Plains")
        assert len(g.get_hand(g.obj(p2)).objects) == 2
        assert findObjectInGraveyard(g, p2, "Plains") is not None

    def testDiabolicTutor(self):
        g, a, p1, p2 = createGameInMainPhase(["Swamp", "Swamp", "Swamp", "Swamp"], ["Diabolic Tutor"], [], [])
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = playSpell(g, a, "Diabolic Tutor")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = selectObject(g, a, "Plains") 
        assert findObjectInHand(g, p1, "Plains") is not None

    def testDistortingLens(self):
        g, a, p1, p2 = createGameInMainPhase(["Distorting Lens", "Island", "Island", "Island"], ["Hibernation"], ["Raging Goblin"], [])
        a = activateAbility(g, a, "Distorting Lens", p1)
        a = selectTarget(g, a, "Raging Goblin")
        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)
        a = answerQuestion(g, a, "Choose", "Green")
        
        a = basicManaAbility(g, a, "Island", p1)
        a = basicManaAbility(g, a, "Island", p1)
        a = basicManaAbility(g, a, "Island", p1)
        a = playSpell(g, a, "Hibernation")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        assertNoSuchObjectInPlay(g, "Raging Goblin")
        goblin = findObjectInHand(g, p2, "Raging Goblin")
        assert "red" in goblin.get_state().tags
        assert "green" not in goblin.get_state().tags

    def testElvishPioneer(self):
        g, a, p1, p2 = createGameInMainPhase(["Forest"], ["Elvish Pioneer", "Plains"], [], [])
        a = basicManaAbility(g, a, "Forest", p1)
        a = playSpell(g, a, "Elvish Pioneer")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        printState(g, a)
        a = selectObject(g, a, "Plains")
        plains = findObjectInPlay(g, "Plains")
        assert plains.tapped

    def testGravePact(self):
        g, a, p1, p2 = createGameInMainPhase(["Grave Pact", "Raging Goblin"], [], ["Elvish Pioneer", "Air Elemental"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Air Elemental"], ["Raging Goblin"])
        
        printState(g, a)
        a = combatDamageStep(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        printState(g, a)
        a = _pass(g, a)
        printState(g, a)
        a = _pass(g, a)
        printState(g, a)

        a = selectObject(g, a, "Elvish Pioneer")
        a = postcombatMainPhase(g, a)

        findObjectInGraveyard(g, p2, "Elvish Pioneer")
        findObjectInPlay(g, "Air Elemental")

    def testHealingSalve(self):
        g, a, p1, p2 = createGameInMainPhase(["Plains", "Raging Goblin"], ["Healing Salve"], ["Plains", "Elvish Pioneer"], ["Healing Salve"])
        a = basicManaAbility(g, a, "Plains", p1)
        a = playSpell(g, a, "Healing Salve")
        a = answerQuestion(g, a, "Choose", "target player gains 3 life")
        a = selectTarget(g, a, "Player1")
        a = payCosts(g, a)
        a = emptyStack(g, a)
        assert g.obj(p1).life == 23

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Elvish Pioneer"], ["Raging Goblin"])
        a = _pass(g, a)
        a = basicManaAbility(g, a, "Plains", p2)
        a = playSpell(g, a, "Healing Salve")
        a = answerQuestion(g, a, "Choose", "prevent the next 3 damage that would be dealt to target creature or player this turn")
        a = selectTarget(g, a, "Elvish Pioneer")
        a = payCosts(g, a)

        a = postcombatMainPhase(g, a)
        findObjectInPlay(g, "Elvish Pioneer")
        findObjectInGraveyard(g, p1, "Raging Goblin")
        assert g.obj(p2).life == 20

    def testIndex(self):
        g, a, p1, p2 = createGameInMainPhase(["Island"], ["Index"], [], [])
        createCardToLibrary(g, "Raging Goblin", g.obj(p1))
        createCardToLibrary(g, "Iron Star", g.obj(p1))
        createCardToLibrary(g, "Elvish Pioneer", g.obj(p1))
        createCardToLibrary(g, "Air Elemental", g.obj(p1))
        createCardToLibrary(g, "Island", g.obj(p1))

        a = basicManaAbility(g, a, "Island", p1)
        a = playSpell(g, a, "Index")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)

        assert a.text == "Put card on top of your library"
        assert len(a.actions) == 5
        assertCardInOptions(g, a, "Raging Goblin")
        assertCardInOptions(g, a, "Iron Star")
        assertCardInOptions(g, a, "Elvish Pioneer")
        assertCardInOptions(g, a, "Air Elemental")
        assertCardInOptions(g, a, "Island")

        a = selectObject(g, a, "Raging Goblin")
        a = selectObject(g, a, "Elvish Pioneer")
        a = selectObject(g, a, "Iron Star")
        a = selectObject(g, a, "Island")
        a = selectObject(g, a, "Air Elemental")

        a = endOfTurn(g, a)
        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        assert findObjectInHand(g, p1, "Air Elemental")

    def testIronStar(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain", "Mountain", "Iron Star"], ["Raging Goblin"], [], [])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Raging Goblin")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        printState(g, a)
        a = answerQuestion(g, a, "Pay 1 to", "Yes")
        a = basicManaAbility(g, a, "Mountain", p1)
        a = payCosts(g, a)
        a = emptyStack(g, a)

        assert g.obj(p1).life == 21

    def testManaClash(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain"], ["Mana Clash"], [], [])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Mana Clash")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

    def testManaLeak(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain", "Mountain", "Mountain", "Mountain", "Mountain"], ["Raging Goblin", "Shock"], ["Island", "Island", "Island", "Island"], ["Mana Leak", "Mana Leak"])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Raging Goblin")
        a = payCosts(g, a)
        a = _pass(g, a)

        a = basicManaAbility(g, a, "Island", p2)
        a = basicManaAbility(g, a, "Island", p2)
        a = playSpell(g, a, "Mana Leak")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        printState(g, a)

        a = answerQuestion(g, a, "Choose", "Pay")
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = payCosts(g, a)

        printState(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        findObjectInPlay(g, "Raging Goblin")

        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Shock")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)
        a = _pass(g, a)
        
        a = basicManaAbility(g, a, "Island", p2)
        a = basicManaAbility(g, a, "Island", p2)
        a = playSpell(g, a, "Mana Leak")
        a = selectTarget(g, a, "Shock")
        a = payCosts(g, a)
        
        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)
        a = answerQuestion(g, a, "Choose", "Counter")

        a = emptyStack(g, a)

        assert g.obj(p1).life == 20
        assert g.obj(p2).life == 20

    def testMindBend(self):
        g, a, p1, p2 = createGameInMainPhase(["Eastern Paladin", "Island", "Swamp", "Swamp"], ["Mind Bend"], ["Raging Goblin"], [])
        a = basicManaAbility(g, a, "Island", p1)
        a = playSpell(g, a, "Mind Bend")
        a = selectTarget(g, a, "Eastern Paladin")
        printState(g, a)

        a = answerQuestion(g, a, "Choose a color or a basic land type", "green")
        printState(g, a)
        a = answerQuestion(g, a, "Change 'green' to...", "red")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        printState(g, a) 
        
        a = basicManaAbility(g, a, "Swamp", p1) 
        a = basicManaAbility(g, a, "Swamp", p1) 
        a = activateAbility(g, a, "Eastern Paladin", p1)
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        assertNoSuchObjectInPlay(g, "Raging Goblin")


    def testMindRot(self):
        g, a, p1, p2 = createGameInMainPhase(["Swamp", "Swamp", "Swamp"], ["Mind Rot"], [], ["Plains", "Plains", "Plains"])
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = playSpell(g, a, "Mind Rot")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = selectObject(g, a, "Plains")
        a = selectObject(g, a, "Plains")
        assert len(g.get_hand(g.obj(p2)).objects) == 1

    def testOraclesAttendants(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain"], ["Shock"], ["Oracle's Attendants", "Raging Goblin"], [])

        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Shock")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)
        a = _pass(g, a)

        a = activateAbility(g, a, "Oracle's Attendants", p2)
        printState(g, a)
        a = selectTarget(g, a, "Raging Goblin")
        printState(g, a)
        a = selectObject(g, a, "Shock")
        
        a = emptyStack(g, a)

        goblin = findObjectInPlay(g, "Raging Goblin")
        attendants = findObjectInPlay(g, "Oracle's Attendants")
        assert attendants.damage == 2
        

    def testOrcishSpy(self):
        g, a, p1, p2 = createGameInMainPhase(["Orcish Spy"], [], [], [])
        a = activateAbility(g, a, "Orcish Spy", p1)
        a = selectTarget(g, a, "Player2")
        a = _pass(g, a)
        a = _pass(g, a)
        printState(g, a)
        a = answerQuestion(g, a, "Look at", "OK")

    def testPanicAttack(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain", "Mountain", "Mountain", "Raging Goblin"], ["Panic Attack"], ["Abyssal Specter", "Angel of Mercy", "Elvish Pioneer"], [])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)

        a = playSpell(g, a, "Panic Attack")

        assert a.text.startswith("Choose the first target")
        a = selectObject(g, a, "Abyssal Specter")

        assert a.text.startswith("Choose the second target")
        a = selectObject(g, a, "Angel of Mercy")
      
        a = answerQuestion(g, a, "Choose the third", "Enough")  

        a = payCosts(g, a)

        a = emptyStack(g, a)

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])
        a = declareBlockersStep(g, a)

        printState(g, a)

        assert len(a.actions) == 2  # pass and pioneer
        a = declareBlockers(g, a, ["Elvish Pioneer"], ["Raging Goblin"])
       
        a = postcombatMainPhase(g, a)

        assertNoSuchObjectInPlay(g, "Raging Goblin")
        assertNoSuchObjectInPlay(g, "Elvish Pioneer")


    def testPersecute(self):
        g, a, p1, p2 = createGameInMainPhase(["Swamp", "Swamp", "Swamp", "Swamp"], ["Persecute"], [], ["Raging Goblin", "Seismic Assault", "Mind Rot"])
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = playSpell(g, a, "Persecute")
        a = selectTarget(g, a, "Player2")
        a = answerQuestion(g, a, "Choose a color", "red")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = answerQuestion(g, a, "Player Player2 reveals cards", "OK")
        a = answerQuestion(g, a, "Player Player2 reveals cards", "OK")
        assert len(g.get_hand(g.obj(p2)).objects) == 1

    def testPrimevalForce(self):
        g, a, p1, p2 = createGameInMainPhase(["Forest", "Forest", "Forest", "Plains", "Plains"], ["Primeval Force", "Primeval Force"], [], [])
        a = basicManaAbility(g, a, "Forest", p1)
        a = basicManaAbility(g, a, "Forest", p1)
        a = basicManaAbility(g, a, "Forest", p1)
        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)

        a = playSpell(g, a, "Primeval Force")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = answerQuestion(g, a, "Choose", "Pay")
        printState(g, a)

        for _ in range(3):
            a = answerQuestion(g, a, "Play Mana Abilities", "Sacrifice forest")
            a = selectObject(g, a, "Forest")

        printState(g, a)
        firstPrimevalForce = findObjectInPlay(g, "Primeval Force").id

        g.obj(p1).manapool = "GGGGG"
        a = playSpell(g, a, "Primeval Force")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = answerQuestion(g, a, "Choose", "Sacrifice")
        secondPrimevalForce = findObjectInGraveyard(g, p1, "Primeval Force").id
        assert firstPrimevalForce != secondPrimevalForce
        

    def testRampantGrowth(self):
        g, a, p1, p2 = createGameInMainPhase(["Forest", "Forest"], ["Rampant Growth"], [], [])
        a = basicManaAbility(g, a, "Forest", p1)
        a = basicManaAbility(g, a, "Forest", p1)
        a = playSpell(g, a, "Rampant Growth")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        a = selectObject(g, a, "Plains")
        plains = findObjectInPlay(g, "Plains")
        assert plains.tapped

    def testRewind(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain"], ["Shock"],["Island", "Island", "Island", "Island"], ["Rewind"])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Shock")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)
        a = _pass(g, a)

        a = basicManaAbility(g, a, "Island", p2) 
        a = basicManaAbility(g, a, "Island", p2) 
        a = basicManaAbility(g, a, "Island", p2) 
        a = basicManaAbility(g, a, "Island", p2) 
        
        a = playSpell(g, a, "Rewind")
        a = selectTarget(g, a, "Shock")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)

        a = selectObject(g, a, "Island")
        a = selectObject(g, a, "Island")
        a = selectObject(g, a, "Island")
        a = selectObject(g, a, "Island")

        printState(g, a)

        assert g.get_stack_length() == 0
        assert g.obj(p2).life == 20
        assert not findObjectInPlay(g, "Island").tapped

    def testSeismicAssault(self):
        g, a, p1, p2 = createGameInMainPhase(["Seismic Assault"], ["Mountain"], [], [])
        a = activateAbility(g, a, "Seismic Assault", p1)
        a = selectTarget(g, a, "Player2")
        a = payCost(g, a, "Discard")
        a = selectObject(g, a, "Mountain")
        a = emptyStack(g, a)

        assert g.obj(p2).life == 18

    def testStarCompass(self):
        g, a, p1, p2 = createGameInMainPhase(["Forest", "Swamp", "Mountain", "Star Compass"], [], [], [])
        a = activateAbility(g, a, "Star Compass", p1)

        assert len(a.actions) == 3

        a = answerQuestion(g, a, "Choose mana", "R")
        assert g.obj(p1).manapool == "R"
 

    def testTeferisPuzzleBox(self):
        g, a, p1, p2 = createGameInMainPhase(["Teferi's Puzzle Box"], ["Mountain", "Raging Goblin"], [], ["Forest", "Rampant Growth", "Primeval Force"])
        a = endOfTurn(g, a)
        printState(g, a)
        # upkeep
        a = _pass(g, a)
        a = _pass(g, a)
        # puzzle box effect in stack
        printState(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        # puzzle box effect resolves
        printState(g, a)

        assert len(a.actions) == 4
        assert a.text == "Put card to the bottom of your library"
        a = selectObject(g, a, "Plains")
        a = selectObject(g, a, "Forest")
        a = selectObject(g, a, "Rampant Growth")
        a = selectObject(g, a, "Primeval Force")

        assert len(g.get_hand(g.obj(p2)).objects) == 4

        a = precombatMainPhase(g, a)

        printState(g, a)

        # should have four plains in hand
        for obj in g.get_hand(g.obj(p2)).objects:
            assert obj.get_state().title == "Plains"

    def testThievesAuction(self):
        g, a, p1, p2 = createGameInMainPhase(["Plains", "Plains", "Raging Goblin"], ["Pacifism", "Thieves' Auction"], ["Eastern Paladin"], [])
        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)
        a = playSpell(g, a, "Pacifism")
        a = selectTarget(g, a, "Eastern Paladin")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        g.obj(p1).manapool = "RRRRRRR"
        a = playSpell(g, a, "Thieves' Auction")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        assert a.player.name == "Player1"
        a = selectObject(g, a, "Raging Goblin")
        assert a.player.name == "Player2"
        a = selectObject(g, a, "Pacifism")
        printState(g, a)
        # choosing a target to enchant
        assert a.player.name == "Player2"
        a = selectObject(g, a, "Raging Goblin")
        assert a.player.name == "Player1"
        a = selectObject(g, a, "Eastern Paladin")
        assert a.player.name == "Player2"
        a = selectObject(g, a, "Plains")
        assert a.player.name == "Player1"
        a = selectObject(g, a, "Plains")
        printState(g, a)

        goblin = findObjectInPlay(g, "Raging Goblin")
        assert "can't attack or block" in goblin.get_state().tags

    def testTwiddle(self):
        g, a, p1, p2 = createGameInMainPhase(["Island", "Island"], ["Twiddle", "Twiddle"], ["Raging Goblin"], [])

        a = basicManaAbility(g, a, "Island", p1)
        a = playSpell(g, a, "Twiddle")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        a = answerQuestion(g, a, "You may", "Tap")

        goblin = findObjectInPlay(g, "Raging Goblin")
        assert goblin.tapped

        a = basicManaAbility(g, a, "Island", p1)
        a = playSpell(g, a, "Twiddle")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        a = answerQuestion(g, a, "You may", "Untap")

        assert not goblin.tapped

    def testVexingArcanix(self):
        g, a, p1, p2 = createGameInMainPhase(["Island", "Island", "Island", "Vexing Arcanix"], [], [], [])
        createCardToLibrary(g, "Iron Star", g.obj(p1))
        createCardToLibrary(g, "Plains", g.obj(p1))
        createCardToLibrary(g, "Raging Goblin", g.obj(p1))
      
        a = basicManaAbility(g, a, "Island", p1) 
        a = basicManaAbility(g, a, "Island", p1) 
        a = basicManaAbility(g, a, "Island", p1) 

        a = activateAbility(g, a, "Vexing Arcanix", p1)
        a = selectTarget(g, a, "Player1")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        a = answerStringQuery(g, a, "Name a Card", "Raging Goblin")

        printState(g, a)

        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")
        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")

        goblin = findObjectInHand(g, p1, "Raging Goblin")
        assert g.obj(p1).life == 20

        a = endOfTurn(g, a)        
        a = endOfTurn(g, a)        
        a = precombatMainPhase(g, a)

        a = basicManaAbility(g, a, "Island", p1)
        a = basicManaAbility(g, a, "Island", p1)
        a = basicManaAbility(g, a, "Island", p1)

        a = activateAbility(g, a, "Vexing Arcanix", p1)
        a = selectTarget(g, a, "Player1")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        a = answerStringQuery(g, a, "Name a Card", "Plains")
        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")
        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")

        star = findObjectInGraveyard(g, p1, "Iron Star")
        assert g.obj(p1).life == 18


if __name__ == "__main__":
    unittest.main()

