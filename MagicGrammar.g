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
    | a=playerDiscardsACardEffect {$value = $a.value}
    | a=xDealNDamageToTargetYEffect {$value = $a.value}
    ;

continuousAbility returns [value]
    : 'flying' {$value = FlyingAbility()}
    ;

triggeredAbility returns [value]
    : a=whenXComesIntoPlayDoEffectAbility {$value = $a.value}
    | a=whenXDealsDamageToYDoEffectAbility {$value = $a.value}
    ;

whenXComesIntoPlayDoEffectAbility returns [value]
    : ('when '|'whenever ') selector ' comes into play, ' effect {$value = WhenXComesIntoPlayDoEffectAbility($selector.value, $effect.text)}
    ;

whenXDealsDamageToYDoEffectAbility returns [value]
    : ('when '|'whenever ') x=selector (' deals '|' deal ') 'damage to ' y=selector ', ' effect {$value = WhenXDealsDamageToYDoEffectAbility($x.value, $y.value, $effect.text)}
    ;

activatedAbility returns [value]
    : a=tappingActivatedAbility {$value=$a.value}
    ;

tappingActivatedAbility returns [value]
    : manaCost ', {T}: ' effect {$value = TapCostDoEffectAbility($manaCost.value, $effect.text)}
    | '{T}: ' effect {$value = TapCostDoEffectAbility("", $effect.text)}
    ;

playerLooseLifeEffect returns [value]
    : selector (' lose ' | ' loses ') NUMBER ' life.' {$value = PlayerLooseLifeEffect($selector.value, int($NUMBER.getText()))}
    ;

playerDiscardsACardEffect returns [value]
    : selector (' discard '|' discards ') numberOfCards '.' {$value = PlayerDiscardsCardEffect($selector.value, $numberOfCards.value)}
    ;

xDealNDamageToTargetYEffect returns [value]
    : x=selector (' deal ' | ' deals ') NUMBER ' damage to target ' y=selector '.' {$value = XDealNDamageToTargetYEffect($x.value, int($NUMBER.getText()), $y.value)}
    ;

selector returns [value]
    : ('a player' | 'each player') {$value = AllPlayersSelector()}
    | 'that player' {$value = ThatPlayerSelector()}
    | 'SELF' {$value = SelfSelector()}
    | 'creature or player' {$value = CreatureOrPlayerSelector()}
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

/*------------------------------------------------------------------
 * LEXER RULES
 *------------------------------------------------------------------*/

NUMBER  : (DIGIT)+ ;
WHITESPACE : ( '\t' | ' ' | '\r' | '\n'| '\u000C' )+    { $channel = HIDDEN; } ;

fragment DIGIT  : '0'..'9' ;

