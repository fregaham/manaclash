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

        if game.isInPlay(obj):
            obj.state.abilities.extend (self.abilities)

    def resolve(self, game, obj):
        print "resolving permanenet %s" % obj.state.title
        game.doZoneTransfer(obj, game.get_in_play_zone())

    def __str__(self):
        return "BasicPermanentRules(" + (",".join(map(str, self.abilities))) + ")"

class DamageAssignmentRules(ObjectRules):
    def resolve(self, game, obj):
        game.doDealDamage(obj.damage_assignment_list, obj.combat)
        game.delete(obj)

    def __str__(self):
        return "DamageAssignmentRules()"

class EffectRules(ObjectRules):
    def __init__(self, effect):
        self.effect = effect
    def resolve(self, game, obj):
        self.effect.resolve(game, obj)
        game.delete(obj)
    def selectTargets(self, game, player, obj):
        return self.effect.selectTargets(game, player, obj)

    def __str__(self):
        return "EffectRules(%s)" % str(self.effect)

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

    def __str__ (self):
        return "BasicNonPermanentRules(%s)" % str(self.effect)

class EnchantPermanentRules(ObjectRules):
    def __init__(self, selector, ability):
        self.selector = selector
        self.ability = ability

    def evaluate(self, game, obj):
        obj.state.abilities.append (PlaySpell())

        if game.isInPlay(obj):
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
        
    def __str__ (self):
        return "EnchantPermanentRules(%s, %s)" % (str(self.selector), str(self.ability))


g_rules = {}
g_rules["[G]"] = BasicLandRules("G")
g_rules["[R]"] = BasicLandRules("R")
g_rules["[U]"] = BasicLandRules("U")
g_rules["[W]"] = BasicLandRules("W")
g_rules["[B]"] = BasicLandRules("B")
g_rules["damage assignment"] = DamageAssignmentRules()
g_rules[""] = ObjectRules()
g_rules[None] = ObjectRules()

g_ruleCache = {}

def caching_magic_parser(what, text):
    
    if (what, text) in g_ruleCache:
        return g_ruleCache[(what, text)]

    from MagicParser import magic_parser
    g_ruleCache[(what,text)] = magic_parser(what, text)
    return g_ruleCache[(what,text)]

def parse(obj):

    text = obj.state.text
    if text is None:
        text = ""

    from MagicParser import magic_parser

    rules = None

    if isinstance(obj, EffectObject):
        rules = caching_magic_parser("effectRules", text)
    elif "artifact" in obj.state.types or "creature" in obj.state.types: 
        rules = caching_magic_parser("permanentRules", text)
    elif "enchantment" in obj.state.types:
        rules = caching_magic_parser("enchantmentRules", text)
    elif "sorcery" in obj.state.types or "instant" in obj.state.types:
        rules = caching_magic_parser("sorceryOrInstantRules", text)
    else:
        return g_rules[obj.state.text]

    assert rules is not None
    return rules

def effectRules(text):
    return caching_magic_parser("effectRules", text)


