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


from abilities import *
from effects import *
from selectors import *
from rules import *
from Parser import *

def R(lhs, rhs, action):
    return Rule(lhs, rhs, action)

def N(label):
    return nt(label)

id = lambda t, x:x

effect = N("effect")
selector = N("selector")
gain = N("gain")
discard = N("discard")
color = N("color")
number = N("number")
numberOfCards = N("numberOfCards")

NUMBER = N("NUMBER")

r = [
    R("sorceryOrInstantRules", [effect], lambda t, x:BasicNonPermanentRules(x)),
    R("effectRules", [effect], lambda t, x:EffectRules(x)),
    R("permanentRules", [N("abilities")], lambda t, x:BasicPermanentRules(x)),
    R("permanentRules", [""], lambda t:BasicPermanentRules([])),
    R("abilities", [N("ability"), ";", N("abilities")], lambda t,x,y:[x] + y),
    R("abilities", [N("ability")], lambda t,x:[x]),

    R("ability", [N("continuousAbility")], id),
    R("ability", [N("triggeredAbility")], id),
    R("ability", [N("activatedAbility")], id),

    R("effectText", [effect], lambda t,e: t),

    R("effect", [N("playerLooseLifeEffect")], id),
    R("effect", [N("playerGainLifeEffect")], id),
    R("effect", [N("playerGainLifeForEachXEffect")], id),
    R("effect", [N("playerDiscardsACardEffect")], id),
    R("effect", [N("xDealNDamageToTargetYEffect")], id),
    R("effect", [N("xDealNDamageToY")], id),
    R("effect", [N("xGetsNN")], id),
    R("effect", [N("targetXGetsNNUntilEndOfTurn")], id),
    R("effect", [N("destroyTargetX")], id),
    R("effect", [N("buryTargetX")], id),
    R("effect", [N("destroyX")], id),
    R("effect", [N("destroyTargetXYGainLifeEqualsToItsPower")], id),
    R("effect", [N("destroyXAtEndOfCombat")], id),
    R("effect", [N("dontUntapDuringItsControllersUntapStep")], id),
    R("effect", [N("targetXDiscardsACard")], id),
    R("effect", [N("targetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard")], id),

    R("enchantmentRules", ["enchant ", selector, ";", effect], lambda t,s,e:EnchantPermanentRules(s, ContinuousEffectStaticAbility(e))),
    R("enchantmentRules", [N("abilities")], lambda t,a:BasicPermanentRules(a)),

    R("continuousAbility", ["flying"], lambda t:TagAbility("flying")),
    R("continuousAbility", ["fear"], lambda t:TagAbility("fear")),
    R("continuousAbility", ["fear (this creature can't be blocked except by artifact creatures and/or black creatures.)"], lambda t:TagAbility("fear")),

    R("triggeredAbility", [N("whenXComesIntoPlayDoEffectAbility")], id),
    R("triggeredAbility", [N("whenXDealsDamageToYDoEffectAbility")], id),
    R("triggeredAbility", [N("whenXBlocksOrBecomesBlockedByYDoEffectAbility")], id),
    R("triggeredAbility", [N("whenXDiscardsACardDoEffectAbility")], id),

    R("when", ["when"], lambda t:t),
    R("when", ["whenever"], lambda t:t),

    R("whenXComesIntoPlayDoEffectAbility", [N("when"), " ", selector, " comes into play, ", N("effectText")], lambda t, w, s, e: WhenXComesIntoPlayDoEffectAbility(s, e)),
    R("whenXComesIntoPlayDoEffectAbility", [N("when"), " ", selector, " enters the battlefield, ", N("effectText")], lambda t, w, s, e: WhenXComesIntoPlayDoEffectAbility(s, e)),

    R("deal", ["deal"], lambda t:t),
    R("deal", ["deals"], lambda t:t),

    R("whenXDealsDamageToYDoEffectAbility", [N("when"), " ", selector, " ", N("deal"), " damage to ", selector, ", ", N("effectText")], lambda t,w,x,d,y,e:WhenXDealsDamageToYDoEffectAbility(x,y,e)),

    R("a", ["a"], lambda t:t),
    R("a", ["an"], lambda t:t),
    R("whenXBlocksOrBecomesBlockedByYDoEffectAbility", [N("when"), " ", N("selector"), " blocks or becomes blocked by ", N("a"), " ", N("selector"), ", ", N("effectText")], lambda t,w,x,a,y,e:WhenXBlocksOrBecomesBlockedByYDoEffectAbility(x,y,e)),

    R("whenXDiscardsACardDoEffectAbility", [N("when"), " ", N("selector"), " discards a card, ", N("effectText")], lambda t,w,x,e:WhenXDiscardsACardDoEffectAbility(x,e)),

    R("activatedAbility", [N("tappingActivatedAbility")], id),

    R("tappingActivatedAbility", [N("manaCost"), ", {t}: ", N("effectText")], lambda t, m, e: TapCostDoEffectAbility(m, e)),

    R("tappingActivatedAbility", ["{t}: ", N("effectText")], lambda t, e: TapCostDoEffectAbility("", e)),

    R("lose", ["lose"], lambda t:t),
    R("lose", ["loses"], lambda t:t),

    R("playerLooseLifeEffect", [N("selector"), " ", N("lose"), " ", N("number"), " life."], lambda t,x,l,n: PlayerLooseLifeEffect(x, n)),

    R("gain", ["gain"], lambda t:t),
    R("gain", ["gains"], lambda t:t),

    R("playerGainLifeEffect", [N("selector"), " ", N("gain"), " ", N("number"), " life."], lambda t,x,l,n: PlayerGainLifeEffect(x, n)),

    R("playerGainLifeForEachXEffect", [N("selector"), " ", N("gain"), " ", N("number"), " life for each ", N("selector"), "."], lambda t,x,g,n,y: PlayerGainLifeForEachXEffect(x, n, y)),

    R("xDealNDamageToTargetYEffect", [N("selector"), " ", N("deal"), " ", N("number"), " damage to target ", N("selector"), "."], lambda t,x,d,n,y:XDealNDamageToTargetYEffect(x, n, y)),

    R("xDealNDamageToY", [N("selector"), " ", N("deal"), " ", N("number"), " damage to ", N("selector"), "."], lambda t,x,d,n,y:XDealNDamageToY(x, y, n)),

    R("get", ["get"], lambda t:t),
    R("get", ["gets"], lambda t:t),
    R("targetXGetsNNUntilEndOfTurn", ["target ", N("selector"), " ", N("get"), " ", N("number"), "/", N("number"), " until end of turn."], lambda t,x,g,a,b:TargetXGetsNNUntilEndOfTurn(x, a, b)),

    R("dontUntapDuringItsControllersUntapStep", [N("selector"), " doesn't untap during its controller's untap step,"], lambda t,x:XDontUntapDuringItsControllersUntapStep(x)),

    R("xGetsNN", [N("selector"), " ", N("get"), " ", N("number"), "/", N("number"), "."], lambda t, x,g,a,b: XGetsNN(x,a,b)),
    
    R("destroyTargetX", ["destroy target ", N("selector"), "."], lambda t,x: DestroyTargetX(x)),
    R("buryTargetX", ["destroy target ", N("selector"), ". it can't be regenerated."], lambda t,x: BuryTargetX(x)),

    R("destroyTargetXYGainLifeEqualsToItsPower", ["destroy target ", selector, ". ", selector, " ", gain, " life equal to its power."], lambda t,x,y,g: DestroyTargetXYGainLifeEqualsToItsPower(x, y)),
    
    R("destroyXAtEndOfCombat", ["destroy ", N("selectorText"), " at end of combat."], lambda t,x: DoXAtEndOfCombat("destroy " + x)),

    R("destroyX", ["destroy ", selector, "."], lambda t,x: DestroyX(x)),

    R("discard", ["discards"], lambda t:t),
    R("discard", ["discard"], lambda t:t),

    R("targetXDiscardsACard", ["target ", selector, " ", discard, " ", numberOfCards, "."], lambda t,x,d,n: TargetXDiscardsACard(x, n)),

    R("playerDiscardsACardEffect", [selector, " ", discard, " ", numberOfCards, "."], lambda t,x,d,n: PlayerDiscardsCardEffect(x, n)),

    R("targetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard", ["target ", selector, " reveals his or her hand. you choose ", selector, " from it. that player discards that card."], lambda t,x,y: TargetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard(x, y)),

    R("selectorText", [selector], lambda t,x:t),

    R("selector", ["a player"], lambda t:AllPlayersSelector()),
    R("selector", ["each player"], lambda t:AllPlayersSelector()),
    R("selector", ["that player"], lambda t:ThatPlayerSelector()),
    R("selector", ["you"], lambda t:YouSelector()),
    R("selector", ["SELF"], lambda t:SelfSelector()),
    R("selector", ["creature"], lambda t:CreatureSelector()),
    R("selector", ["that creature"], lambda t:ThatCreatureSelector()),
    R("selector", ["creature or player"], lambda t:CreatureOrPlayerSelector()),
    R("selector", ["attacking or blocking creature"], lambda t:AttackingOrBlockingCreatureSelector()),
    R("selector", ["attacking creature"], lambda t:AttackingCreatureSelector()),
    R("selector", ["creature attacking you"], lambda t:CreatureAttackingYouSelector()),
    R("selector", ["non", color, " creature"], lambda t,c:NonColorCreatureSelector(c)),
    R("selector", ["enchanted creature"], lambda t:EnchantedCreatureSelector()),
    R("selector", ["opponent"], lambda t:OpponentSelector()),
    R("selector", ["an opponent"], lambda t:OpponentSelector()),
    R("selector", ["a card"], lambda t:AllSelector()),

    R("numberOfCards", ["a card"], lambda t:1),

    R("manaCost", [N("manaCostElement"), N("manaCost")], lambda t,e,c: e + c),
    R("manaCost", [N("manaCostElement")], lambda t,e: e),

    R("manaCostElement", ["{", NUMBER, "}"], lambda t,n: n),

    R("number", [NUMBER], lambda t,n: int(n)),
    R("number", ['x'], lambda t: 'X'),
    R("number", ['-', NUMBER], lambda t,n: -int(n)),
    R("number", ['-x'], lambda t: '-X'),
    R("number", ['+', NUMBER], lambda t,n: int(n)),
    R("number", ['+x'], lambda t: '+X'),

    R("color", ["red"], lambda t:t),
    R("color", ["green"], lambda t:t),
    R("color", ["blue"], lambda t:t),
    R("color", ["white"], lambda t:t),
    R("color", ["black"], lambda t:t),

    R("NUMBER", ["0"], lambda t:t),
    R("NUMBER", ["1"], lambda t:t),
    R("NUMBER", ["2"], lambda t:t),
    R("NUMBER", ["3"], lambda t:t),
    R("NUMBER", ["4"], lambda t:t),
    R("NUMBER", ["5"], lambda t:t),
    R("NUMBER", ["6"], lambda t:t),
    R("NUMBER", ["7"], lambda t:t),
    R("NUMBER", ["8"], lambda t:t),
    R("NUMBER", ["9"], lambda t:t)
]

def magic_parser(label, text):
    for result in parse(r, label, text):
        return result

    return None


