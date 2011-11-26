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

from objects import  *
from selectors import *
from actions import *

class Effect:
    def setText(self):
        self.text = text

    def getText(self):
        return self.text

    def getSlots(self):
        return []

class ContinuousEffect(Effect):
    def apply (self, game, obj):
        pass

class OneShotEffect(Effect):
    def resolve(self, game, obj):
        pass

    def selectTargets(self, game, player, obj):
        return True

    def validateTargets(self, game, obj):
        return True

class PlayerLooseLifeEffect(OneShotEffect):
    def __init__ (self, playerSelector, count):
        self.selector = playerSelector
        self.count = count

    def resolve(self, game, obj):
        if self.count == "X":
            count = obj.x
        else:
            count = self.count

        for player in self.selector.all(game, obj):
            game.doLoseLife(player, count)

        return True

    def __str__ (self):
        return "PlayerLooseLifeEffect(%s, %s)" % (str(self.selector), str(self.count))

class PlayerGainLifeEffect(OneShotEffect):
    def __init__ (self, playerSelector, count):
        self.selector = playerSelector
        self.count = count
    def resolve(self, game, obj):
        if self.count == "X":
            count = obj.x
        elif self.count == "that much":
            count = obj.slots["that much"]
        else:
            count = self.count

        for player in self.selector.all(game, obj):
            game.doGainLife(player, count)

        return True

    def __str__ (self):
        return "PlayerGainLifeEffect(%s, %s)" % (self.selector, self.count)



class PlayerGainLifeForEachXEffect(OneShotEffect):
    def __init__ (self, playerSelector, count, eachSelector):
        self.selector = playerSelector
        self.count = count
        self.eachSelector = eachSelector

    def resolve(self, game, obj):
        if self.count == "X":
            count = obj.x
        else:
            count = self.count

        for player in self.selector.all(game, obj):
            eachcount = len([x for x in self.eachSelector.all(game, obj)])
            game.doGainLife(player, count * eachcount)

        return True

    def __str__ (self):
        return "PlayerGainLifeForEachXEffect(%s, %s, %s)" % (self.selector, self.count, self.eachSelector)

class PlayerDiscardsCardEffect(OneShotEffect):
    def __init__ (self, playerSelector, count):
        self.selector = playerSelector
        self.count = count

    def resolve(self, game, obj):
        for player in self.selector.all(game, obj):
            assert player is not None
            for i in range(self.count):
                from process import process_discard_a_card
                process_discard_a_card(game, player.get_object())

        return True

    def __str__ (self):
        return "PlayerDiscardsCardEffect(%s, %s)" % (self.selector, self.count)

class XDealNDamageToY(OneShotEffect):
    def __init__ (self, x_selector, y_selector, n):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.count = n

    def resolve(self, game, obj):
        sources = [x for x in self.x_selector.all(game, obj)]
        assert len(sources) == 1

        source = sources[0]

        count = 0
        if self.count == "X":
            assert obj.x is not None
            count = obj.x
        else:
            count = int(self.count)

        damage = []
        for y in self.y_selector.all(game, obj):
            damage.append ( (source, y, count) )

        game.doDealDamage(damage)

        return True

    def __str__ (self):
        return "XDealNDamageToY(%s, %s, %s)" % (self.x_selector, self.y_selector, self.count)

class SingleTargetOneShotEffect(OneShotEffect):

    def __init__ (self, targetSelector, optional = False):
        self.targetSelector = targetSelector    
        self.optional = optional

    def resolve(self, game, obj):
        if self.validateTargets(game, obj):
            target = obj.targets["target"]
            self.doResolve(game, obj, target)

            return True

        return False

    def validateTargets(self, game, obj):
        from process import process_validate_target
        return process_validate_target(game, obj, self.targetSelector, obj.targets["target"])

    def selectTargets(self, game, player, obj):
        from process import process_select_target
        target = process_select_target(game, player, obj, self.targetSelector, self.optional)
        if target == None:
            return False

        obj.targets["target"] = LastKnownInformation(game, target)

        return self.doModal(game, player, obj)
    
    def doModal(self, game, player, obj):
        return True

    def doResolve(self, game, obj, target):
        pass

    def __str__ (self):
        return "SingleTargetOneShotEffect(%s)" % self.targetSelector

