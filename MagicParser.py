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

from numberof import *
from abilities import *
from effects import *
from selectors import *
from conditions import *
from dialogs import *
from rules import *
from cost import *
from Parser import *

def R(lhs, rhs, action):
    return Rule(lhs, rhs, action)

def N(label):
    return nt(label)

id = lambda t, x:x

creatureType = N("creatureType")
effect = N("effect")
selector = N("selector")
gain = N("gain")
discard = N("discard")
color = N("color")
number = N("number")
Number = N("Number")
numberOfCards = N("numberOfCards")
manaCost = N("manaCost")
basicLand = N("basicLand")
costs = N("costs")
cardType = N("cardType")
tag = N("tag")
condition = N("condition")
dialog = N("dialog")
counter = N("counter")

NUMBER = N("NUMBER")

r = [
    R("sorceryOrInstantRules", [effect], lambda t, x:BasicNonPermanentRules(x)),
    R("sorceryOrInstantRules", [effect, ";", N("abilities")], lambda t, e, ax:BasicNonPermanentRules(e, ax)),

    R("effectRules", [effect], lambda t, x:EffectRules(x)),
    R("effectRules", [N("graveyardEffect")], lambda t, x:EffectRules(x)),

    R("nonBasicLandRules", [N("abilities")], lambda t, x:NonBasicLandRules(x)),
    R("nonBasicLandRules", [""], lambda t:NonBasicLandRules([])),

    R("permanentRules", [N("abilities")], lambda t, x:BasicPermanentRules(x)),
    R("permanentRules", [""], lambda t:BasicPermanentRules([])),
    R("abilities", [N("ability"), ";", N("abilities")], lambda t,x,y:[x] + y),
    R("abilities", [N("ability"), ", ", N("abilities")], lambda t,x,y:[x] + y),
    R("abilities", [N("ability")], lambda t,x:[x]),

    R("ability", [N("continuousAbility")], id),
    R("ability", [N("conditionalContinuousAbility")], id),
    R("ability", [N("triggeredAbility")], id),
    R("ability", [N("activatedAbility")], id),

    R("effectText", [effect], lambda t,e: t),
    R("manaEffectText", [N("manaEffect")], lambda t,e: t),
    R("graveyardEffectText", [N("graveyardEffect")], lambda t,e: t),

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

    R("continuousAbility", ["haste"], lambda t:TagAbility("haste")),
    R("continuousAbility", ["haste (this creature can attack and {t} as soon as it comes under your control.)"], lambda t:TagAbility("haste")),
    R("continuousAbility", ["haste (this creature can attack the turn it comes under your control.)"], lambda t:TagAbility("haste")),

    R("continuousAbility", ["fear"], lambda t:TagAbility("fear")),
    R("continuousAbility", ["fear (this creature can't be blocked except by artifact creatures and/or black creatures.)"], lambda t:TagAbility("fear")),
    R("continuousAbility", ["you may have SELF assign its combat damage as though it weren't blocked."], lambda t:TagAbility("x-sneaky")),
    R("continuousAbility", [effect], lambda t,e:ContinuousEffectStaticAbility(e)),

    R("continuousAbility", ["SELF can't block."], lambda t:TagAbility("can't block")),

    R("conditionalContinuousAbility", ["if ", condition, ", ", effect], lambda t,c,e:ConditionalContinuousEffectStaticAbility(c,e)),

    R("ability", ["first strike (this creature deals combat damage before creatures without first strike.)"], lambda t:TagAbility("first strike")),
    R("ability", [tag], lambda t,tag:TagAbility(tag)),
    R("ability", ["SELF is unblockable."], lambda t:TagAbility("unblockable")),
    R("ability", ["SELF can block any number of creatures."], lambda t:TagAbility("can block any number of creatures")),

    R("abilities", [selector, " ", N("get"), " ", N("number"), "/", N("number"), " and have ", tag, "."], lambda t,x,g,a,b,tag:[ContinuousEffectStaticAbility(XGetsNN(x,a,b)), ContinuousEffectStaticAbility(XGetsTag(x, tag))]),
    R("abilities", [selector, " ", N("get"), " ", N("number"), "/", N("number"), " and have ", tag, ". (they're unblockable as long as defending player controls ", selector, ".)"], lambda t,x,g,a,b,tag,s:[ContinuousEffectStaticAbility(XGetsNN(x,a,b)), ContinuousEffectStaticAbility(XGetsTag(x, tag))]),

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

    R("triggeredAbility", [N("when"), " ", selector, " is dealt damage, ", N("effectText")], lambda t,w,x,e:WhenXDealsDamageToYDoEffectAbility(AllSelector(),x,e)),

    R("ability", [N("when"), " ", selector, " ", N("deal"), " damage, ", N("effectText")], lambda t,w,x,d,e:WhenXDealsDamageDoEffectAbility(x,e)),

    R("a", ["a"], lambda t:t),
    R("a", ["an"], lambda t:t),
    R("whenXBlocksOrBecomesBlockedByYDoEffectAbility", [N("when"), " ", N("selector"), " blocks or becomes blocked by ", N("a"), " ", N("selector"), ", ", N("effectText")], lambda t,w,x,a,y,e:WhenXBlocksOrBecomesBlockedByYDoEffectAbility(x,y,e)),

    R("triggeredAbility", [N("when"), " ", selector, " attacks, ", N("effectText")], lambda t,w,s,e: WhenXAttacksDoEffectAbility(s,e)),
    R("triggeredAbility", [N("when"), " ", selector, " blocks, ", N("effectText")], lambda t,w,s,e: WhenXBlocksDoEffectAbility(s,e)),
    R("triggeredAbility", [N("when"), " ", selector, " attacks or blocks, ", N("effectText")], lambda t,w,s,e: WhenXAttacksOrBlocksDoEffectAbility(s,e)),

    R("whenXDiscardsACardDoEffectAbility", [N("when"), " ", N("selector"), " discards a card, ", N("effectText")], lambda t,w,x,e:WhenXDiscardsACardDoEffectAbility(x,e)),

    R("triggeredAbility", [N("when"), " ", selector, " is put into a graveyard from the battlefield, ", N("effectText")], lambda t,w,x,e:WhenXIsPutIntoGraveyardFromPlayDoEffectAbility(x,e)),

    R("triggeredAbility", [N("when"), " ", selector, " ", N("cast"), " ", selector, ", ", N("effectText")], lambda t,w,x,c,y,e:WhenXCastsYDoEffectAbility(x,y,e)),

    R("triggeredAbility", [N("when"), " ", selector, " causes ", selector, " to discard ", selector, ", ", N("effectText")], lambda t,w,x,y,z,e:WhenXCausesYToDiscardZ(x,y,z,e)),

    R("triggeredAbility", [N("when"), " ", selector, " becomes tapped, ", N("effectText")], lambda t,w,x,e: WhenXBecomesTappedDoEffectAbility(x, e)),
    R("triggeredAbility", [N("when"), " ", selector, " is tapped for mana, ", N("manaEffectText")], lambda t,w,x,e: WhenXBecomesTappedForManaDoManaEffectAbility(x, e)),

    R("triggeredAbility", ["as SELF enters the battlefield, ", dialog], lambda t,d: AsSelfComesIntoPlayAnswerDialog(d)),

    R("triggeredAbility", [N("when"), " ", selector, " becomes the target of a ", selector, ", ", N("effectText"), " (it won't be affected by the spell or ability.)"], lambda t,w,x,y,e:WhenXBecomesTargetOfYDoEffectAbility(x,y,e)),

    R("triggeredAbility", [N("when"), " ", selector, " control no other ", selector, ", ", N("effectText")], lambda t,w,x,y,e:WhenXControlsNoOtherYDoEffectAbility(x,y,e)),
    R("triggeredAbility", ["at the beginning of each player's upkeep, ", N("effectText")], lambda t,e:AtTheBeginningOfEachPlayerssUpkeepDoEffectAbility(e)),

    R("activatedAbility", [N("tappingActivatedAbility")], id),
    R("activatedAbility", [N("tappingActivatedManaAbility")], id),

    R("tappingActivatedAbility", [costs, ", {t}: ", N("effectText")], lambda t, c, e: TapCostDoEffectAbility(c, e)),
    R("tappingActivatedAbility", [costs, ", {t}, ", costs, ": ", N("effectText")], lambda t, c1, c2, e: TapCostDoEffectAbility(c1 + c2, e)),
    R("tappingActivatedAbility", ["{t}, ", costs, ": ", N("effectText")], lambda t, c, e: TapCostDoEffectAbility(c, e)),

    R("tappingActivatedAbility", [costs, ", {t}: ", N("effectText"), " activate this ability only during your turn."], lambda t, c, e: SelfTurnTapCostDoEffectAbility(c, e)),

    R("tappingActivatedAbility", ["{t}: ", N("effectText")], lambda t, e: TapCostDoEffectAbility([], e)),
    R("tappingActivatedAbility", ["{t}: ", N("effectText"), " activate this ability only during your turn."], lambda t, e: SelfTurnTapCostDoEffectAbility([], e)),

    R("tappingActivatedManaAbility", ["{t}: ", N("manaEffectText")], lambda t, e: TapDoManaEffectAbility(e)),

    R("ability", [costs, ": ", N("graveyardEffectText"), " activate this ability only during your upkeep."], lambda t,c,e: CostDoEffectGraveyardUpkeepAbility(c, e)),

    R("ability", [costs, ": ", N("effectText"), " activate this ability only any time you could cast a sorcery."], lambda t,c,e: CostDoEffectAsSorceryAbility(c, e)),
    R("ability", [costs, ": ", N("effectText")], lambda t, c, e: CostDoEffectAbility(c, e)),

    R("lose", ["lose"], lambda t:t),
    R("lose", ["loses"], lambda t:t),

    R("playerLooseLifeEffect", [N("selector"), " ", N("lose"), " ", N("number"), " life."], lambda t,x,l,n: PlayerLooseLifeEffect(x, n)),

    R("gain", ["gain"], lambda t:t),
    R("gain", ["gains"], lambda t:t),

    R("playerGainLifeEffect", [N("selector"), " ", N("gain"), " ", N("number"), " life."], lambda t,x,l,n: PlayerGainLifeEffect(x, n)),

    R("playerGainLifeForEachXEffect", [N("selector"), " ", N("gain"), " ", N("number"), " life for each ", N("selector"), "."], lambda t,x,g,n,y: PlayerGainLifeForEachXEffect(x, n, y)),

    R("xDealNDamageToTargetYEffect", [N("selector"), " ", N("deal"), " ", N("Number"), " damage to target ", N("selector"), "."], lambda t,x,d,n,y:XDealNDamageToTargetYEffect(x, n, y)),

    R("effect", [selector, " ", N("deal"), " damage equal to ", N("Number"), " to target ", selector, "."], lambda t,x,d,n,y:XDealNDamageToTargetYEffect(x, n, y)),

    R("effect", [N("selector"), " ", N("deal"), " ", N("Number"), " damage to ", N("selector"), "."], lambda t,x,d,n,y:XDealNDamageToY(x, y, n)),
    R("effect", [N("selector"), " ", N("deal"), " ", N("Number"), " damage to each creature and each player."], lambda t,x,d,n:XDealNDamageToY(x, CreatureOrPlayerSelector(), n)),
    R("effect", [N("selector"), " ", N("deal"), " damage to ", selector, " equal to the ",  N("Number"), "."], lambda t,x,d,y,n:XDealNDamageToY(x, y, n)),

    R("get", ["get"], lambda t:t),
    R("get", ["gets"], lambda t:t),
    R("targetXGetsNNUntilEndOfTurn", ["target ", N("selector"), " ", N("get"), " ", N("number"), "/", N("number"), " until end of turn."], lambda t,x,g,a,b:TargetXGetsNNUntilEndOfTurn(x, a, b)),
    R("effect", [N("selector"), " ", N("get"), " ", N("number"), "/", N("number"), " until end of turn."], lambda t,x,g,a,b:XGetsNNUntilEndOfTurn(x, a, b)),
    R("effect", [N("selector"), " gains flying until end of turn."], lambda t,x:XGetsTagUntilEndOfTurn(x, "flying")),

    R("effect", ["target ", selector, " becomes the color of your choice until end of turn."], lambda t,x:TargetXBecomesTheColorOfYourChoiceUntilEndOfTurn(x)),

    R("dontUntapDuringItsControllersUntapStep", [N("selector"), " doesn't untap during its controller's untap step."], lambda t,x:XGetsTag(x, "does not untap")),
    R("dontUntapDuringItsControllersUntapStep", [N("selector"), " don't untap during their controllers' untap steps."], lambda t,x:XGetsTag(x, "does not untap")),

    R("xGetsNN", [N("selector"), " ", N("get"), " ", N("number"), "/", N("number"), "."], lambda t, x,g,a,b: XGetsNN(x,a,b)),
    R("effect", [selector, " ", N("get"), " ", N("number"), "/", N("number"), " for each ", selector, "."], lambda t,x,g,a,b,y:XGetsNNForEachY(x,a,b,y)),
    R("effect", [selector, " ", N("get"), " ", N("number"), "/", N("number"), " for each other creature on the battlefield that shares at least one creature type with it. (for example, if two goblin warriors and a goblin shaman are on the battlefield, each gets +2/+2.)"], lambda t,x,g,a,b:XGetsNNForEachOtherCreatureInPlayThatSharesAtLeastOneCreatureTypeWithIt(x,a,b)),
    
    R("destroyTargetX", ["destroy target ", N("selector"), "."], lambda t,x: DestroyTargetX(x)),
    R("buryTargetX", ["destroy target ", N("selector"), ". it can't be regenerated."], lambda t,x: BuryTargetX(x)),

    R("destroyTargetXYGainLifeEqualsToItsPower", ["destroy target ", selector, ". ", selector, " ", gain, " life equal to its power."], lambda t,x,y,g: DestroyTargetXYGainLifeEqualsToItsPower(x, y)),

    R("buryTargetXYGainLifeEqualsToItsToughness", ["destroy target ", selector, ". it can't be regenerated. ", selector, " ", gain, " life equal to its toughness."], lambda t,x,y,g: BuryTargetXYGainLifeEqualsToItsToughness(x, y)),

    R("destroyXAtEndOfCombat", ["destroy ", N("selectorText"), " at end of combat."], lambda t,x: DoXAtEndOfCombat("destroy " + x + ".")),

    R("destroyX", ["destroy ", selector, "."], lambda t,x: DestroyX(x)),
    R("destroyX", ["destroy all ", selector, "."], lambda t,x: DestroyX(x)),

    R("effect", ["destroy ", selector, ". it can't be regenerated."], lambda t,x:BuryX(x)),

    R("discard", ["discards"], lambda t:t),
    R("discard", ["discard"], lambda t:t),

    R("effect", ["target ", selector, " ", discard, " ", numberOfCards, "."], lambda t,x,d,n: TargetXDiscardsACard(x, n)),
    R("effect", ["target ", selector, " discards a card for each ", selector, "."], lambda t,x,y:TargetXDiscardsACard(x,EachSelectorNumber(y))),

    R("playerDiscardsACardEffect", [selector, " ", discard, " ", numberOfCards, "."], lambda t,x,d,n: PlayerDiscardsCardEffect(x, n)),

    R("targetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard", ["target ", selector, " reveals his or her hand. you choose ", selector, " from it. that player discards that card."], lambda t,x,y: TargetXRevealsHandYouChooseYCardThatPlayerDiscardsThatCard(x, y)),

    R("effect", [selector, " may put ", selector, " from your hand onto the battlefield."], lambda t, x, y: XMayPutYFromHandIntoPlay(x, y, False)),
    R("effect", [selector, " may put ", selector, " from your hand onto the battlefield tapped."], lambda t, x, y: XMayPutYFromHandIntoPlay(x, y, True)),
    R("effect", [selector, " may put ", selector, " from his or her hand onto the battlefield."], lambda t, x, y: XMayPutYFromHandIntoPlay(x, y, False)),
    R("effect", [selector, " may put ", selector, " from his or her hand onto the battlefield tapped."], lambda t, x, y: XMayPutYFromHandIntoPlay(x, y, True)),

    R("effect", ["search your library for ", selector, " and put that card onto the battlefield. then shuffle your library."], lambda t,x:XSearchLibraryForXAndPutThatCardIntoPlay(YouSelector(), x, False)),
    R("effect", ["search your library for ", selector, " and put that card onto the battlefield tapped. then shuffle your library."], lambda t,x:XSearchLibraryForXAndPutThatCardIntoPlay(YouSelector(), x, True)),
    R("effect", ["search your library for ", selector, " and put that card into your hand. then shuffle your library."], lambda t,x:XSearchLibraryForXAndPutItIntoHand(YouSelector(), x)),
    R("effect", ["search your library for a ", selector, ", reveal that card, and put it into your hand. then shuffle your library."], lambda t,x:XSearchLibraryForXAndPutItIntoHand(YouSelector(), x, True)),
    
    R("effect", ["sacrifice ", selector, " unless you ", costs, "."], lambda t,s,c: SacrificeAllXUnlessYouCost(s, c)),
    R("effect", ["sacrifice all ", selector, "."], lambda t,s: SacrificeAllX(s)),
    R("effect", ["sacrifice SELF."], lambda t: SacrificeAllX(SelfSelector())),
    R("effect", ["sacrifice a ", selector, "."], lambda t,x: XSacrificeY(YouSelector(), x)),
    R("effect", [selector, " sacrifices ", selector, "."], lambda t,x,y:XSacrificeY(x,y)),

    R("effect", ["regenerate ", selector, ". (the next time this creature would be destroyed this turn, it isn't. instead tap it, remove all damage from it, and remove it from combat.)"], lambda t,s: RegenerateX(s)),
    R("effect", ["regenerate ", selector, "."], lambda t,s: RegenerateX(s)),
   
    R("effect", ["all creatures able to block ", selector, " do so."], lambda t,s: XGetsTag(s, "lure")),

    R("effect", ["you may tap target ", selector, "."], lambda t,s: YouMayTapTargetX(s)),
    R("effect", ["tap target ", selector, "."], lambda t,s: TapTargetX(s)),

    R("effect", ["target ", selector, " ", N("gain"), " ", N("number"), " life."], lambda t,x,l,n: TargetXGainLife(x, n)),

    R("effect", ["prevent the next ", number, " damage that would be dealt to target ", selector, " this turn."], lambda t,n,s: PreventNextNDamageThatWouldBeDealtToTargetXThisTurn(s, n)),
    R("effect", ["prevent all combat damage that would be dealt this turn."], lambda t:PreventAllCombatDamageThatWouldBeDealtThisTurn()),

    R("effect", ["choose one - target player gains ", number, " life; or prevent the next ", number, " damage that would be dealt to target creature or player this turn."], lambda t,n1,n2: ChooseEffect("target player gains " + str(n1) + " life.", "prevent the next " + str(n2) +" damage that would be dealt to target creature or player this turn.")),

    R("effect", [selector, " can't attack or block."], lambda t,s:XGetsTag(s, "can't attack or block")),
    R("effect", [selector, " can't attack."], lambda t,s:XGetsTag(s, "can't attack")),
    R("effect", [selector, " can't be countered."], lambda t,s:XGetsTag(s, "can't be countered")),
    R("effect", [selector, " can't be blocked except by walls."], lambda t,s:XGetsTag(s, "can't be blocked except by walls")),
    R("effect", [selector, " have shroud. (you can't be the target of spells or abilities.)"], lambda t,s:XGetsTag(s, "shroud")),

    R("effect", [selector, " has fear. (it can't be blocked except by artifact creatures and/or black creatures.)"], lambda t,s:XGetsTag(s, "fear")),
    R("effect", [selector, " has flying. (it can't be blocked except by creatures with flying or reach.)"], lambda t,s:XGetsTag(s, "flying")),

    R("effect", ["target ", selector, " gains ", tag, " until end of turn."], lambda t,x,g:TargetXGetsTagUntilEndOfTurn(x,g)),

    R("effect", ["you may ", costs, ". if you do, ", N("effectText")], lambda t,c,e: YouMayPayCostIfYouDoY(c, e)),

    R("effect", ["look at the top ", number, " cards of your library, then put them back in any order."], lambda t,n: LookAtTopNCardsOfYourLibraryPutThemBackInAnyOrder(n)),

    R("effect", ["counter target ", selector, " unless its controller ", costs, "."], lambda t,x,c: CounterTargetXUnlessItsControllerPaysCost(x,c)),
    R("effect", ["counter target ", selector, "."], lambda t,x: CounterTargetX(x)),

    R("effect", ["change the target of target ", selector, "."], lambda t,x: ChangeTargetOfTargetX(x)),

    R("effect", ["return ", selector, " to its owner's hand."], lambda t,x: ReturnXToOwnerHands(x)),
    R("effect", ["return target ", selector, " to its owner's hand."], lambda t,x: ReturnTargetXToOwnerHands(x)),
    R("effect", ["return target ", selector, " to your hand."], lambda t,x: ReturnTargetXToOwnerHands(x)),
    R("effect", ["you may return target ", selector, " to your hand."], lambda t,x: ReturnTargetXToOwnerHands(x, True)),
    R("effect", ["return ", selector, " to their owners' hands."], lambda t,x: ReturnXToOwnerHands(x)),
    R("effect", ["return all ", selector, " to their owners' hands."], lambda t,x: ReturnXToOwnerHands(x)),

    R("effect", ["you may tap or untap target ", selector, "."], lambda t,x: YouMayTapOrUntapTargetX(x)),

    R("draw", ["draw"], lambda t:t),
    R("draw", ["draws"], lambda t:t),

    R("effect", [selector, " may draw a card."], lambda t,x: XMayDrawACard(x)),
    R("effect", ["draw ", N("numberOfCards"), "."], lambda t,n: DrawCards(YouSelector(), n)),
    R("effect", ["draw a card for each ", selector, "."], lambda t,x: DrawCards(YouSelector(), EachSelectorNumber(x))),
    R("effect", ["target ", selector, " draws ", N("numberOfCards"), "."], lambda t,x,n: TargetXDrawCards(x, n)),

    R("effect", [selector, " ", N("draw"), " ", N("numberOfCards"), " and ", selector, " ", N("lose"), " ", N("number"), " life."], lambda t,x,d,n,y,l,m: XAndY(DrawCards(x,n), PlayerLooseLifeEffect(y, m))),
    R("effect", ["draw ", N("numberOfCards"), ", then discard ", N("numberOfCards"), "."], lambda t,n,m:XAndY(DrawCards(YouSelector(), n), PlayerDiscardsCardEffect(YouSelector(), m))),

    R("effect", ["if ", selector, " would deal damage to ", selector,", prevent ", number, " of that damage."], lambda t,x,y,n:IfXWouldDealDamageToYPreventNOfThatDamage(x,y,n)),
    R("effect", ["if ", selector, " would deal damage to ", selector,", it deals double that damage to that ", selector, " instead."], lambda t,x,y,_:IfXWouldDealDamageToYItDealsDoubleThatDamageToThatYInstead(x,y)),

    R("effect", [selector, " costs ", manaCost, " less to cast."], lambda t,s,c:XCostsNLessToCast(s,c)),
    R("effect", [selector, " cost ", manaCost, " less to cast."], lambda t,s,c:XCostsNLessToCast(s,c)),
    R("effect", [selector, " costs ", manaCost, " more to cast except during its controller's turn."], lambda t,s,c:XCostsNMoreToCastExceptDuringItsControllersTurn(s,c)),

    R("effect", ["if target ", selector, " has more cards in hand than you, draw cards equal to the difference."], lambda t,s:IfTargetPlayerHasMoreCardsInHandThanYouDrawCardsEqualToTheDifference(s)),

    R("effect", [selector, "'s power and toughness are each equal to ", Number, "."], lambda t,x,n:XPowerAndToughnessAreEachEqualToN(x,n)),
    R("effect", [selector, "'s power is equal to the ", Number, " and its toughness is equal to that number plus ", Number, "."], lambda t,x,n,m:XPowerIsNAndToughnessIsM(x,n,NumberSum(n,m))),

    R("effect", [selector, " skips his or her next combat phase."], lambda t,s:PlayerSkipsNextCombatPhase(s)),

    R("effect", [selector, " are ", basicLand, "."], lambda t,x,l: XIsBasicLandType(x,l)),

    R("effect", ["reveal the top ", number, " cards of your library. put all ", selector, " revealed this way into your hand and the rest on the bottom of your library in any order."], lambda t,n,s: RevealTopNCardsOfYourLibraryPutAllXIntoYourHandAndTheRestOnTheBottomOfYourLibraryInAnyOrder(n, s)),

    R("effect", ["search target ", selector, "'s library for a ", selector, " and put that card onto the battlefield under your control. then that player shuffles his or her library."], lambda t,x,y:SearchTargetXsLibraryForYAndPutThatCardInPlayUnderYourControl(x,y)),

    R("effect", ["reveal the top card of your library. if it's a ", selector, ", put it onto the battlefield. otherwise, put it into your graveyard."], lambda t,y: XRevealTopCardOfHisLibraryIfItIsYPutItInPlayOtherwisePutItIntoGraveyard(YouSelector(), y)),

    R("effect", ["the next time a ", selector, " of your choice would deal damage to ", selector, " this turn, prevent that damage."], lambda t,x,y: TheNextTimeXOfYourChoiceWouldDealDamageToYThisTurnPreventThatDamage(x,y)),

    R("effect", [selector, " control ", selector, "."], lambda t,x,y:XControlsY(x,y)),

    R("effect", ["put a ", counter, " counter on ", selector, "."], lambda t,c,s:PutXCounterOnY(c, s)),

    R("effect", ["at the beginning of each player's draw step, if ", condition, ", that player draws an additional card."], lambda t,c:AtTheBeginningOfEachPlayerDrawStepIfXThatPlayerDrawsAnAdditionalCard(c)),

    R("effect", ["untap all ", selector, "."], lambda t,s: UntapAllX(s)),

    R("effect", [selector, " is a ", Number, "/", Number, " ", color, " ", creatureType, " creature that's still a land."], lambda t,x,n,m,c,p:XIsANNCTCreature(x,n,m,c,p)),
    R("effect", ["all ", selector, " become ", Number, "/", Number, " creatures until end of turn. they're still lands."], lambda t,x,n,m:AllXBecomeNNCreaturesUntilEndOfTurn(x,n,m)),

    R("effect", ["you and target ", selector, " each flip a coin. SELF deals ", Number, " damage to each player whose coin comes up tails. repeat this process until both players' coins come up heads on the same flip."], lambda t,x,n:YouAndTargetXEachFlipCoinSELFDealsNDamageToEachPlayerWhoseCoinComesUpTailsRepeatThisProcessUntilBothPlayersCoinsComeUpHeadsOnTheSameFlip(x, n)),

    R("effect", ["target ", selector, " puts the top ", Number, " cards of his or her library into his or her graveyard."], lambda t,x,n:TargetXPutsTheTopNCardsOfLibraryIntoGraveyard(x, n)),

    R("effect", ["change the text of target ", selector, " by replacing all instances of one color word with another or one basic land type with another. (for example, you may change \"nonblack creature\" to \"nongreen creature\" or \"forestwalk\" to \"islandwalk.\" this effect lasts indefinitely.)"], lambda t,x:ChangeTheTextOfTargetXByReplacingAllInstancesOfOneColorWordWithAnotherOrOneBasicLandTypeWithAnother(x)),

    R("manaEffect", ["add ", manaCost, " to your mana pool."], lambda t, m: XAddXToYourManaPool(YouSelector(),m)),
    R("manaEffect", ["add ", number, " mana of any color to your mana pool."], lambda t,n: XAddNManaOfAnyColorToYourManapool(YouSelector(),n)),
    R("manaEffect", [selector, " adds ", number, " mana of any color to his or her mana pool (in addition to the mana the land produces)."], lambda t,x,n: XAddNManaOfAnyColorToYourManapool(x,n)),
    R("manaEffect", ["add ", manaCost, " or ", manaCost, " to your mana pool."], lambda t,m1,m2: XAddOneOfTheseManaToYourManaPool(YouSelector(), [m1,m2])),

    R("graveyardEffect", ["return SELF from your graveyard to your hand."], lambda t: ReturnXToOwnerHands(SelfSelector())),

    R("condition", [selector, " have ", number, " or less life"], lambda t,s,n:IfXHasNOrLessLife(s, n)),
    R("condition", ["SELF is untapped"], lambda t:ExistsUntappedX(SelfSelector())),

    R("dialog", ["choose a creature type."], lambda t:ChooseCreatureType()),

    R("costs", [N("cost")], lambda t, c: [c]),
    R("costs", [N("cost"), ", ", N("costs")], lambda t, c, cs:[c] + cs),
    R("costs", ["sacrifice ", number, " ", selector], lambda t,n,s: ([SacrificeSelectorCost(s)] * n)),

    R("cost", [N("manaCost")], lambda t, m: ManaCost(m)),
    R("cost", ["pay ", N("manaCost")], lambda t, m: ManaCost(m)),
    R("cost", ["pays ", N("manaCost")], lambda t, m: ManaCost(m)),
    R("cost", ["tap an untapped ", selector], lambda t, s: TapSelectorCost(s)),
    R("cost", ["sacrifice ", selector], lambda t, s: SacrificeSelectorCost(s)),
    R("cost", ["pay ", number, " life"], lambda t,n:PayLifeCost(n)),
    R("cost", ["pay half your life rounded up"], lambda t:PayHalfLifeRoundedUpCost()),

    R("selectorText", [selector], lambda t,x:t),

    R("selector", [N("basicSelector"), " or ", selector], lambda t,x,y:OrSelector(x,y)),
    R("selector", [N("basicSelector")], id),

    R("basicSelector", ["player"], lambda t:AllPlayersSelector()),
    R("basicSelector", ["a player"], lambda t:AllPlayersSelector()),
    R("basicSelector", ["a source"], lambda t:AllSelector()),
    R("basicSelector", ["each player"], lambda t:AllPlayersSelector()),
    R("basicSelector", ["each other player"], lambda t:EachOtherPlayerSelector()),
    R("basicSelector", ["that player"], lambda t:ThatPlayerSelector()),
    R("basicSelector", ["you"], lambda t:YouSelector()),
    R("basicSelector", ["it"], lambda t:ItSelector()),
    R("basicSelector", ["its controller"], lambda t:ItsControllerSelector()),

    R("basicSelector", ["SELF"], lambda t:SelfSelector()),
    R("basicSelector", ["creature"], lambda t:CreatureSelector()),
    R("basicSelector", ["creatures with power greater than ", Number], lambda t,n:CreatureWithPowerGreaterThanNSelector(n)),
    R("basicSelector", ["creature with power ", Number, " or greater"], lambda t,n:CreatureWithPowerNOrGreaterSelector(n)),
    R("basicSelector", ["all creatures"], lambda t:CreatureSelector()),
    R("basicSelector", ["creatures"], lambda t:CreatureSelector()),
    R("basicSelector", ["a creature"], lambda t:CreatureSelector()),
    R("basicSelector", ["each creature"], lambda t:CreatureSelector()),
    R("basicSelector", ["creatures on the battlefield"], lambda t:CreatureSelector()),
    R("basicSelector", ["creature with flying"], lambda t:CreatureWithFlyingSelector()),
    R("basicSelector", ["a creature you control"], lambda t:CreatureYouControlSelector()),
    R("basicSelector", ["creature you control"], lambda t:CreatureYouControlSelector()),
    R("basicSelector", ["creatures you control"], lambda t:CreatureYouControlSelector()),
    R("basicSelector", ["all creatures you control"], lambda t:CreatureYouControlSelector()),
    R("basicSelector", ["that creature"], lambda t:ThatCreatureSelector()),
    R("basicSelector", ["that creature's controller"], lambda t:ThatCreaturesControllerSelector()),

    R("basicSelector", ["that land"], lambda t:ThatLandSelector()),
    R("basicSelector", ["that land's controller"], lambda t:ThatLandsControllerSelector()),
    R("basicSelector", ["the sacrificed creature"], lambda t:SacrificedCreatureSelector()),
    R("basicSelector", ["creatures of the chosen type"], lambda t:CreatureOfTheChosenType()),
    R("basicSelector", ["a creature or player"], lambda t:CreatureOrPlayerSelector()),
    R("basicSelector", ["creature or player"], lambda t:CreatureOrPlayerSelector()),
    R("basicSelector", ["attacking or blocking creature"], lambda t:AttackingOrBlockingCreatureSelector()),
    R("basicSelector", ["attacking creature"], lambda t:AttackingCreatureSelector()),
    R("basicSelector", ["creature attacking you"], lambda t:CreatureAttackingYouSelector()),
    R("basicSelector", ["non", color, " creature"], lambda t,c:NonColorCreatureSelector(c)),
    R("basicSelector", [color, " permanent"], lambda t,c:ColorPermanentSelector(c)),
    R("basicSelector", [color, " permanents"], lambda t,c:ColorPermanentSelector(c)),
    R("basicSelector", [color, " creature"], lambda t,c:ColorCreatureSelector(c)),
    R("basicSelector", [color, " creatures"], lambda t,c:ColorCreatureSelector(c)),
    R("basicSelector", ["enchanted creature"], lambda t:EnchantedCreatureSelector()),
    R("basicSelector", ["enchanted permanent"], lambda t:EnchantedPermanentSelector()),
    R("basicSelector", ["enchanted land"], lambda t:EnchantedLandSelector()),

    R("basicSelector", ["opponent"], lambda t:OpponentSelector()),
    R("basicSelector", ["an opponent"], lambda t:OpponentSelector()),
    R("basicSelector", ["a card"], lambda t:CardSelector()),
    R("basicSelector", [color, " ", cardType, " card"], lambda t,c,p:ColorTypeCardSelector(c,p)),
    R("basicSelector", ["a land"], lambda t:LandSelector()),
    R("basicSelector", ["land"], lambda t:LandSelector()),
    R("basicSelector", ["lands"], lambda t:LandSelector()),

    R("basicSelector", ["a creature card"], lambda t:CreatureCardSelector()),
    R("basicSelector", ["creature card"], lambda t:CreatureCardSelector()),
    R("basicSelector", ["creature card from your graveyard"], lambda t:CreatureCardFromYourGraveyardSelector()),
    R("basicSelector", ["creature cards of the chosen type"], lambda t:CreatureCardOfTheChosenType()),
    R("basicSelector", ["a basic land card"], lambda t:BasicLandCardSelector()),
    R("basicSelector", ["a ", basicLand, " card"], lambda t,x:SubTypeCardSelector(x)),
    R("basicSelector", [basicLand], lambda t,x:LandSubTypeSelector(x)),
    R("basicSelector", ["a ", basicLand], lambda t,x:LandSubTypeSelector(x)),
    R("basicSelector", [basicLand, " you control"], lambda t,x:SubtypeYouControlSelector(x)),
    R("basicSelector", ["nonbasic land"], lambda t:NonBasicLandSelector()),
    R("basicSelector", ["nonbasic lands"], lambda t:NonBasicLandSelector()),
    R("basicSelector", ["artifact"], lambda t:ArtifactSelector()),
    R("basicSelector", ["artifact or land"], lambda t:ArtifactOrLandSelector()),
    R("basicSelector", ["artifact, enchantment, or land"], lambda t:ArtifactEnchantmentOrLandSelector()),
    R("basicSelector", ["enchantment"], lambda t:EnchantmentSelector()),
    R("basicSelector", ["a ", color, " spell"], lambda t,c:ColorSpellSelector(c)),
    R("basicSelector", ["spell"], lambda t:SpellSelector()),
    R("basicSelector", ["each spell"], lambda t:SpellSelector()),
    R("basicSelector", ["a spell"], lambda t:SpellSelector()),
    R("basicSelector", ["instant spell"], lambda t:InstantSpellSelector()),
    R("basicSelector", ["spell with a single target"], lambda t:SpellWithSingleTargetSelector()),
    R("basicSelector", ["creature spell"], lambda t:CreatureSpellSelector()),
    R("basicSelector", ["creature spells"], lambda t:CreatureSpellSelector()),
    R("basicSelector", ["a creature spell"], lambda t:CreatureSpellSelector()),
    R("basicSelector", ["other ", N("creatureType"), " creatures"], lambda t,c:OtherXCreaturesSelector(c)),
    R("basicSelector", ["a spell or ability an opponent controls"], lambda t:SpellOrAbilityAnOpponentControls()),
    R("basicSelector", ["spell or ability"], lambda t:SpellOrAbilitySelector()),
    R("basicSelector", ["permanent"], lambda t:AllPermanentSelector()),
    R("basicSelector", [color, " source"], lambda t,c:ColorSourceSelector(c)),
    R("basicSelector", [N("creatureType")], lambda t,c:SubTypeSelector(c)),
    R("basicSelector", [N("creatureType"), " card from your graveyard"], lambda t,c:SubTypeCardFromYourGraveyardSelector(c)),

    R("numberOfCards", ["a card"], lambda t:NNumber(1)),
    R("numberOfCards", [N("number"), " cards"], lambda t,n:NNumber(n)),

    R("manaCost", [N("manaCostElement"), N("manaCost")], lambda t,e,c: e + c),
    R("manaCost", [N("manaCostElement")], lambda t,e: e),

    R("manaCostElement", ["{", NUMBER, "}"], lambda t,n: n),
    R("manaCostElement", ["{g}"], lambda t: "G"),
    R("manaCostElement", ["{r}"], lambda t: "R"),
    R("manaCostElement", ["{b}"], lambda t: "B"),
    R("manaCostElement", ["{w}"], lambda t: "W"),
    R("manaCostElement", ["{u}"], lambda t: "U"),

    R("Number", [N("number")], lambda t,n:NNumber(n)),
    R("Number", [selector, "'s power"], lambda t,s:SelectorsPower(s)),
    R("Number", ["the number of cards in your hand"], lambda t:NumberOfCardsInYourHand()),
    R("Number", ["the number of ", selector], lambda t,x:EachSelectorNumber(x)),

    R("Number", ["number of ", N("basicLand"), " he or she controls"], lambda t,s:EachSelectorNumber(SubTypeXControlsSelector(s, ThatPlayerSelector()))),
    R("Number", ["number of creature cards in all graveyards"], lambda t:NumberOfCreatureCardsInAllGraveyards()),

    R("number", ["a"], lambda t: 1),
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
    R("NUMBER", [N("NUMERAL"),N("NUMBER")], lambda t,n,m:n+m),

    # we need to keep the grammaticaly incorrect versions also for the text replacement effects
    R("tag", ["mountainwalk"], lambda t:t),
    R("tag", ["mountainwalk (this creature is unblockable as long as defending player controls a mountain.)"], lambda t:"mountainwalk"),

    R("tag", ["forestwalk"], lambda t:t),
    R("tag", ["forestwalk (this creature is unblockable as long as defending player controls a forest.)"], lambda t:"forestwalk"),

    R("tag", ["islandwalk"], lambda t:t),
    R("tag", ["islandwalk (this creature is unblockable as long as defending player controls a island.)"], lambda t:"islandwalk"),

    R("tag", ["plainswalk"], lambda t:t),
    R("tag", ["plainswalk (this creature is unblockable as long as defending player controls a plains.)"], lambda t:"plainswalk"),

    R("tag", ["swampwalk"], lambda t:t),
    R("tag", ["swampwalk (this creature is unblockable as long as defending player controls a swamp.)"], lambda t:"swampwalk"),

    R("tag", ["vigilance"], lambda t:t),
    R("tag", ["first strike"], lambda t:t),
    R("tag", ["reach (this creature can block creatures with flying.)"], lambda t:"reach"),
    R("tag", ["defender (this creature can't attack.)"], lambda t:"defender"),
    R("tag", ["defender"], lambda t:"defender"),
    R("tag", ["flying"], lambda t:"flying"),

    R("tag", ["SELF enters the battlefield tapped."], lambda t:"comes into play tapped"),

    # hack for flying defender combo
    R("tag", ["flying (this creature can't attack, and it can block creatures with flying.)"], lambda t:"flying"),
    

    R("creatureType", ["goblin"], lambda t:t),
    R("creatureType", ["elf"], lambda t:t),
    R("creatureType", ["treefolk"], lambda t:t),
    R("creatureType", ["wall"], lambda t:t),
    R("creatureType", ["zombie"], lambda t:t),

    R("cardType", ["instant"], lambda t:t),
    R("cardType", ["sorcery"], lambda t:t),

    R("counter", ["+1/+1"], lambda t:t)
]

def magic_parser(label, text):
    for result in parse(r, label, text):
        return result

    return None


