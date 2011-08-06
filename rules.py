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

class ObjectRules:
    def evaluate(self, game, obj):
        pass

    def resolve(self, game, obj):
        pass

    def selectTargets(self, game, player, obj):
        return True

class BasicLandRules(ObjectRules):
    def __init__ (self, color):
        self.color = color

    def evaluate(self, game, obj):
        obj.state.abilities.append (BasicManaAbility(self.color))

class BasicPermanentRules(ObjectRules):
    def evaluate(self, game, obj):
        obj.state.abilities.append (PlaySpell())

        obj.state.abilities.extend (parsePermanentAbilities(obj))

    def resolve(self, game, obj):
        print "resolving permanenet %s" % obj.state.title
        game.doZoneTransfer(obj, game.get_in_play_zone())

class DamageAssignmentRules(ObjectRules):
    def resolve(self, game, obj):
        game.doDealDamage(obj.damage_assignment_list)
        game.delete(obj)

class EffectRules(ObjectRules):
    def __init__(self, effect):
        self.effect = effect
    def resolve(self, game, obj):
        self.effect.resolve(game, obj)
        game.delete(obj)
    def selectTargets(self, game, player, obj):
        return self.effect.selectTargets(game, player, obj)

class BasicNonPermanentRules(ObjectRules):
    def __init__(self, effect):
        self.effect = effect
    def evaluate(self, game, obj):
        obj.state.abilities.append (PlaySpell())
    def resolve(self, game, obj):
        self.effect.resolve(game, obj)
        game.doZoneTransfer(obj, game.get_graveyard(game.objects[obj.state.owner_id]))
    def selectTargets(self, game, player, obj):
        return self.effect.selectTargets(game, player, obj)

class EnchantPermanentRules(ObjectRules):
    def __init__(self, selector, ability):
        self.selector = selector
        self.ability = ability

    def evaluate(self, game, obj):
        obj.state.abilities.append (PlaySpell())
        obj.state.abilities.append(self.ability)

    def resolve(self, game, obj):
        from process import process_validate_target
        if process_validate_target(game, obj, self.selector, obj.targets["target"]):
            obj.enchanted_id = obj.targets["target"].get_id()
            game.doZoneTransfer(obj, game.get_in_play_zone())
        else:
            game.doZoneTransfer(obj, game.get_graveyard(game.objects[obj.state.owner_id]))

    def selectTargets(self, game, player, obj):
        from process import process_select_target
        target = process_select_target(game, player, obj, self.selector)
        if target == None:
            return False

        obj.targets["target"] = LastKnownInformation(game, target)

        return True
        



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
#    from MagicGrammarLexer import MagicGrammarLexer
    from MagicGrammarParser import MyMagicGrammarLexer, MyMagicGrammarParser

    if isinstance(obj, EffectObject):
        # print "trying to parse: \"%s\"" % obj.state.text
        char_stream = ANTLRStringStream(obj.state.text)
        lexer = MyMagicGrammarLexer(char_stream)
        tokens = CommonTokenStream(lexer)
        parser = MyMagicGrammarParser(tokens);

        effect = parser.effect()
        
        assert effect is not None
        print "effect: " + `effect`
        assert effect.value is not None

        assert len(parser.myErrors) == 0 and len(lexer.myErrors) == 0

        return EffectRules(effect.value)
    
    if "artifact" in obj.state.types or "creature" in obj.state.types: 

        parsePermanentAbilities(obj)

        return BasicPermanentRules()

    if "enchantment" in obj.state.types:
        #print "trying to parse: \"%s\"" % obj.state.text
        char_stream = ANTLRStringStream(obj.state.text)
        lexer = MyMagicGrammarLexer(char_stream)
        tokens = CommonTokenStream(lexer)
        parser = MyMagicGrammarParser(tokens);

        rule = parser.enchantment()
        assert rule is not None
        assert len(parser.myErrors) == 0 and len(lexer.myErrors) == 0
        return rule

    if "sorcery" in obj.state.types or "instant" in obj.state.types:
        #print "trying to parse: \"%s\"" % obj.state.text
        char_stream = ANTLRStringStream(obj.state.text)
        lexer = MyMagicGrammarLexer(char_stream)
        tokens = CommonTokenStream(lexer)
        parser = MyMagicGrammarParser(tokens)

        effect = parser.effect()
#        print type(effect)

        assert effect is not None
        assert effect.value is not None
        assert len(parser.myErrors) == 0 and len(lexer.myErrors) == 0

        return BasicNonPermanentRules(effect.value)
    
    return g_rules[obj.state.text]

def parsePermanentAbilities(obj):
#    from MagicGrammarLexer import MagicGrammarLexer
    from MagicGrammarParser import MyMagicGrammarLexer, MyMagicGrammarParser

    if obj.state.text != "":
        #print "trying to parse: \"%s\"" % obj.state.text
        char_stream = ANTLRStringStream(obj.state.text)
        lexer = MyMagicGrammarLexer(char_stream)
        tokens = CommonTokenStream(lexer)
        parser = MyMagicGrammarParser(tokens)

        ability = parser.ability()
        assert ability is not None 
        assert len(parser.myErrors) == 0 and len(lexer.myErrors) == 0

        return [ability]

    return []