class XDealNDamageToTargetYEffect(SingleTargetOneShotEffect):
    def __init__ (self, sourceSelector, count, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.sourceSelector = sourceSelector
        self.count = count
           
    def doResolve(self, game, obj, target): 
        sources = [x for x in self.sourceSelector.all(game, obj)]
        assert len(sources) == 1

        source = sources[0]

        count = 0
        if self.count == "X":
            assert obj.x is not None
            count = obj.x
        else:
            count = int(self.count)

        game.doDealDamage([(source, target, count)])

    def __str__ (self):
        return "XDealNDamageToTargetYEffect(%s, %s, %s)" % (self.targetSelector, self.count, self.sourceSelector)

class XGetsNN(ContinuousEffect):
    def __init__ (self, selector, power, toughness):
        self.selector = selector
        self.power = power
        self.toughness = toughness

    def apply(self, game, obj):
        power = self.power
        toughness = self.toughness
        if power == "+X":
            power = obj.x
        elif power == "-X":
            power = - obj.x
        if toughness == "+X":
            toughness = obj.x
        elif toughness == "-X":
            toughness = - obj.x

        for o in self.selector.all(game, obj):
            o.state.power += power
            o.state.toughness += toughness

    def __str__ (self):
        return "XGetsNN(%s, %s, %s)" % (self.selector, self.power, self.toughness)

class XGetsTag(ContinuousEffect):
    def __init__ (self, selector, tag):
        self.selector = selector
        self.tag = tag

    def apply(self, game, obj):
        for o in self.selector.all(game, obj):
            o.state.tags.add (self.tag)

    def __str__ (self):
        return "XGetsTag(%s, %s)" % (self.selector, self.tag)

class TargetXGetsNNUntilEndOfTurn(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, power, toughness):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.power = power
        self.toughness = toughness

    def doResolve(self, game, obj, target):
        power = self.power
        toughness = self.toughness
        if power == "+X":
            power = obj.x
        elif power == "-X":
            power = - obj.x
        if toughness == "+X":
            toughness = obj.x
        elif toughness == "-X":
            toughness = - obj.x
        
        game.until_end_of_turn_effects.append ( (obj, XGetsNN(LKISelector(target), power, toughness)))

    def __str__ (self):
        return "TargetXGetsNNUntilEndOfTurn(%s, %s, %s)" % (self.targetSelector, self.power, self.toughness)

class XGetsNNUntilEndOfTurn(OneShotEffect):
    def __init__(self, selector, power, toughness):
        self.selector = selector
        self.power = power
        self.toughness = toughness

    def resolve(self, game, obj):
        game.until_end_of_turn_effects.append ( (obj, XGetsNN(self.selector, self.power, self.toughness)))

    def __str__ (self):
        return "XGetsNNUntilEndOfTurn(%s, %s, %s)" % (self.selector, self.power, self.toughness)

class XGetsTagUntilEndOfTurn(OneShotEffect):
    def __init__ (self, selector, tag):
        self.selector = selector
        self.tag = tag

    def resolve(self, game, obj):
        game.until_end_of_turn_effects.append ( (obj, XGetsTag(self.selector, self.tag)) )

    def __str__ (self):
        return "XGetsTagUntilEndOfTurn(%s, %s)" % (self.selector, self.tag)

class DestroyTargetX(SingleTargetOneShotEffect):
    def __init__(self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.doDestroy(target)

    def __str__ (self):
        return "DestroyTargetX(%s)" % self.targetSelector

class BuryTargetX(SingleTargetOneShotEffect):
    def __init__(self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.doBury(target)

    def __str__ (self):
        return "BuryTargetX(%s)" % self.targetSelector
       
class DestroyTargetXYGainLifeEqualsToItsPower(SingleTargetOneShotEffect):
    def __init__(self, targetSelector, playerSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.playerSelector = playerSelector

    def doResolve(self, game, obj, target):
        game.doDestroy(target)

        count = target.get_state().power
        for player in self.playerSelector.all(game, obj):
            game.doGainLife(player, count)

    def __str__ (self):
        return "DestroyTargetXYGainLifeEqualsToItsPower(%s, %s)" % (self.targetSelector, self.playerSelector)

class BuryTargetXYGainLifeEqualsToItsToughness(SingleTargetOneShotEffect):
    def __init__(self, targetSelector, playerSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.playerSelector = playerSelector

    def doResolve(self, game, obj, target):
        game.doBury(target)

        count = target.get_state().toughness
        for player in self.playerSelector.all(game, obj):
            game.doGainLife(player, count)

    def __str__ (self):
        return "BuryTargetXYGainLifeEqualsToItsToughness(%s, %s)" % (self.targetSelector, self.playerSelector)

class DoXAtEndOfCombat(OneShotEffect):
    def __init__ (self, effect):
        self.effect = effect

    def resolve(self, game, obj):
        e = game.create_effect_object(obj.get_source_lki(), obj.get_controller_id(), self.effect, obj.get_slots())
        game.end_of_combat_triggers.append (e)

        return True

    def __str__ (self):
        return "DoXAtEndOfCombat(%s)" % self.effect

class DestroyX(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        for o in self.selector.all(game, obj):
            game.doDestroy(o)

        return True

    def __str__ (self):
        return "DestroyX(%s)" % self.selector

class XDontUntapDuringItsControllersUntapStep(ContinuousEffect):
    def __init__ (self, selector):
        self.selector = selector

    def apply(self, game, obj):
        for o in self.selector.all(game, obj):
            o.state.tags.add ("does not untap")

    def __str__ (self):
        return "XDontUntapDuringItsControllersUntapStep(%s)" % self.selector

class TargetXDiscardsACard(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, count):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.count = count
    
    def doResolve(self, game, obj, target):
        from process import process_discard_a_card
        for i in range(self.count):
            process_discard_a_card(game, target.get_object())

    def __str__ (self):
        return "TargetXDiscardsACard(%s, %d)" % (self.targetSelector, self.count)

class TargetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, cardSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.cardSelector = cardSelector

    def doResolve(self, game, obj, target):
        from process import process_reveal_hand_and_discard_a_card
        process_reveal_hand_and_discard_a_card(game, target.get_object(), game.objects[obj.get_state().controller_id], self.cardSelector, obj)

    def __str__ (self):
        return "TargetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard(%s, %s)" % (self.targetSelector, self.cardSelector)

class XMayPutYFromHandIntoPlay(OneShotEffect):
    def __init__ (self, x_selector, y_selector, tapped = False):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.tapped = tapped

    def resolve(self, game, obj):

        for player in self.x_selector.all(game, obj):
            actions = []
            for card in game.get_hand(player).objects:
                if self.y_selector.contains(game, obj, card):
                    _p = Action ()
                    _p.object = card
                    _p.text = "Put " + str(card) + " into play"
                    actions.append (_p)

            if len(actions) > 0:

                _pass = PassAction (player)
                _pass.text = "Pass"

                actions = [_pass] + actions

                _as = ActionSet (game, player, "Choose a card to put into play", actions)
                a = game.input.send (_as)
 
                a.object.tapped = self.tapped
                game.doZoneTransfer (a.object, game.get_in_play_zone())

        return True

    def __str__ (self):
        return "XMayPutYFromHandIntoPlay(%s, %s)" % (self.x_selector, self.y_selector)

class YouMayTapTargetX(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector, True)

    def doResolve(self, game, obj, target):
        game.doTap(target.get_object())

    def __str__ (self):
        return "YouMayTapTargetX(%s)" % self.targetSelector

class YouMayPayCostIfYouDoY(OneShotEffect):
    def __init__ (self, cost, effectText):
        self.cost = cost

        from rules import effectRules

        self.effectText = effectText

    def resolve(self, game, obj):
        controller = game.objects[obj.get_state().controller_id]
        _pay = Action()
        _pay.text = "Yes"
        
        _notpay = Action()
        _notpay.text = "No"

        _as = ActionSet (game, controller, ("Pay %s to %s?" % (", ".join(map(str, self.cost)), self.effectText)), [_pay, _notpay])
        a = game.input.send(_as)

        if a == _pay:
            from process import process_pay_cost, process_trigger_effect
            if process_pay_cost(game, controller, obj, self.cost):
                process_trigger_effect(game, obj, self.effectText, {})
     
        return True

    def __str__ (self):
        return "YouMayPayCostIfYouDoY(%s, %s)" % (self.cost, self.effectText)

class PreventNextNDamageThatWouldBeDealtToTargetXThisTurn(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, n):
        SingleTargetOneShotEffect.__init__(self, targetSelector, True)
        self.n = n

    def doResolve(self, game, obj, target):
        n = self.n
        if n == "X":
            n = obj.x
        game.doPreventNextDamge(target.get_object(), n)

    def __str__ (self):
        return "PreventNextNDamageThatWouldBeDealtToTargetXThisTurn(%s, %s)" % (self.targetSelector, str(self.n))

class AddXToYourManaPool(OneShotEffect):
    def __init__ (self, mana):
        self.mana = mana

    def resolve(self, game, obj):
        game.objects[obj.get_state().controller_id].manapool += self.mana

        return True

    def __str__ (self):
        return "AddXToYourManaPool(%s)" % self.mana

class RegenerateX(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        for o in self.selector.all(game, obj):
            game.doRegenerate(o)

        return True

    def __str__ (self):
        return "RegenerateX(%s)" % self.selector

class XSearchLibraryForXAndPutThatCardIntoPlay(OneShotEffect):
    def __init__ (self, x_selector, y_selector, tapped = False):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.tapped = tapped

    def resolve(self, game, obj):

        for player in self.x_selector.all(game, obj):
            actions = []
            for card in game.get_library(player).objects:
                if self.y_selector.contains(game, obj, card):
                    _p = Action ()
                    _p.object = card
                    _p.text = "Put " + str(card) + " into play"
                    actions.append (_p)

            if len(actions) > 0:

                _pass = PassAction (player)
                _pass.text = "Pass"

                actions = [_pass] + actions

                _as = ActionSet (game, player, "Choose a card to put into play", actions)
                a = game.input.send (_as)
 
                a.object.tapped = self.tapped
                game.doZoneTransfer (a.object, game.get_in_play_zone())

                game.doShuffle(game.get_library(player))

        return True

    def __str__ (self):
        return "XSearchLibraryForXAndPutThatCardIntoPlay(%s, %s)" % (self.x_selector, self.y_selector)

class SacrificeXUnlessYouCost(OneShotEffect):
    def __init__ (self, selector, costs):
        self.selector = selector
        self.costs = costs

    def resolve(self, game, obj):
        controller = game.objects[obj.get_state().controller_id]
        _pay = Action()
        _pay.text = "Pay %s" % str(map(str, self.costs))
        
        _notpay = Action()
        _notpay.text = "Sacrifice %s" % self.selector

        _as = ActionSet (game, controller, "Choose", [_pay, _notpay])
        a = game.input.send(_as)

        if a == _pay:
            from process import process_pay_cost
            if process_pay_cost(game, controller, obj, self.costs):
                return
            # else, sacrifice...
             
        for o in self.selector.all(game, obj):
            game.doSacrifice(o)

        return True
        
    def __str__ (self):
        return "SacrificeXUnlessYouCost(%s, %s)" % (self.selector, str(map(str,self.costs)))


class ChooseEffect(Effect):

    def __init__ (self, effect1text, effect2text):
        self.effect1text = effect1text
        self.effect2text = effect2text

        from rules import effectRules
        self.effect1 = effectRules(effect1text).effect
        self.effect2 = effectRules(effect2text).effect

    def resolve(self, game, obj):
        if obj.modal == 1:
            return self.effect1.resolve(game, obj)
        elif obj.modal == 2:
            return self.effect2.resolve(game, obj)
        else:
            raise Exception("Not modal")

    def selectTargets(self, game, player, obj):

        _option1 = Action()
        _option1.text = str(self.effect1text)
        
        _option2 = Action()
        _option2.text = str(self.effect2text)

        _as = ActionSet (game, player, "Choose", [_option1, _option2])
        a = game.input.send(_as)

        if a == _option1:
            obj.modal = 1
            effect = self.effect1
        else:
            obj.modal = 2
            effect = self.effect2

        return effect.selectTargets(game, player, obj)

    def validateTargets(self, game, obj):
        if obj.modal == 1:
            return self.effect1.validateTargets(game, obj)
        elif obj.modal == 2:
            return self.effect2.validateTargets(game, obj)
        else:
            raise Exception("Not modal")

    def __str__ (self):
        return "ChooseEffect(%s, %s)" % (self.effect1text, self.effect2text)

class TargetXGainLife(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, count):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.count = count
    
    def doResolve(self, game, obj, target):
        if self.count == "X":
            count = obj.x
        else:
            count = self.count

        game.doGainLife(target.get_object(), count)

    def __str__ (self):
        return "TargetXGainLife(%s, %d)" % (self.targetSelector, self.count)

class LookAtTopNCardsOfYourLibraryPutThemBackInAnyOrder(OneShotEffect):
    def __init__ (self, n):
        self.n = n

    def resolve(self, game, obj):
        player = game.objects[obj.get_controller_id()]
        library = game.get_library(player)

        if self.n == "X":
            n = obj.x
        else:
            n = self.n

        n = int(n)

        cards = []
        for i in range(n):
           if len(library.objects) > 0:
                cards.append(library.objects.pop())

        while len(cards) > 0:
            options = []
            for card in cards:
                _option = Action()
                _option.text = str(card)
                _option.object = card
        
            _as = ActionSet (game, player, "Put card on top of your library", options)
            a = game.input.send(_as)

            cards.remove (a.object)
            library.objects.append(a.object)

    def __str__ (self):
        return "LookAtTopNCardsOfYourLibraryPutThemBackInAnyOrder(%s)" % self.n

class CounterTargetXUnlessItsControllerPaysCost(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector, costs):
        SingleTargetOneShotEffect.__init__(self, targetSelector)
        self.costs = costs
    
    def doResolve(self, game, obj, target):

        controller = game.objects[target.get_state().controller_id]
        _pay = Action()
        _pay.text = "Pay %s" % str(map(str, self.costs))
        
        _notpay = Action()
        _notpay.text = "Counter %s" % target

        _as = ActionSet (game, controller, "Choose", [_pay, _notpay])
        a = game.input.send(_as)

        if a == _pay:
            from process import process_pay_cost
            if process_pay_cost(game, controller, obj, self.costs):
                return
            # else, counter.
        game.doCounter(target)

    def __str__ (self):
        return "CounterTargetXUnlessItsControllerPaysCost(%s, %s)" % (self.targetSelector, str(map(str,self.costs)))

class CounterTargetX(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        game.doCounter(target)

    def __str__ (self):
        return "CounterTargetX(%s)" % (self.targetSelector)

class ReturnXToOwnerHands(OneShotEffect):
    def __init__ (self, selector):
        self.selector = selector

    def resolve(self, game, obj):
        for o in self.selector.all(game, obj):
            owner = game.objects[o.get_object().owner_id]
            hand = game.get_hand(owner)
            game.doZoneTransfer(o.get_object(), hand)

        return True

    def __str__ (self):
        return "ReturnXToOwnerHands(%s)" % self.selector

class ReturnTargetXToOwnerHands(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        owner = game.objects[target.get_object().owner_id]
        hand = game.get_hand(owner)
        game.doZoneTransfer(target.get_object(), hand)

    def __str__ (self):
        return "ReturnTargetXToOwnerHands(%s)" % self.targetSelector
      
class YouMayTapOrUntapTargetX(SingleTargetOneShotEffect):
    def __init__ (self, targetSelector):
        SingleTargetOneShotEffect.__init__(self, targetSelector)

    def doResolve(self, game, obj, target):
        if obj.modal == "tap":
            game.doTap(target)
        elif obj.modal == "untap":
            game.doUntap(target)

    def doModal(self, game, player, obj):
        _pass = PassAction(player)

        _tap = Action()
        _tap.text = "Tap"

        _untap = Action()
        _untap.text = "Untap"
        
        _as = ActionSet (game, player, "You may tap or untap target", [_pass, _tap, _untap])
        a = game.input.send(_as)

        if a.text == "Tap":
            obj.modal = "tap"
        elif a.text == "Untap":
            obj.modal = "untap"
        else:
            return False

        return True

    def __str__ (self):
        return "YouMayTapOrUntapTargetX(%s)" % (self.targetSelector)

class YouMayDrawACard(OneShotEffect):
    def __init__ (self):
        pass

    def resolve(self, game, obj):
        controller = game.objects[obj.get_state().controller_id]
        _yes = Action()
        _yes.text = "Yes"
        
        _no = Action()
        _no.text = "No"

        _as = ActionSet (game, controller, ("Draw a card?"), [_yes, _no])
        a = game.input.send(_as)

        if a == _yes:
            game.doDrawCard(controller)
     
        return True

    def __str__ (self):
        return "YouMayDrawACard()"

class DrawACard(OneShotEffect):
    def __init__ (self):
        pass

    def resolve(self, game, obj):
        controller = game.objects[obj.get_state().controller_id]
        game.doDrawCard(controller)
        return True

    def __str__ (self):
        return "DrawACard()"


