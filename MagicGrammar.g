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
    ;

continuousAbility returns [value]
    : 'flying' {$value = FlyingAbility()}
    ;

triggeredAbility returns [value]
    : 'when SELF comes into play, ' effect {$value = WhenSelfComesIntoPlayDoEffectAbility($effect.text)}
    ;

playerLooseLifeEffect returns [value]
    : selector ('lose' | 'loses') NUMBER 'life.' {$value = PlayerLooseLifeEffect($selector.value, int($NUMBER.getText()))}
    ;

selector returns [value]
    : 'each player' {$value = AllPlayersSelector()}
    ;

expr  returns [value]  : term ( ( PLUS | MINUS )  term )* {$value = "42"};

term    : factor ( ( MULT | DIV ) factor )* ;

factor  : NUMBER ;


/*------------------------------------------------------------------
 * LEXER RULES
 *------------------------------------------------------------------*/

NUMBER  : (DIGIT)+ ;

WHITESPACE : ( '\t' | ' ' | '\r' | '\n'| '\u000C' )+    { $channel = HIDDEN; } ;

fragment DIGIT  : '0'..'9' ;

