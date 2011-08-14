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

    def __str__(self):
        return "BasicLandRules()"

class BasicPermanentRules(ObjectRules):
    def __init__(self, abilities):
        self.abilities = abilities

    def evaluate(self, game, obj):
        obj.state.abilities.append (PlaySpell())
        obj.state.abilities.extend (self.abilities)

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

    text = obj.state.text
    if text is None:
        text = ""

    from MagicGrammarParser import MyMagicGrammarLexer, MyMagicGrammarParser
    char_stream = ANTLRStringStream(text)
    lexer = MyMagicGrammarLexer(char_stream)
    tokens = CommonTokenStream(lexer)
    parser = MyMagicGrammarParser(tokens)

    rules = None

    if isinstance(obj, EffectObject):
        rules = parser.effectRules()
    elif "artifact" in obj.state.types or "creature" in obj.state.types: 
        rules = parser.permanentRules()
    elif "enchantment" in obj.state.types:
        rules = parser.enchantmentRules()
    elif "sorcery" in obj.state.types or "instant" in obj.state.types:
        rules = parser.sorceryOrInstantRules()
    else:
        return g_rules[obj.state.text]

    assert rules is not None
    sys.stderr.write("Parsing %s\n" % text)
    for lexerError in lexer.myErrors:
        sys.stderr.write(lexerError + "\n")
    for parserError in parser.myErrors:
        sys.stderr.write(parserError + "\n")
    assert len(parser.myErrors) == 0 and len(lexer.myErrors) == 0
    return rules


