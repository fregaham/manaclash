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
                if g.obj(a.object_id).get_state().title == name:
                    return g.next(a)

    assert False

def playLand(g, ax, name):
    printState(g, ax)
    for a in ax.actions:
        if isinstance(a, AbilityAction):
            if isinstance(a.ability, PlayLandAbility):
                if g.obj(a.object_id).get_state().title == name:
                    return g.next(a)

    assert False


def printState(g, a):
    player = g.obj(a.player_id)
    print ("player %s: %s" % (player.name, a.text))
    print ("turn %s, phase: %s, step: %s" % (g.get_active_player().name, g.current_phase, g.current_step))
    print ("battlefield: %s" % (" ".join(map(lambda x:str(x),g.get_in_play_zone().objects))))
    print ("stack: %s" % (" ".join(map(lambda x:"["+str(x)+"]",g.get_stack_zone().objects))))
    print ("library: %d graveyard: %d" % (len(g.get_library(player).objects), len(g.get_graveyard(player).objects) ))
    print ("hand: %s" % (" ".join(map(lambda x:"["+str(x)+"]",g.get_hand(player).objects))))
    print ("manapool: %s" % (player.manapool))
    print ("life: %d" % (player.life))

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

def upkeep(g, ax):
    while g.current_phase != "beginning" or g.current_step != "upkeep" or ax.text != "You have priority":
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
            obj = None if a.object_id is None else g.obj(a.object_id)
            if obj != None and obj.get_state().title == attacker:
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
            obj = None if b.object_id is None else g.obj(b.object_id)
            if obj != None and obj.get_state().title == blocker:
                foundBlocker = True
                ax = g.next(b)

                printState(g, ax)

                foundAttacker = False
                assert ax.text.startswith("Block which")
                for a in ax.actions:
                    a_obj = None if a.object_id is None else g.obj(a.object_id)
                    if a_obj != None and a_obj.get_state().title == attacker:
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
    while ax.text != "You have priority" or ax.player_id != player_id:
        ax = _pass(g, ax)

    for a in ax.actions:
        if isinstance(a, AbilityAction):
            if g.obj(a.object_id).get_state().title == name:
                return g.next(a)

    assert False

def basicManaAbility(g, ax, name, player_id):
    for a in ax.actions:
        if isinstance(a, AbilityAction):
            if isinstance(a.ability, BasicManaAbility) and g.obj(a.object_id).get_state().title == name:
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
        if a.text.startswith("Discard") and g.obj(a.object_id).get_state().title == name:
            return g.next(a)

    assert False

def selectTarget(g, ax, name):
    printState(g, ax)
    assert ax.text.startswith("Choose a target")
    for a in ax.actions:
        if a.object_id is not None:
            if g.obj(a.object_id).get_state().title == name:
                return g.next(a)

    assert False

def selectObject(g, ax, name):
    printState(g, ax)
    for a in ax.actions:
        if a.object_id is not None:
            if g.obj(a.object_id).get_state().title == name:
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
        if a.object_id is not None:
            if g.obj(a.object_id).get_state().title == name:
                return True

    assert False

def assertOptions(g, ax, query, *options_prefixes):
    assert ax.text.startswith(query)
    assert len(ax.actions) == len(options_prefixes)
    for i in range(len(ax.actions)):
        assert ax.actions[i].text.startswith(options_prefixes[i])


