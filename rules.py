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
from objects import *
from effects import *
from selectors import *

from antlr3 import *
from MagicGrammarLexer import *
from MagicGrammarParser import *

class ObjectRules:
    def evaluate(self, game, obj):
        pass

    def resolve(self, game, obj):
        pass

class BasicLandRules(ObjectRules):
    def __init__ (self, color):
        self.color = color

    def evaluate(self, game, obj):
        obj.state.abilities.append (BasicManaAbility(self.color))

class BasicPermanentRules(ObjectRules):
    def evaluate(self, game, obj):
        obj.state.abilities.append (PlaySpell())

        obj.state.abilities.extend (parsePermanentAbilities(game, obj))

    def resolve(self, game, obj):
        print "resolving permanenet %s" % obj.state.title
        game.doZoneTransfer(obj, game.get_in_play_zone())

class DamageAssignmentRules(ObjectRules):
    def resolve(self, game, obj):
        game.doAssignDamage(obj.damage_assignment_list)
        game.delete(obj)

class EffectRules(ObjectRules):
    def __init__(self, effect):
        self.effect = effect
    def resolve(self, game, obj):
        self.effect.resolve(game, obj)
        game.delete(obj)

g_rules = {}
g_rules["[G]"] = BasicLandRules("G")
g_rules["[R]"] = BasicLandRules("R")
g_rules["[U]"] = BasicLandRules("U")
g_rules["[W]"] = BasicLandRules("W")
g_rules["[B]"] = BasicLandRules("B")
g_rules["damage assignment"] = DamageAssignmentRules()
g_rules[""] = ObjectRules()
g_rules[None] = ObjectRules()

def parse(obj):

    if isinstance(obj, EffectObject):
        # print "trying to parse: \"%s\"" % obj.state.text
        char_stream = ANTLRStringStream(obj.state.text)
        lexer = MagicGrammarLexer(char_stream)
        tokens = CommonTokenStream(lexer)
        parser = MagicGrammarParser(tokens);

        effect = parser.effect()
        return EffectRules(effect.value)
    
    if "artifact" in obj.state.types or "creature" in obj.state.types or "enchantment" in obj.state.types:
        return BasicPermanentRules()
    
    return g_rules[obj.state.text]

def parsePermanentAbilities(game, obj):
    if obj.state.text != "":
        # print "trying to parse: \"%s\"" % obj.state.text
        char_stream = ANTLRStringStream(obj.state.text)
        lexer = MagicGrammarLexer(char_stream)
        tokens = CommonTokenStream(lexer)
        parser = MagicGrammarParser(tokens);

        ability = parser.ability()
        return [ability]

    return []




