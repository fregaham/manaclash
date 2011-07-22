grammar MagicGrammar;

options {
    language = Python;
}

tokens {
    PLUS    = '+' ;
    MINUS   = '-' ;
    MULT    = '*' ;
    DIV = '/' ;
    
}

@header {
import sys
import traceback

from abilities import *
from effects import *
from selectors import *
from rules import *

from MagicGrammarLexer import MagicGrammarLexer

}

@main {
def main(argv, otherArg=None):
  char_stream = ANTLRStringStream(argv[1])
  lexer = MagicGrammarLexer(char_stream)
  tokens = CommonTokenStream(lexer)
  parser = MagicGrammarParser(tokens);

  try:
        ret = parser.ability()

        

        print `ret`
  except RecognitionException:
    traceback.print_stack()
}

/*------------------------------------------------------------------
 * PARSER RULES
 *------------------------------------------------------------------*/

ability returns [value] 
    : a=continuousAbility {$value = $a.value}
    | a=triggeredAbility {$value = $a.value}
    | a=activatedAbility {$value = $a.value}
    ;

effect returns [value]
    : a=playerLooseLifeEffect {$value = $a.value}
    | a=playerGainLifeEffect {$value = $a.value}
    | a=playerGainLifeForEachXEffect {$value = $a.value}
    | a=playerDiscardsACardEffect {$value = $a.value}
    | a=xDealNDamageToTargetYEffect {$value = $a.value}
    | a=xGetsNN {$value = $a.value}
    | a=targetXGetsNNUntilEndOfTurn {$value = $a.value}
    | a=destroyTargetX {$value = $a.value}
    | a=buryTargetX {$value = $a.value}
    | a=destroyX {$value = $a.value}
    | a=destroyTargetXYGainLifeEqualsToItsPower {$value = $a.value}
    | a=destroyXAtEndOfCombat {$value = $a.value}
    | a=dontUntapDuringItsControllersUntapStep {$value = $a.value}
    ;

enchantment returns [value]
    : 'enchant ' x=selector ' ' effect {$value = EnchantPermanentRules($x.value, ContinuousEffectStaticAbility($effect.value))}
    ;

continuousAbility returns [value]
    : 'flying' {$value = FlyingAbility()}
    ;

triggeredAbility returns [value]
    : a=whenXComesIntoPlayDoEffectAbility {$value = $a.value}
    | a=whenXDealsDamageToYDoEffectAbility {$value = $a.value}
    | a=whenXBlocksOrBecomesBlockedByYDoEffectAbility {$value = $a.value}
    ;

whenXComesIntoPlayDoEffectAbility returns [value]
    : ('when '|'whenever ') selector ' comes into play, ' effect {$value = WhenXComesIntoPlayDoEffectAbility($selector.value, $effect.text)}
    | ('when '|'whenever ') selector ' enters the battlefield, ' effect {$value = WhenXComesIntoPlayDoEffectAbility($selector.value, $effect.text)}
    ;

whenXDealsDamageToYDoEffectAbility returns [value]
    : ('when '|'whenever ') x=selector (' deals '|' deal ') 'damage to ' y=selector ', ' effect {$value = WhenXDealsDamageToYDoEffectAbility($x.value, $y.value, $effect.text)}
    ;

whenXBlocksOrBecomesBlockedByYDoEffectAbility returns [value]
    : ('when '|'whenever ') x=selector ' blocks or becomes blocked by' (' a '|' an ') y=selector ', ' effect {$value=WhenXBlocksOrBecomesBlockedByYDoEffectAbility($x.value, $y.value, $effect.text)}
    ;

activatedAbility returns [value]
    : a=tappingActivatedAbility {$value=$a.value}
    ;

tappingActivatedAbility returns [value]
    : manaCost ', {T}: ' effect {$value = TapCostDoEffectAbility($manaCost.value, $effect.text)}
    | '{T}: ' effect {$value = TapCostDoEffectAbility("", $effect.text)}
    ;

playerLooseLifeEffect returns [value]
    : selector (' lose ' | ' loses ') number ' life.' {$value = PlayerLooseLifeEffect($selector.value, $number.value)}
    ;

playerGainLifeEffect returns [value]
    : selector (' gain ' | ' gains ') number ' life.' {$value = PlayerGainLifeEffect($selector.value, $number.value)}
    ;

playerGainLifeForEachXEffect returns [value]
    : a=selector (' gain '|' gains ') number ' life for each ' x=selector '.' {$value = PlayerGainLifeForEachXEffect($a.value, $number.value, $x.value)}
    ;

