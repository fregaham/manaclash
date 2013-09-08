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
from actions import AbilityAction, PassAction, PayCostAction, QueryNumber

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

    def testSeismicAssault(self):
        g, a, p1, p2 = createGameInMainPhase(["Seismic Assault"], ["Mountain"], [], [])
        a = activateAbility(g, a, "Seismic Assault", p1)
        a = selectTarget(g, a, "Player2")
        a = payCost(g, a, "Discard")
        a = selectObject(g, a, "Mountain")
        a = emptyStack(g, a)

        assert g.obj(p2).life == 18


if __name__ == "__main__":
    unittest.main()

