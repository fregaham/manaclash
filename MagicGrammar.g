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
    ;

effect returns [value]
    : a=playerLooseLifeEffect {$value = $a.value}
    | a=playerDiscardsACardEffect {$value = $a.value}
    ;

continuousAbility returns [value]
    : 'flying' {$value = FlyingAbility()}
    ;

triggeredAbility returns [value]
    : ('when '|'whenever ') selector ' comes into play, ' effect {$value = WhenXComesIntoPlayDoEffectAbility($selector.value, $effect.text)}
    | ('when '|'whenever ') x=selector (' deals' | ' deal') ' damage to ' y=selector ', ' effect {$value = WhenXDealsDamageToYDoEffectAbility($x.value, $y.value, $effect.text)}
    ;

playerLooseLifeEffect returns [value]
    : selector (' lose ' | ' loses ') NUMBER ' life.' {$value = PlayerLooseLifeEffect($selector.value, int($NUMBER.getText()))}
    ;

playerDiscardsACardEffect returns [value]
    : selector (' discard '|' discards ') numberOfCards '.' {$value = PlayerDiscardsCardEffect($selector.value, $numberOfCards.value)}
    ;

selector returns [value]
    : ('a player' | 'each player') {$value = AllPlayersSelector()}
    | 'that player' {$value = ThatPlayerSelector()}
    | 'SELF' {$value = SelfSelector()}
    ;

numberOfCards returns [value]
    : 'a card' {$value = 1}
    ;



/*------------------------------------------------------------------
 * LEXER RULES
 *------------------------------------------------------------------*/

NUMBER  : (DIGIT)+ ;
WHITESPACE : ( '\t' | ' ' | '\r' | '\n'| '\u000C' )+    { $channel = HIDDEN; } ;

fragment DIGIT  : '0'..'9' ;