playerDiscardsACardEffect returns [value]
    : selector (' discard '|' discards ') numberOfCards '.' {$value = PlayerDiscardsCardEffect($selector.value, $numberOfCards.value)}
    ;

xDealNDamageToTargetYEffect returns [value]
    : x=selector (' deal ' | ' deals ') number ' damage to target ' y=selector '.' {$value = XDealNDamageToTargetYEffect($x.value, $number.value, $y.value)}
    ;

targetXGetsNNUntilEndOfTurn returns [value]
    : 'target ' selector (' gets '|' get ') a=number '/' b=number ' until end of turn.' {$value = TargetXGetsNNUntilEndOfTurn($selector.value, $a.value, $b.value)}
    ;

dontUntapDuringItsControllersUntapStep returns [value]
    : x=selector 'doesn\'t untap during its controller\'s untap step.' {$value = XDontUntapDuringItsControllersUntapStep($selector.value)}
    ;

xGetsNN returns [value]
    : x=selector (' gets '|' get ') a=number '/' b=number '.' {$value = XGetsNN($x.value, $a.value, $b.value)}
    ;

destroyTargetX returns [value]
    : 'destroy target ' x=selector '.' {$value = DestroyTargetX($x.value)}
    ;

buryTargetX returns [value]
    : 'destroy target ' x=selector '. it can\'t be regenerated.' {$value = BuryTargetX($x.value)}
    ;

destroyTargetXYGainLifeEqualsToItsPower returns [value]
    : 'destroy target ' x=selector '. ' y=selector (' gain '|' gains ') 'life equal to its power.' {$value = DestroyTargetXYGainLifeEqualsToItsPower($x.value, $y.value)}
    ;

destroyXAtEndOfCombat returns [value]
    : 'destroy ' x=selector ' at end of combat.' {$value = DoXAtEndOfCombat('destroy ' + $x.text + '.')}
    | 'destroy that creature at end of combat.' {$value = DoXAtEndOfCombat('destroy that creature.')}
    ;

destroyX returns [value]
    : 'destroy ' x=selector '.' {$value=DestroyX($x.value)}
    | 'destroy that creature.' {$value=DestroyX(ThatCreatureSelector())}
    ;

selector returns [value]
    : ('a player'|'each player') {$value = AllPlayersSelector()}
    | 'that creature' {$value = ThatCreatureSelector()}
    | 'that player' {$value = ThatPlayerSelector()}
    | 'you' {$value = YouSelector()}
    | 'SELF' {$value = SelfSelector()}
    | 'creature' {$value = CreatureSelector()}
    | 'creature or player' {$value = CreatureOrPlayerSelector()}
    | 'attacking or blocking creature' {$value = AttackingOrBlockingCreatureSelector()}
    | 'attacking creature' {$value = AttackingCreatureSelector()}
    | 'creature attacking you' {$value = CreatureAttackingYouSelector()}
    | 'non' color ' creature' {$value = NonColorCreatureSelector($color.value)}
    | 'enchanted creature' {$value = EnchantedCreatureSelector()} 
    ;

numberOfCards returns [value]
    : 'a card' {$value = 1}
    ;

manaCost returns [value]
    : a=manaCostElement b=manaCost {$value = $a.value + $b.value}
    | manaCostElement {$value = $manaCostElement.value}
    ;

manaCostElement returns [value]
    : '{' NUMBER '}' {$value = $NUMBER.getText()}
    ;

number returns [value]
    : NUMBER {$value = int($NUMBER.getText())}
    | 'X' {$value = 'X'}
    | '-' NUMBER {$value = -int($NUMBER.getText())}
    | '-' 'X' {$value = '-X'}
    | '+' NUMBER {$value = int($NUMBER.getText())}
    | '+' 'X' {$value = '+X'}
    ;

color returns [value]
    : 'red' {$value = 'red'}
    | 'green' {$value = 'green'}
    | 'black' {$value = 'black'}
    | 'white' {$value = 'white'}
    | 'blue' {$value = 'blue'}
    ;

/*------------------------------------------------------------------
 * LEXER RULES
 *------------------------------------------------------------------*/

NUMBER  : (DIGIT)+ ;
WHITESPACE : ( '\t' | ' ' | '\r' | '\n'| '\u000C' )+    { $channel = HIDDEN; } ;

fragment DIGIT  : '0'..'9' ;