class ManaClashTest(unittest.TestCase):

    def testAbyssalSpecter(self):
        g, a, p1, p2 = createGameInMainPhase(["Abyssal Specter"], [], [], ["Plains", "Mountain"])

        g = g.copy()

        a = declareAttackersStep(g, a)

        g = g.copy()

        a = declareAttackers(g, a, ["Abyssal Specter"])

        g = g.copy()

        
        a = combatDamageStep(g, a)
        g = g.copy()

        a = _pass(g, a)
        g = g.copy()

        a = _pass(g, a)
        g = g.copy()
        a = _pass(g, a)
        
        g = g.copy()
        a = _pass(g, a)

        g = g.copy()
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
        assert a.player_id == p1
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

    def testCinderWall(self):
        g, a, p1, p2 = createGameInMainPhase(["Goblin Chariot"], [], ["Cinder Wall"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Goblin Chariot"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Cinder Wall"], ["Goblin Chariot"])
        a = postcombatMainPhase(g, a)

        assertNoSuchObjectInPlay(g, "Cinder Wall")
        assertNoSuchObjectInPlay(g, "Goblin Chariot")

    def testChastise(self):
        g, a, p1, p2 = createGameInMainPhase(["Goblin Chariot"], [], ["Plains", "Plains", "Plains", "Plains"], ["Chastise"])

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Goblin Chariot"])

        printState(g, a)

        a = _pass(g, a)

        a = basicManaAbility(g, a, "Plains", p2)
        a = basicManaAbility(g, a, "Plains", p2)
        a = basicManaAbility(g, a, "Plains", p2)
        a = basicManaAbility(g, a, "Plains", p2)

        a = playSpell(g, a, "Chastise")
        a = selectTarget(g, a, "Goblin Chariot")
        a = payCosts(g, a)

        a = emptyStack(g, a)

        assertNoSuchObjectInPlay(g, "Goblin Chariot") 
        assert g.obj(p2).life == 22


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

    def testCityOfBrass(self):
        g, a, p1, p2 = createGameInMainPhase(["City of Brass"], [], [], [])
        a = activateAbility(g, a, "City of Brass", p1)
        printState(g, a)

        a = answerQuestion(g, a, "Choose a color", "Black")

        printState(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
        printState(g, a)

        assert g.obj(p1).life == 19

    def testCoastalHornclaw(self):
        g, a, p1, p2 = createGameInMainPhase(["Coastal Hornclaw", "Island"], [], [], [])
        hornclaw = findObjectInPlay(g, "Coastal Hornclaw") 
        assert "flying" not in hornclaw.get_state().tags

        a = activateAbility(g, a, "Coastal Hornclaw", p1)
        printState(g, a)

        a = answerQuestion(g, a, "Play", "Sacrifice land")
        printState(g, a)
        a = selectObject(g, a, "Island")

        a = emptyStack(g, a)

        hornclaw = findObjectInPlay(g, "Coastal Hornclaw")
        assert "flying" in hornclaw.get_state().tags
   
        a = endOfTurn(g, a)
        a = endOfTurn(g, a)

        hornclaw = findObjectInPlay(g, "Coastal Hornclaw")
        assert "flying" not in hornclaw.get_state().tags


    def testCoastalTower(self):
        g, a, p1, p2 = createGameInMainPhase(["Coastal Tower"], [], [], [])
        a = activateAbility(g, a, "Coastal Tower", p1)
        a = answerQuestion(g, a, "Choose mana", "W")
        assert g.obj(p1).manapool == "W"

    def testCoatOfArms(self):
        g, a, p1, p2 = createGameInMainPhase(["Coat of Arms", "Goblin Chariot", "Goblin Raider", "Goblin Glider"], [], [], [])
        chariot = findObjectInPlay(g, "Goblin Chariot") 
        raider = findObjectInPlay(g, "Goblin Raider")
        glider = findObjectInPlay(g, "Goblin Glider")

        assert chariot.get_state().power == 4
        assert chariot.get_state().toughness == 4

        assert raider.get_state().power == 4
        assert raider.get_state().toughness == 4

        assert glider.get_state().power == 3
        assert glider.get_state().toughness == 3


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

    def testConfiscate(self):
        g, a, p1, p2 = createGameInMainPhase([], ["Confiscate"], ["Glory Seeker"], [])
        g.obj(p1).manapool = "UUUUUU"

        a = playSpell(g, a, "Confiscate")
        a = selectTarget(g, a, "Glory Seeker")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        seeker = findObjectInPlay(g, "Glory Seeker")
        assert "summoning sickness" in seeker.get_state().tags
        assert seeker.get_state().controller_id == p1


    def testDarkBanishing(self):
        g, a, p1, p2 = createGameInMainPhase(["Swamp", "Swamp", "Swamp"], ["Dark Banishing"], ["Raging Goblin"], [])
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)

        a = playSpell(g, a, "Dark Banishing")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)

        a = emptyStack(g, a)

        assert findObjectInGraveyard(g, p2, "Raging Goblin") is not None

    def testDeathPitOffering(self):
        g, a, p1, p2 = createGameInMainPhase(["Raging Goblin", "Drudge Skeletons"], ["Death Pit Offering", "Scathe Zombies"], [], [])
        g.obj(p1).manapool = "BBBBBBB"
        a = playSpell(g, a, "Death Pit Offering")

        printState(g, a)

        a = payCosts(g, a)
        a = emptyStack(g, a)

        printState(g, a)

        assertNoSuchObjectInPlay(g, "Raging Goblin")
        assertNoSuchObjectInPlay(g, "Drudge Skeletons")

        a = playSpell(g, a, "Scathe Zombies")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        zombies = findObjectInPlay(g, "Scathe Zombies")
        assert zombies.get_state().power == 4
        assert zombies.get_state().toughness == 4

    def testDefenseGrid(self):
        g, a, p1, p2 = createGameInMainPhase(["Defense Grid"], [], ["Mountain", "Mountain", "Mountain", "Mountain"], ["Shock", "Shock"])
        a = _pass(g, a)

        a = basicManaAbility(g, a, "Mountain", p2)
        a = playSpell(g, a, "Shock")
        a = selectTarget(g, a, "Player1")
      
        printState(g, a) 

        assertOptions(g, a, "Play Mana Abilities", "Cancel", "[R]", "[R]", "[R]")

        a = basicManaAbility(g, a, "Mountain", p2)
        a = basicManaAbility(g, a, "Mountain", p2)
        a = basicManaAbility(g, a, "Mountain", p2)

        printState(g, a) 
        assertOptions(g, a, "Play Mana Abilities", "Cancel", "Pay R3")

        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        assert g.obj(p1).life == 18

        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        a = basicManaAbility(g, a, "Mountain", p2)
        a = playSpell(g, a, "Shock")
        a = selectTarget(g, a, "Player1")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        assert g.obj(p1).life == 16


    def testDrudgeSkeletons(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain"], ["Shock"], ["Drudge Skeletons", "Swamp"], [])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Shock")
        a = selectTarget(g, a, "Drudge Skeletons")
        a = payCosts(g, a)
        a = _pass(g, a)

        a = basicManaAbility(g, a, "Swamp", p2)
        a = activateAbility(g, a, "Drudge Skeletons", p2)
        a = payCosts(g, a)
        a = emptyStack(g, a)

        printState(g, a)

        skeletons = findObjectInPlay(g, "Drudge Skeletons")

        assert skeletons.damage == 0
        assert skeletons.tapped 


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

    def testDisruptingScepter(self):
        g, a, p1, p2 = createGameInMainPhase(["Swamp", "Swamp", "Swamp", "Disrupting Scepter"], [], [], ["Island", "Plains"])
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = basicManaAbility(g, a, "Swamp", p1)
        a = activateAbility(g, a, "Disrupting Scepter", p1)
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)

        a = selectObject(g, a, "Plains") 

        assert len(g.get_hand(g.obj(p2)).objects) == 1

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

    def testFlyingCarpet(self):
        g, a, p1, p2 = createGameInMainPhase(["Flying Carpet", "Raging Goblin", "Mountain", "Mountain"], [], [], [])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = activateAbility(g, a, "Flying Carpet", p1)

        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        goblin = findObjectInPlay(g, "Raging Goblin")
        assert "flying" in goblin.get_state().tags

    def testFyndhornElder(self):
        g, a, p1, p2 = createGameInMainPhase(["Fyndhorn Elder"], [], [], [])
        a = activateAbility(g, a, "Fyndhorn Elder", p1)
        a = emptyStack(g, a)

        assert g.obj(p1).manapool == "GG"

    def testFungusaur(self):
        g, a, p1, p2 = createGameInMainPhase(["Fungusaur"], [], ["Raging Goblin"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Fungusaur"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Raging Goblin"], ["Fungusaur"])

        a = postcombatMainPhase(g, a)
        fungusaur = findObjectInPlay(g, "Fungusaur")

        assert fungusaur.get_state().power == 3
        assert fungusaur.get_state().toughness == 3

    def testFurnanceOfRath(self):
        g, a, p1, p2 = createGameInMainPhase(["Furnace of Rath", "Goblin Chariot"], [], ["Giant Badger"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Goblin Chariot"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Giant Badger"], ["Goblin Chariot"])

        a = postcombatMainPhase(g, a)

        assertNoSuchObjectInPlay(g, "Goblin Chariot")
        assertNoSuchObjectInPlay(g, "Giant Badger")


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

    def testHammerOfBogardan(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain", "Mountain", "Mountain", "Mountain", "Mountain"], ["Hammer of Bogardan"], [], [])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Hammer of Bogardan")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)

        a = emptyStack(g, a)

        assert g.obj(p2).life == 17

        a = endOfTurn(g, a)
        a = endOfTurn(g, a)

        a = upkeep(g, a)
        printState(g, a)

        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)

        a = activateAbility(g, a, "Hammer of Bogardan", p1)
        a = payCosts(g, a)

        a = endOfTurn(g, a)
        a = endOfTurn(g, a)
        a = postcombatMainPhase(g, a)

        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Hammer of Bogardan")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)

        a = emptyStack(g, a)

        assert g.obj(p2).life == 14

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

    def testHolyDay(self):
        g, a, p1, p2 = createGameInMainPhase(["Raging Goblin", "Plains"], ["Holy Day"], ["Elvish Pioneer"], [])
        a = basicManaAbility(g, a, "Plains", p1)
        
        a = playSpell(g, a, "Holy Day")
        a = payCosts(g, a)

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Elvish Pioneer"], ["Raging Goblin"])

        a = postcombatMainPhase(g, a)
        findObjectInPlay(g, "Raging Goblin")
        findObjectInPlay(g, "Elvish Pioneer")

    def testHowlingMine(self):
        g, a, p1, p2 = createGameInMainPhase(["Howling Mine"], [], [], ["Howling Mine"])
        assert len(g.get_hand(g.obj(p1)).objects) == 0
        assert len(g.get_hand(g.obj(p2)).objects) == 1

        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        assert len(g.get_hand(g.obj(p2)).objects) == 3

        g.obj(p2).manapool = "2"

        a = playSpell(g, a, "Howling Mine")
        a = payCosts(g, a)

        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        assert len(g.get_hand(g.obj(p1)).objects) == 3
        assert len(g.get_hand(g.obj(p2)).objects) == 2

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

    def testInspiration(self):
        g, a, p1, p2 = createGameInMainPhase(["Island", "Island", "Island", "Island"], ["Inspiration"], [], [])
        a = basicManaAbility(g, a, "Island", p1)
        a = basicManaAbility(g, a, "Island", p1)
        a = basicManaAbility(g, a, "Island", p1)
        a = basicManaAbility(g, a, "Island", p1)

        a = playSpell(g, a, "Inspiration")
        a = selectTarget(g, a, "Player1")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        assert len(g.get_hand(g.obj(p1)).objects) == 2

    def testIntruderAlarm(self):
        g, a, p1, p2 = createGameInMainPhase(["Intruder Alarm", "Air Elemental"], [], ["Goblin Chariot", "Mountain"], ["Raging Goblin"])
        chariot = findObjectInPlay(g, "Goblin Chariot")
        chariot.tapped = True

        elemental = findObjectInPlay(g, "Air Elemental")
        elemental.tapped = True
    
        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        chariot = findObjectInPlay(g, "Goblin Chariot")
        assert chariot.tapped

        elemental = findObjectInPlay(g, "Air Elemental")
        assert elemental.tapped 
           
        a = basicManaAbility(g, a, "Mountain", p2)
        a = playSpell(g, a, "Raging Goblin")
        a = payCosts(g, a)
        a = _pass(g, a)
        a = _pass(g, a)

        a = _pass(g, a)
        a = _pass(g, a)
 
        chariot = findObjectInPlay(g, "Goblin Chariot")
        assert not chariot.tapped

        elemental = findObjectInPlay(g, "Air Elemental")
        assert not elemental.tapped 
        

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

    def testLhurgoyf(self):
        g, a, p1, p2 = createGameInMainPhase(["Lhurgoyf", "Mountain"], ["Shock"], ["Raging Goblin"], [])

        lhurgoyf = findObjectInPlay(g, "Lhurgoyf")
        assert lhurgoyf.get_state().power == 0
        assert lhurgoyf.get_state().toughness == 1

        a = basicManaAbility(g, a, "Mountain", p1)
        a = playSpell(g, a, "Shock")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        lhurgoyf = findObjectInPlay(g, "Lhurgoyf")
        assert lhurgoyf.get_state().power == 1
        assert lhurgoyf.get_state().toughness == 2

    def testLivingTerrain(self):
        g, a, p1, p2 = createGameInMainPhase([], ["Forest", "Living Terrain"], [], [])

        a = playLand(g, a, "Forest")

        g.obj(p1).manapool = "GGGG"
        a = playSpell(g, a, "Living Terrain")
        a = selectTarget(g, a, "Forest")
        a = payCosts(g, a)

        a = declareAttackersStep(g, a)

        # summoning sickness
        assertOptions(g, a, "Select attackers", "No more")

        a = endOfTurn(g, a)
        a = endOfTurn(g, a)
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Forest"])
        a = postcombatMainPhase(g, a)
        assert g.obj(p2).life == 15


    def testLoneWolf(self):
        g, a, p1, p2 = createGameInMainPhase(["Lone Wolf"], [], ["Norwood Ranger"], [])

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Lone Wolf"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Norwood Ranger"], ["Lone Wolf"])
        
        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        a = answerQuestion(g, a, "Assign", "Yes")
        a = postcombatMainPhase(g, a)

        assert g.obj(p2).life == 18

        a = endOfTurn(g, a)
        a = endOfTurn(g, a)

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Lone Wolf"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Norwood Ranger"], ["Lone Wolf"])

        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        a = answerQuestion(g, a, "Assign", "No")
        a = postcombatMainPhase(g, a)

        assert g.obj(p2).life == 18 
        assertNoSuchObjectInPlay(g, "Norwood Ranger")


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

    def testMasterDecoy(self):
        g, a, p1, p2 = createGameInMainPhase(["Master Decoy", "Plains"], [], ["Raging Goblin"], [])
        a = basicManaAbility(g, a, "Plains", p1)
        a = activateAbility(g, a, "Master Decoy", p1)

        printState(g, a) 

        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        goblin = findObjectInPlay(g, "Raging Goblin")
        assert goblin.tapped

    def testMillstone(self):
        g, a, p1, p2 = createGameInMainPhase(["Plains", "Plains", "Millstone"], [], [], [])
        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)
        a = activateAbility(g, a, "Millstone", p1)

        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        grave = g.get_graveyard(g.obj(p2))
        assert len(grave.objects) == 2
               

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

    def testMindSlash(self):
        g, a, p1, p2 = createGameInMainPhase(["Swamp", "Mind Slash", "Raging Goblin"], [], [], ["Plains", "Island"])
        a = basicManaAbility(g, a, "Swamp", p1)
        a = activateAbility(g, a, "Mind Slash", p1)
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)

        a = selectObject(g, a, "Raging Goblin")

        a = _pass(g, a)
        a = _pass(g, a)

        a = selectObject(g, a, "Plains")
     
        assert len(g.get_hand(g.obj(p2)).objects) == 1


    def testNaturalAffinity(self):
        g, a, p1, p2 = createGameInMainPhase(["Forest", "Plains"], ["Natural Affinity"], ["Swamp", "Mountain"], [])
        g.obj(p1).manapool = "GGG"

        a = playSpell(g, a, "Natural Affinity")
        a = payCosts(g, a)

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Forest", "Plains"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Swamp"], ["Forest"])

        a = postcombatMainPhase(g, a)

        assert g.obj(p2).life == 18
        assertNoSuchObjectInPlay(g, "Forest")
        assertNoSuchObjectInPlay(g, "Swamp")
        findObjectInPlay(g, "Mountain")
        findObjectInPlay(g, "Plains")


    def testNightmare(self):
        g, a, p1, p2 = createGameInMainPhase(["Swamp", "Swamp", "Swamp", "Nightmare"], [], [], [])
        nightmare = findObjectInPlay(g, "Nightmare")

        assert nightmare.get_state().power == 3
        assert nightmare.get_state().toughness == 3

    def testNoblePurpose(self):
        g, a, p1, p2 = createGameInMainPhase(["Raging Goblin", "Noble Purpose"], [], [], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])

        a = postcombatMainPhase(g, a)

        assert g.obj(p1).life == 21


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

    def testOrcishArtillery(self):
        g, a, p1, p2 = createGameInMainPhase(["Orcish Artillery"], [], [], [])
        a = activateAbility(g, a, "Orcish Artillery", p1)
        a = selectTarget(g, a, "Player2")
        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)


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

    def testPlowUnder(self):
        g, a, p1, p2 = createGameInMainPhase([], ["Plow Under"], ["Swamp", "Mountain"], [])
        g.obj(p1).manapool = "GGGGG"

        a = playSpell(g, a, "Plow Under")
        a = selectObject(g, a, "Swamp")
        a = selectObject(g, a, "Mountain")
       
        a = payCosts(g, a)

        a = emptyStack(g, a)
        printState(g, a)

        a = endOfTurn(g, a)
        a = endOfTurn(g, a)
        a = endOfTurn(g, a)

        a = precombatMainPhase(g, a)
        findObjectInHand(g, p2, "Swamp")
        findObjectInHand(g, p2, "Mountain")


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

    def testPyrotechnics(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain", "Mountain", "Mountain", "Mountain", "Mountain"], ["Pyrotechnics"], ["Aven Cloudchaser", "Elvish Pioneer"], [])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        
        a = playSpell(g, a, "Pyrotechnics")
        a = selectObject(g, a, "Aven Cloudchaser")
        a = selectObject(g, a, "Aven Cloudchaser")
        a = selectObject(g, a, "Elvish Pioneer")
        a = selectObject(g, a, "Player2")

        a = payCosts(g, a)
        a = emptyStack(g, a)

        assertNoSuchObjectInPlay(g, "Aven Cloudchaser")
        assertNoSuchObjectInPlay(g, "Elvish Pioneer")
        assert g.obj(p2).life == 19

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

    def testRedeem(self):
        g, a, p1, p2 = createGameInMainPhase(["Grizzly Bears"], [], ["Raging Goblin", "Eager Cadet", "Plains", "Plains"], ["Redeem"])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Grizzly Bears"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Raging Goblin", "Eager Cadet"], ["Grizzly Bears", "Grizzly Bears"])

        a = _pass(g, a)

        a = basicManaAbility(g, a, "Plains", p2)
        a = basicManaAbility(g, a, "Plains", p2)

        a = playSpell(g, a, "Redeem")
        a = selectObject(g, a, "Raging Goblin")
        a = selectObject(g, a, "Eager Cadet")
        a = payCosts(g, a)

        a = emptyStack(g, a)
        a = _pass(g, a)
        a = _pass(g, a)

        assert a.text.startswith("Assign 1 damage from")
        a = selectObject(g, a, "Raging Goblin")

        assert a.text.startswith("Assign 1 damage from")
        a = selectObject(g, a, "Eager Cadet")

        a = postcombatMainPhase(g, a)

        findObjectInPlay(g, "Raging Goblin")
        findObjectInPlay(g, "Eager Cadet")
        assertNoSuchObjectInPlay(g, "Grizzly Bears")


    def testRelentlessAssault(self):
        g, a, p1, p2 = createGameInMainPhase(["Raging Goblin"], ["Relentless Assault", "Mountain"], [], [])

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])
        a = postcombatMainPhase(g, a)

        g.obj(p1).manapool = "RRRR"
        a = playSpell(g, a, "Relentless Assault")
        a = payCosts(g, a)

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin"])

        a = postcombatMainPhase(g, a)
        a = playLand(g, a, "Mountain")

        assert g.obj(p2).life == 18
        assert g.turn_number == 0


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

    def testRukhEgg(self):
        g, a, p1, p2 = createGameInMainPhase(["Balduvian Barbarians"], [], ["Rukh Egg"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Balduvian Barbarians"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Rukh Egg"], ["Balduvian Barbarians"])

        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        bird = findObjectInPlay(g, "Token")
        assert bird.get_state().power == 4
        assert bird.get_state().toughness == 4
        assert "flying" in bird.get_state().tags

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Token"])

        a = postcombatMainPhase(g, a)

        assert g.obj(p1).life == 16


    def testSacredGround(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain", "Mountain", "Mountain"], ["Stone Rain"], ["Plains", "Sacred Ground"], [])
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        a = basicManaAbility(g, a, "Mountain", p1)
        
        a = playSpell(g, a, "Stone Rain")
        a = selectTarget(g, a, "Plains")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        assert findObjectInPlay(g, "Plains") is not None
        

    def testSanctimony(self):
        g, a, p1, p2 = createGameInMainPhase(["Mountain", "Mountain"], ["Shock"],["Sanctimony"], [])
        a = basicManaAbility(g, a, "Mountain", p1)

        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        a = answerQuestion(g, a, "Gain 1 life?", "Yes")
        
        printState(g, a)

        assert g.obj(p2).life == 21

        a = basicManaAbility(g, a, "Mountain", p1)

        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        a = answerQuestion(g, a, "Gain 1 life?", "No")
        
        printState(g, a)

    def testSeaMonster(self):
        g, a, p1, p2 = createGameInMainPhase(["Sea Monster"], [], [], ["Island"])
        a = declareAttackersStep(g, a)
        printState(g, a)

        assertOptions(g, a, "Select attackers", "No more")

        a = endOfTurn(g, a)
        a = postcombatMainPhase(g, a)

        a = playLand(g, a, "Island")

        a = endOfTurn(g, a)

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Sea Monster"])
        a = postcombatMainPhase(g, a)

        assert g.obj(p2).life == 14



    def testSeasonedMarshal(self):
        g, a, p1, p2 = createGameInMainPhase(["Seasoned Marshal"], [], ["Raging Goblin"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Seasoned Marshal"])
       
        a = selectObject(g, a, "Raging Goblin")
        printState(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)
        a = _pass(g, a)
        a = _pass(g, a)
 
        printState(g, a)

        assertOptions(g, a, "Select blockers", "No more blockers")


    def testSeismicAssault(self):
        g, a, p1, p2 = createGameInMainPhase(["Seismic Assault"], ["Mountain"], [], [])
        a = activateAbility(g, a, "Seismic Assault", p1)
        a = selectTarget(g, a, "Player2")
        a = payCost(g, a, "Discard")
        a = selectObject(g, a, "Mountain")
        a = emptyStack(g, a)

        assert g.obj(p2).life == 18

    def testSeverSoul(self):
        g, a, p1, p2 = createGameInMainPhase([], ["Sever Soul"], ["Avatar of Hope"], [])
        g.obj(p1).manapool = "BBBBB"
        a = playSpell(g, a, "Sever Soul")
        a = selectTarget(g, a, "Avatar of Hope")
        a = payCosts(g, a) 
        a = emptyStack(g, a)

        assert g.obj(p1).life == 29

    def testShiftingSky(self):
        g, a, p1, p2 = createGameInMainPhase(["Eastern Paladin"], ["Shifting Sky"], ["Raging Goblin"], [])
        g.obj(p1).manapool = "BBU"
        a = playSpell(g, a, "Shifting Sky")
        a = payCosts(g, a)
        a = emptyStack(g, a)
        printState(g, a)
        a = answerQuestion(g, a, "Choose a color", "green")
        g.obj(p1).manapool = "BB"
        a = activateAbility(g, a, "Eastern Paladin", p1)
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        assertNoSuchObjectInPlay(g, "Raging Goblin")

    def testSneakyHomunculus(self):
        g, a, p1, p2 = createGameInMainPhase(["Sneaky Homunculus"], [], ["Ardent Militia"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Sneaky Homunculus"])
        a = declareBlockersStep(g, a)
        a = selectObject(g, a, "Ardent Militia")

        assertOptions(g, a, "Block which attacker", "Cancel block")

        a = answerQuestion(g, a, "Block which attacker", "Cancel")

        a = declareBlockers(g, a, [], [])

        a = endOfTurn(g, a)
        a = endOfTurn(g, a)
        a = endOfTurn(g, a)

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Ardent Militia"])
        a = declareBlockersStep(g, a)
        a = selectObject(g, a, "Sneaky Homunculus")
        assertOptions(g, a, "Block which attacker", "Cancel block")


    def testStarCompass(self):
        g, a, p1, p2 = createGameInMainPhase(["Forest", "Swamp", "Mountain", "Star Compass"], [], [], [])
        a = activateAbility(g, a, "Star Compass", p1)

        assert len(a.actions) == 3

        a = answerQuestion(g, a, "Choose mana", "R")
        assert g.obj(p1).manapool == "R"

    def testSoulFeast(self):
        g, a, p1, p2 = createGameInMainPhase([], ["Soul Feast"], [], [])
        g.obj(p1).manapool = "BBBBB"

        a = playSpell(g, a, "Soul Feast")
        a = selectTarget(g, a, "Player2")
        a = payCosts(g, a)
        a = emptyStack(g, a)
        assert g.obj(p1).life == 24
        assert g.obj(p2).life == 16

    def testSunweb(self):
        g, a, p1, p2 = createGameInMainPhase(["Raging Goblin", "Air Elemental"], [], ["Sunweb"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Raging Goblin", "Air Elemental"])

        a = declareBlockersStep(g, a)

        a = selectObject(g, a, "Sunweb")

        printState(g, a)

        assertOptions(g, a, "Block which attacker", "Cancel block", "Let")
        
        a = selectObject(g, a, "Air Elemental")

        a = postcombatMainPhase(g, a)

        printState(g, a)
        assertNoSuchObjectInPlay(g, "Air Elemental")

    def testSwarmOfRats(self):
        g, a, p1, p2 = createGameInMainPhase(["Swarm of Rats", "Ravenous Rats", "Ravenous Rats"], [], [], [])
        swarm = findObjectInPlay(g, "Swarm of Rats")
        assert swarm.get_state().power == 3
        assert swarm.get_state().toughness == 1


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

        assert a.player_id == p1
        a = selectObject(g, a, "Raging Goblin")
        assert a.player_id == p2
        a = selectObject(g, a, "Pacifism")
        printState(g, a)
        # choosing a target to enchant
        assert a.player_id == p2
        a = selectObject(g, a, "Raging Goblin")
        assert a.player_id == p1
        a = selectObject(g, a, "Eastern Paladin")
        assert a.player_id == p2
        a = selectObject(g, a, "Plains")
        assert a.player_id == p1
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

    def testUnsummon(self):
        g, a, p1, p2 = createGameInMainPhase(["Island"], ["Unsummon"], ["Raging Goblin"], [])
        a = basicManaAbility(g, a, "Island", p1)
        a = playSpell(g, a, "Unsummon")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        assert findObjectInHand(g, p2, "Raging Goblin") != None


    def testUrzasArmor(self):
        g, a, p1, p2 = createGameInMainPhase(["Goblin Chariot"], [], ["Urza's Armor"], [])

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Goblin Chariot"])

        a = postcombatMainPhase(g, a)

        assert g.obj(p2).life == 19

    def testUrzasTower(self):
        g, a, p1, p2 = createGameInMainPhase(["Urza's Tower", "Urza's Power Plant"], ["Urza's Mine"], [], [])
        a = activateAbility(g, a, "Urza's Tower", p1)
        assert g.obj(p1).manapool == "1"

        tower = findObjectInPlay(g, "Urza's Tower")
        tower.tapped = False

        printState(g, a)

        a = playLand(g, a, "Urza's Mine")
        a = activateAbility(g, a, "Urza's Tower", p1)
        assert g.obj(p1).manapool == "13"

        printState(g, a)

    def testVampiricSpirit(self):
        g, a, p1, p2 = createGameInMainPhase(["Swamp", "Swamp", "Swamp", "Swamp"], ["Vampiric Spirit"], [], [])
        a = basicManaAbility(g, a, "Swamp", p1) 
        a = basicManaAbility(g, a, "Swamp", p1) 
        a = basicManaAbility(g, a, "Swamp", p1) 
        a = basicManaAbility(g, a, "Swamp", p1) 

        a = playSpell(g, a, "Vampiric Spirit")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        assert g.obj(p1).life == 16


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

    def testWarpedDevotion(self):
        g, a, p1, p2 = createGameInMainPhase(["Raging Goblin", "Island"], ["Unsummon"], ["Warped Devotion"], [])
        a = basicManaAbility(g, a, "Island", p1)

        a = playSpell(g, a, "Unsummon")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        printState(g, a)

        a = answerQuestion(g, a, "Discard a card", "Discard")
        assert len(g.get_hand(g.obj(p1)).objects) == 0


    def testWrathOfGod(self):
        g, a, p1, p2 = createGameInMainPhase(["Plains", "Plains", "Plains", "Plains", "Angelic Page"], ["Wrath of God"], ["Raging Goblin"], [])
        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)
        a = basicManaAbility(g, a, "Plains", p1)

        a = playSpell(g, a, "Wrath of God")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        assertNoSuchObjectInPlay(g, "Angelic Page")
        assertNoSuchObjectInPlay(g, "Raging Goblin")
      
    def testWrathOfMaritLage(self):
        g, a, p1, p2 = createGameInMainPhase([], ["Wrath of Marit Lage"], ["Raging Goblin"], [])
        g.obj(p1).manapool = "UUUUU"
        a = playSpell(g, a, "Wrath of Marit Lage")
        a = payCosts(g, a)
        a = emptyStack(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        chariot = findObjectInPlay(g, "Raging Goblin")
        assert chariot.tapped

        a = endOfTurn(g, a)
        a = precombatMainPhase(g, a)

        chariot = findObjectInPlay(g, "Raging Goblin")
        assert chariot.tapped

    def testWorship(self):
        g, a, p1, p2 = createGameInMainPhase(["Goblin Chariot"], [], ["Worship", "Angelic Page"], [])
        g.obj(p2).life = 1

        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Goblin Chariot"])
        #a = declareBlockersStep(g, a)
        a = postcombatMainPhase(g, a)

        assert g.obj(p2).life == 1

    def testZombify(self):
        g, a, p1, p2 = createGameInMainPhase(["Raging Goblin", "Swamp", "Swamp", "Swamp", "Swamp"], ["Zombify"], ["Mountain"], ["Shock"])
        a = _pass(g, a)

        a = basicManaAbility(g, a, "Mountain", p2)
        a = playSpell(g, a, "Shock")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        a = basicManaAbility(g, a, "Swamp", p1) 
        a = basicManaAbility(g, a, "Swamp", p1) 
        a = basicManaAbility(g, a, "Swamp", p1) 
        a = basicManaAbility(g, a, "Swamp", p1) 

        a = playSpell(g, a, "Zombify")
        a = selectTarget(g, a, "Raging Goblin")
        a = payCosts(g, a)

        a = _pass(g, a)
        a = _pass(g, a)

        findObjectInPlay(g, "Raging Goblin")


    def testZursWeirding(self):
        g, a, p1, p2 = createGameInMainPhase(["Zur's Weirding"], [], [], [])
        a = endOfTurn(g, a)        
        a = _pass(g, a)
        a = _pass(g, a) 

        a = answerQuestion(g, a, "Player Player2 reveals cards", "OK")
        a = answerQuestion(g, a, "Player Player2 reveals cards", "OK")

        printState(g, a)      

        a = answerQuestion(g, a, "Pay pay 2 life", "Yes")
        a = answerQuestion(g, a, "Play", "Pay 2 life") 

        printState(g, a)
        a = precombatMainPhase(g, a)

        assert g.obj(p1).life == 18
        assert len(g.get_hand(g.obj(p2)).objects) == 0

        a = endOfTurn(g, a)
        a = _pass(g, a)
        a = _pass(g, a)

        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")
        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")

        printState(g, a)

        a = answerQuestion(g, a, "Pay pay 2 life", "No")
        printState(g, a)

        a = precombatMainPhase(g, a)

        assert g.obj(p1).life == 18
        assert g.obj(p2).life == 20

        assert len(g.get_hand(g.obj(p1)).objects) == 1

    def testZursWeirding2(self):
        g, a, p1, p2 = createGameInMainPhase(["Zur's Weirding"], [], ["Zur's Weirding"], [])
        a = endOfTurn(g, a)        
        a = _pass(g, a)
        a = _pass(g, a) 

        a = answerQuestion(g, a, "Player Player2 reveals cards", "OK")
        a = answerQuestion(g, a, "Player Player2 reveals cards", "OK")

        printState(g, a)      

        a = answerQuestion(g, a, "Pay pay 2 life", "Yes")
        a = answerQuestion(g, a, "Play", "Pay 2 life") 

        a = precombatMainPhase(g, a)

        assert g.obj(p1).life == 18
        assert len(g.get_hand(g.obj(p2)).objects) == 0

        a = endOfTurn(g, a)
        a = _pass(g, a)
        a = _pass(g, a)

        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")
        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")

        printState(g, a)

        a = answerQuestion(g, a, "Pay pay 2 life", "No")
        printState(g, a)

        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")
        a = answerQuestion(g, a, "Player Player1 reveals cards", "OK")

        printState(g, a)

        a = answerQuestion(g, a, "Pay pay 2 life", "No")

        a = precombatMainPhase(g, a)

        assert g.obj(p1).life == 18
        assert g.obj(p2).life == 20

        assert len(g.get_hand(g.obj(p1)).objects) == 1

    def testCombat(self):
        g, a, p1, p2 = createGameInMainPhase(["Goblin Chariot"], [], ["Severed Legion", "Maggot Carrier"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Goblin Chariot"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Severed Legion", "Maggot Carrier"], ["Goblin Chariot", "Goblin Chariot"])
      
        a = _pass(g, a)
        a = _pass(g, a)

        a = selectObject(g, a, "Severed Legion")
        a = selectObject(g, a, "Severed Legion")

        printState(g, a) 

        a = postcombatMainPhase(g, a)

        assertNoSuchObjectInPlay(g, "Severed Legion")
        assertNoSuchObjectInPlay(g, "Goblin Chariot")

    def testCombatFirstStrike(self):
        g, a, p1, p2 = createGameInMainPhase(["Tundra Wolves"], [], ["Wood Elves"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Tundra Wolves"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Wood Elves"], ["Tundra Wolves"])

        a = _pass(g, a)
        a = _pass(g, a)

        a = postcombatMainPhase(g, a)

        assertNoSuchObjectInPlay(g, "Wood Elves")
        findObjectInPlay(g, "Tundra Wolves")
      
    def testCombatFirstStrike2(self):
        g, a, p1, p2 = createGameInMainPhase(["Tundra Wolves"], [], ["Elvish Pioneer", "Wood Elves"], [])
        a = declareAttackersStep(g, a)
        a = declareAttackers(g, a, ["Tundra Wolves"])
        a = declareBlockersStep(g, a)
        a = declareBlockers(g, a, ["Elvish Pioneer", "Wood Elves"], ["Tundra Wolves", "Tundra Wolves"])

        a = _pass(g, a)
        a = _pass(g, a)

        a = selectObject(g, a, "Wood Elves")

        printState(g, a)

        a = postcombatMainPhase(g, a)

        assertNoSuchObjectInPlay(g, "Wood Elves")
        assertNoSuchObjectInPlay(g, "Tundra Wolves")
        findObjectInPlay(g, "Elvish Pioneer" )

if __name__ == "__main__":
    unittest.main()

