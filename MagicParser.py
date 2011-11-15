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
from cost import *
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
manaCost = N("manaCost")
basicLand = N("basicLand")
costs = N("costs")

NUMBER = N("NUMBER")

r = [
    R("sorceryOrInstantRules", [effect], lambda t, x:BasicNonPermanentRules(x)),
    R("effectRules", [effect], lambda t, x:EffectRules(x)),
    R("permanentRules", [N("abilities")], lambda t, x:BasicPermanentRules(x)),
    R("permanentRules", [""], lambda t:BasicPermanentRules([])),
    R("abilities", [N("ability"), ";", N("abilities")], lambda t,x,y:[x] + y),
    R("abilities", [N("ability"), ", ", N("abilities")], lambda t,x,y:[x] + y),
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
    R("effect", [N("buryTargetXYGainLifeEqualsToItsToughness")], id),
    R("effect", [N("destroyXAtEndOfCombat")], id),
    R("effect", [N("dontUntapDuringItsControllersUntapStep")], id),
    R("effect", [N("targetXDiscardsACard")], id),
    R("effect", [N("targetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard")], id),

    R("enchantmentRules", ["enchant ", selector, ";", effect], lambda t,s,e:EnchantPermanentRules(s, ContinuousEffectStaticAbility(e))),
    R("enchantmentRules", ["enchant ", selector, " (target a ", selector, " as you cast this. this card enters the battlefield attached to that ", selector, ".);", effect], lambda t,s,s2,s3,e:EnchantPermanentRules(s, ContinuousEffectStaticAbility(e))),

    R("enchantmentRules", ["enchant ", selector, ";", N("ability")], lambda t,s,a:EnchantPermanentRules(s, a)),
    R("enchantmentRules", ["enchant ", selector, " (target a ", selector, " as you cast this. this card enters the battlefield attached to that ", selector, ".);", N("ability")], lambda t,s,s2,s3,a:EnchantPermanentRules(s, a)),

    R("enchantmentRules", [N("abilities")], lambda t,a:BasicPermanentRules(a)),
    R("enchantmentRules", [N("effect")], lambda t,e:BasicPermanentRules([ContinuousEffectStaticAbility(e)])),

    R("continuousAbility", ["flying"], lambda t:TagAbility("flying")),
    R("continuousAbility", ["flying (this creature can't be blocked except by creatures with flying or reach.)"], lambda t:TagAbility("flying")),

    R("continuousAbility", ["fear"], lambda t:TagAbility("fear")),
    R("continuousAbility", ["fear (this creature can't be blocked except by artifact creatures and/or black creatures.)"], lambda t:TagAbility("fear")),
    R("ability", ["you may have SELF assign its combat damage as though it weren't blocked."], lambda t:TagAbility("x-sneaky")),

    R("ability", ["first strike (this creature deals combat damage before creatures without first strike.)"], lambda t:TagAbility("first strike")),
    R("ability", ["vigilance"], lambda t:TagAbility("vigilance")),

    R("triggeredAbility", [N("whenXComesIntoPlayDoEffectAbility")], id),
    R("triggeredAbility", [N("whenXDealsDamageToYDoEffectAbility")], id),
    R("triggeredAbility", [N("whenXDealsCombatDamageToYDoEffectAbility")], id),
    R("triggeredAbility", [N("whenXBlocksOrBecomesBlockedByYDoEffectAbility")], id),
    R("triggeredAbility", [N("whenXDiscardsACardDoEffectAbility")], id),

    R("when", ["when"], lambda t:t),
    R("when", ["whenever"], lambda t:t),

    R("whenXComesIntoPlayDoEffectAbility", [N("when"), " ", selector, " comes into play, ", N("effectText")], lambda t, w, s, e: WhenXComesIntoPlayDoEffectAbility(s, e)),
    R("whenXComesIntoPlayDoEffectAbility", [N("when"), " ", selector, " enters the battlefield, ", N("effectText")], lambda t, w, s, e: WhenXComesIntoPlayDoEffectAbility(s, e)),

    R("deal", ["deal"], lambda t:t),
    R("deal", ["deals"], lambda t:t),

    R("cast", ["casts"], lambda t:t),
    R("cast", ["cast"], lambda t:t),

    R("whenXDealsDamageToYDoEffectAbility", [N("when"), " ", selector, " ", N("deal"), " damage to ", selector, ", ", N("effectText")], lambda t,w,x,d,y,e:WhenXDealsDamageToYDoEffectAbility(x,y,e)),

    R("whenXDealsCombatDamageToYDoEffectAbility", [N("when"), " ", selector, " ", N("deal"), " combat damage to ", selector, ", ", N("effectText")], lambda t,w,x,d,y,e:WhenXDealsCombatDamageToYDoEffectAbility(x,y,e)),

    R("ability", [N("when"), " ", selector, " ", N("deal"), " damage, ", N("effectText")], lambda t,w,x,d,e:WhenXDealsDamageDoEffectAbility(x,e)),

    R("a", ["a"], lambda t:t),
    R("a", ["an"], lambda t:t),
    R("whenXBlocksOrBecomesBlockedByYDoEffectAbility", [N("when"), " ", N("selector"), " blocks or becomes blocked by ", N("a"), " ", N("selector"), ", ", N("effectText")], lambda t,w,x,a,y,e:WhenXBlocksOrBecomesBlockedByYDoEffectAbility(x,y,e)),

    R("triggeredAbility", [N("when"), " ", selector, " attacks, ", N("effectText")], lambda t,w,s,e: WhenXAttacksDoEffectAbility(s,e)),

    R("whenXDiscardsACardDoEffectAbility", [N("when"), " ", N("selector"), " discards a card, ", N("effectText")], lambda t,w,x,e:WhenXDiscardsACardDoEffectAbility(x,e)),

    R("triggeredAbility", [N("when"), " ", selector, " ", N("cast"), " ", selector, ", ", N("effectText")], lambda t,w,x,c,y,e:WhenXCastsYDoEffectAbility(x,y,e)),

    R("activatedAbility", [N("tappingActivatedAbility")], id),

    R("tappingActivatedAbility", [costs, ", {t}: ", N("effectText")], lambda t, c, e: TapCostDoEffectAbility(c, e)),
    R("tappingActivatedAbility", [costs, ", {t}: ", N("effectText"), " activate this ability only during your turn."], lambda t, c, e: SelfTurnTapCostDoEffectAbility(c, e)),

    R("tappingActivatedAbility", ["{t}: ", N("effectText")], lambda t, e: TapCostDoEffectAbility([], e)),
    R("tappingActivatedAbility", ["{t}: ", N("effectText"), " activate this ability only during your turn."], lambda t, e: SelfTurnTapCostDoEffectAbility([], e)),

    R("ability", [costs, ": ", N("effectText")], lambda t, c, e: CostDoEffectAbility(c, e)),

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
    R("effect", [N("selector"), " ", N("get"), " ", N("number"), "/", N("number"), " until end of turn."], lambda t,x,g,a,b:XGetsNNUntilEndOfTurn(x, a, b)),

    R("dontUntapDuringItsControllersUntapStep", [N("selector"), " doesn't untap during its controller's untap step."], lambda t,x:XDontUntapDuringItsControllersUntapStep(x)),

    R("xGetsNN", [N("selector"), " ", N("get"), " ", N("number"), "/", N("number"), "."], lambda t, x,g,a,b: XGetsNN(x,a,b)),
    
    R("destroyTargetX", ["destroy target ", N("selector"), "."], lambda t,x: DestroyTargetX(x)),
    R("buryTargetX", ["destroy target ", N("selector"), ". it can't be regenerated."], lambda t,x: BuryTargetX(x)),

    R("destroyTargetXYGainLifeEqualsToItsPower", ["destroy target ", selector, ". ", selector, " ", gain, " life equal to its power."], lambda t,x,y,g: DestroyTargetXYGainLifeEqualsToItsPower(x, y)),

    R("buryTargetXYGainLifeEqualsToItsToughness", ["destroy target ", selector, ". it can't be regenerated. ", selector, " ", gain, " life equal to its toughness."], lambda t,x,y,g: BuryTargetXYGainLifeEqualsToItsToughness(x, y)),

    R("destroyXAtEndOfCombat", ["destroy ", N("selectorText"), " at end of combat."], lambda t,x: DoXAtEndOfCombat("destroy " + x + ".")),

    R("destroyX", ["destroy ", selector, "."], lambda t,x: DestroyX(x)),

    R("discard", ["discards"], lambda t:t),
    R("discard", ["discard"], lambda t:t),

    R("targetXDiscardsACard", ["target ", selector, " ", discard, " ", numberOfCards, "."], lambda t,x,d,n: TargetXDiscardsACard(x, n)),

    R("playerDiscardsACardEffect", [selector, " ", discard, " ", numberOfCards, "."], lambda t,x,d,n: PlayerDiscardsCardEffect(x, n)),

    R("targetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard", ["target ", selector, " reveals his or her hand. you choose ", selector, " from it. that player discards that card."], lambda t,x,y: TargetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard(x, y)),

    R("effect", [selector, " may put ", selector, " from your hand onto the battlefield."], lambda t, x, y: XMayPutYFromHandIntoPlay(x, y, False)),
    R("effect", [selector, " may put ", selector, " from your hand onto the battlefield tapped."], lambda t, x, y: XMayPutYFromHandIntoPlay(x, y, True)),
    R("effect", [selector, " may put ", selector, " from his or her hand onto the battlefield."], lambda t, x, y: XMayPutYFromHandIntoPlay(x, y, False)),
    R("effect", [selector, " may put ", selector, " from his or her hand onto the battlefield tapped."], lambda t, x, y: XMayPutYFromHandIntoPlay(x, y, True)),

    R("effect", ["search your library for ", selector, " and put that card onto the battlefield. then shuffle your library."], lambda t,x:XSearchLibraryForXAndPutThatCardIntoPlay(YouSelector(), x, False)),
    R("effect", ["search your library for ", selector, " and put that card onto the battlefield tapped. then shuffle your library."], lambda t,x:XSearchLibraryForXAndPutThatCardIntoPlay(YouSelector(), x, True)),

    R("effect", ["add ", manaCost, " to your mana pool."], lambda t, m: AddXToYourManaPool(m)),

    R("effect", ["sacrifice ", selector, " unless you ", costs, "."], lambda t,s,c: SacrificeXUnlessYouCost(s, c)),

    R("effect", ["regenerate ", selector, ". (the next time this creature would be destroyed this turn, it isn't. instead tap it, remove all damage from it, and remove it from combat.)"], lambda t,s: RegenerateX(s)),
    
    R("effect", ["all creatures able to block ", selector, " do so."], lambda t,s: XGetsTag(s, "lure")),

    R("effect", ["you may tap target ", selector, "."], lambda t,s: YouMayTapTargetX(s)),

    R("effect", ["target ", selector, " ", N("gain"), " ", N("number"), " life."], lambda t,x,l,n: TargetXGainLife(x, n)),

    R("effect", ["prevent the next ", number, " damage that would be dealt to target ", selector, " this turn."], lambda t,n,s: PreventNextNDamageThatWouldBeDealtToTargetXThisTurn(s, n)),
    R("effect", ["choose one - target player gains ", number, " life; or prevent the next ", number, " damage that would be dealt to target creature or player this turn."], lambda t,n1,n2: ChooseEffect("target player gains " + str(n1) + " life.", "prevent the next " + str(n2) +" damage that would be dealt to target creature or player this turn.")),

    R("effect", [selector, " can't attack or block."], lambda t,s:XGetsTag(s, "can't attack or block")),

    R("effect", ["you may ", costs, ". if you do, ", N("effectText")], lambda t,c,e: YouMayPayCostIfYouDoY(c, e)),

    R("effect", ["look at the top ", number, " cards of your library, then put them back in any order."], lambda t,n: LookAtTopNCardsOfYourLibraryPutThemBackInAnyOrder(n)),

    R("effect", ["counter target ", selector, " unless its controller ", costs, "."], lambda t,x,c: CounterTargetXUnlessItsControllerPaysCost(x,c)),

    R("effect", ["return ", selector, " to its owner's hand."], lambda t,x: ReturnXToOwnerHands(x)),

    R("costs", [N("cost")], lambda t, c: [c]),
    R("costs", [N("cost"), ", ", N("costs")], lambda t, c, cs:[c] + cs),
    R("costs", ["sacrifice ", number, " ", selector], lambda t,n,s: ([SacrificeSelectorCost(s)] * n)),

    R("cost", [N("manaCost")], lambda t, m: ManaCost(m)),
    R("cost", ["pay ", N("manaCost")], lambda t, m: ManaCost(m)),
    R("cost", ["pays ", N("manaCost")], lambda t, m: ManaCost(m)),
    R("cost", ["tap an untapped ", selector], lambda t, s: TapSelectorCost(s)),
    R("cost", ["sacrifice ", selector], lambda t, s: SacrificeSelectorCost(s)),

    R("selectorText", [selector], lambda t,x:t),

    R("selector", [N("basicSelector"), " or ", selector], lambda t,x,y:OrSelector(x,y)),
    R("selector", [N("basicSelector")], id),

    R("basicSelector", ["player"], lambda t:AllPlayersSelector()),
    R("basicSelector", ["a player"], lambda t:AllPlayersSelector()),
    R("basicSelector", ["each player"], lambda t:AllPlayersSelector()),
    R("basicSelector", ["each other player"], lambda t:EachOtherPlayerSelector()),
    R("basicSelector", ["that player"], lambda t:ThatPlayerSelector()),
    R("basicSelector", ["you"], lambda t:YouSelector()),
    R("basicSelector", ["it"], lambda t:ItSelector()),
    R("basicSelector", ["SELF"], lambda t:SelfSelector()),
    R("basicSelector", ["creature"], lambda t:CreatureSelector()),
    R("basicSelector", ["creature with flying"], lambda t:CreatureWithFlyingSelector()),
    R("basicSelector", ["a creature you control"], lambda t:CreatureYouControlSelector()),
    R("basicSelector", ["creature you control"], lambda t:CreatureYouControlSelector()),
    R("basicSelector", ["creatures you control"], lambda t:CreatureYouControlSelector()),
    R("basicSelector", ["that creature"], lambda t:ThatCreatureSelector()),
    R("basicSelector", ["creature or player"], lambda t:CreatureOrPlayerSelector()),
    R("basicSelector", ["attacking or blocking creature"], lambda t:AttackingOrBlockingCreatureSelector()),
    R("basicSelector", ["attacking creature"], lambda t:AttackingCreatureSelector()),
    R("basicSelector", ["creature attacking you"], lambda t:CreatureAttackingYouSelector()),
    R("basicSelector", ["non", color, " creature"], lambda t,c:NonColorCreatureSelector(c)),
    R("basicSelector", ["enchanted creature"], lambda t:EnchantedCreatureSelector()),
    R("basicSelector", ["opponent"], lambda t:OpponentSelector()),
    R("basicSelector", ["an opponent"], lambda t:OpponentSelector()),
    R("basicSelector", ["a card"], lambda t:CardSelector()),
    R("basicSelector", ["a creature card"], lambda t:CreatureCardSelector()),
    R("basicSelector", ["a basic land card"], lambda t:BasicLandCardSelector()),
    R("basicSelector", ["a ", basicLand, " card"], lambda t,x:SubTypeCardSelector(x)),
    R("basicSelector", [basicLand], lambda t,x:SubTypeSelector(x)),
    R("basicSelector", ["artifact"], lambda t:ArtifactSelector()),
    R("basicSelector", ["enchantment"], lambda t:EnchantmentSelector()),
    R("basicSelector", ["a ", color, " spell"], lambda t,c:ColorSpellSelector(c)),
    R("basicSelector", ["spell"], lambda t:SpellSelector()),
    
    R("numberOfCards", ["a card"], lambda t:1),

    R("manaCost", [N("manaCostElement"), N("manaCost")], lambda t,e,c: e + c),
    R("manaCost", [N("manaCostElement")], lambda t,e: e),

    R("manaCostElement", ["{", NUMBER, "}"], lambda t,n: n),
    R("manaCostElement", ["{g}"], lambda t: "G"),
    R("manaCostElement", ["{r}"], lambda t: "R"),
    R("manaCostElement", ["{b}"], lambda t: "B"),
    R("manaCostElement", ["{w}"], lambda t: "W"),
    R("manaCostElement", ["{u}"], lambda t: "U"),

    R("number", ["one"], lambda t: 1),
    R("number", ["two"], lambda t: 2),
    R("number", ["three"], lambda t: 3),
    R("number", ["four"], lambda t: 4),
    R("number", ["five"], lambda t: 5),
    R("number", ["six"], lambda t: 6),
    R("number", ["seven"], lambda t: 7),
    R("number", ["eight"], lambda t: 8),
    R("number", ["nine"], lambda t: 9),

    R("number", [NUMBER], lambda t,n: int(n)),
    R("number", ['x'], lambda t: 'X'),
    R("number", ['-', NUMBER], lambda t,n: -int(n)),
    R("number", ['-x'], lambda t: '-X'),
    R("number", ['+', NUMBER], lambda t,n: int(n)),
    R("number", ['+x'], lambda t: '+X'),
    R("number", ["that much"], lambda t: "that much"),

    R("color", ["red"], lambda t:t),
    R("color", ["green"], lambda t:t),
    R("color", ["blue"], lambda t:t),
    R("color", ["white"], lambda t:t),
    R("color", ["black"], lambda t:t),

    R("basicLand", ["island"], lambda t:t),
    R("basicLand", ["forest"], lambda t:t),
    R("basicLand", ["swamp"], lambda t:t),
    R("basicLand", ["plains"], lambda t:t),
    R("basicLand", ["mountain"], lambda t:t),

    R("basicLand", ["islands"], lambda t:"island"),
    R("basicLand", ["forests"], lambda t:"forest"),
    R("basicLand", ["swamps"], lambda t:"swamp"),
    R("basicLand", ["plains"], lambda t:"plains"),
    R("basicLand", ["mountains"], lambda t:"mountain"),

    R("NUMERAL", ["0"], lambda t:t),
    R("NUMERAL", ["1"], lambda t:t),
    R("NUMERAL", ["2"], lambda t:t),
    R("NUMERAL", ["3"], lambda t:t),
    R("NUMERAL", ["4"], lambda t:t),
    R("NUMERAL", ["5"], lambda t:t),
    R("NUMERAL", ["6"], lambda t:t),
    R("NUMERAL", ["7"], lambda t:t),
    R("NUMERAL", ["8"], lambda t:t),
    R("NUMERAL", ["9"], lambda t:t),
    R("NUMBER", [N("NUMERAL")], lambda t,n:n),
    R("NUMBER", [N("NUMERAL"),N("NUMBER")], lambda t,n,m:n+m)
]

def magic_parser(label, text):
    for result in parse(r, label, text):
        return result

    return None


