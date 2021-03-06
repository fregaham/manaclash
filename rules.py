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
#from effects import *
from selectors import *
from process import Process, SandwichProcess

class ObjectRules:
    def getAbilities(self):
        return []

    def resolve(self, game, obj):
        game.process_returns_push(True)

    def selectTargets(self, game, player, obj):
        game.process_returns_push(True)


class BasicLandRules(ObjectRules):
    def __init__ (self, color):
        self.color = color

    def __str__(self):
        return "BasicLandRules()"

class NonBasicLandRules(ObjectRules):
    def __init__(self, abilities):
        self.abilities = abilities

    def getAbilities(self):
        return self.abilities

    def resolve(self, game, obj):
        game.onResolve(obj)
        game.doZoneTransfer(obj, game.get_in_play_zone())
        game.process_returns_push(True)

    def __str__(self):
        return "NonBasicLandRules(" + (",".join(map(str, self.abilities))) + ")"

class BasicPermanentRules(ObjectRules):
    def __init__(self, abilities):
        self.abilities = abilities

    def getAbilities(self):
        return [PlaySpell()] + self.abilities

    def resolve(self, game, obj):
#        print("resolving permanenet %s" % obj.state.title)
        game.onResolve(obj)
        game.doZoneTransfer(obj, game.get_in_play_zone())
        game.process_returns_push(True)

    def __str__(self):
        return "BasicPermanentRules(" + (",".join(map(str, self.abilities))) + ")"

class DamageAssignmentRules(ObjectRules):
    def resolve(self, game, obj):
        game.onResolve(obj)
        game.doDealDamage(obj.damage_assignment_list, obj.combat)
        game.delete(obj)
        game.process_returns_push(True)

    def __str__(self):
        return "DamageAssignmentRules()"

class EffectRulesProcess(SandwichProcess):
    def __init__ (self, effect, obj):
        SandwichProcess.__init__ (self)
        self.effect = effect
        self.obj_id = obj.id

    def pre(self, game):
        self.effect.resolve(game, game.obj(self.obj_id))

    def main(self, game):
        # peek at the return, pass it over to the upstream process
        if game.process_returns_top():
            game.onResolve(game.obj(self.obj_id))

    def post(self, game):
        game.doZoneTransfer(game.obj(self.obj_id), game.get_removed_zone())
#        game.delete(game.obj(self.obj_id))

class EffectRules(ObjectRules):
    def __init__(self, effect):
        self.effect = effect

    def resolve(self, game, obj):
        game.process_push(EffectRulesProcess(self.effect, obj))

    def selectTargets(self, game, player, obj):
        self.effect.selectTargets(game, player, obj)

    def __str__(self):
        return "EffectRules(%s)" % str(self.effect)

class BasicNonPermanentRulesResolveProcess(SandwichProcess):
    def __init__ (self, effect, obj):
        SandwichProcess.__init__ (self)
        self.effect = effect
        self.obj_id = obj.id

    def pre(self, game):
        self.effect.resolve(game, game.obj(self.obj_id))

    def main(self, game):
        # peek at the return, pass it over to the upstream process
        if game.process_returns_top():
            game.onResolve(game.obj(self.obj_id))

    def post(self, game):
        obj = game.obj(self.obj_id)
        game.doZoneTransfer(obj, game.get_graveyard(game.objects[obj.state.owner_id]))

class BasicNonPermanentRules(ObjectRules):
    def __init__(self, effect, abilities = []):
        self.effect = effect
        self.abilities = abilities

    def getAbilities(self):
        return [PlaySpell()] + self.abilities

    def resolve(self, game, obj):
        game.process_push(BasicNonPermanentRulesResolveProcess(self.effect, obj))

    def selectTargets(self, game, player, obj):
        self.effect.selectTargets(game, player, obj)

    def __str__ (self):
        return "BasicNonPermanentRules(%s, %s)" % (str(self.effect), ",".join(map(str, self.abilities)))

class EnchantPermanentRulesResolveProcess(SandwichProcess):
    def __init__ (self, selector, obj):
        SandwichProcess.__init__ (self)
        self.selector = selector
        self.obj_id = obj.id

    def pre(self, game):
        from process import ValidateTargetProcess
        obj = game.obj(self.obj_id)
        game.process_push(ValidateTargetProcess(obj, self.selector, obj.targets["target"]))

    def main(self, game):
        # peek at the return, pass it over to the upstream process
        if game.process_returns_top():
            obj = game.obj(self.obj_id)
            obj.enchanted_id = game.lki(obj.targets["target"]).get_id()
            game.onResolve(obj)

    def post(self, game):
        if game.process_returns_top():
            game.doZoneTransfer(game.obj(self.obj_id), game.get_in_play_zone())
        else:
            game.doZoneTransfer(game.obj(self.obj_id), game.get_graveyard(game.objects[obj.state.owner_id]))

class EnchantPermanentRulesSelectTargets(SandwichProcess):
    def __init__ (self, player, selector, obj):
        SandwichProcess.__init__ (self)
        self.selector = selector
        self.player_id = player.id
        self.obj_id = obj.id

    def pre(self, game):
        from process import SelectTargetProcess
        player = game.obj(self.player_id)
        obj = game.obj(self.obj_id)
        game.process_push(SelectTargetProcess(player, obj, self.selector))

    def main(self, game):
        target = game.process_returns_pop()
        if target == None:
            game.process_returns_push(False)
        else:
            game.obj(self.obj_id).targets["target"] = game.create_lki(game.obj(target))
            game.process_returns_push(True)
        

class EnchantPermanentRules(ObjectRules):
    def __init__(self, selector, abilities = []):
        self.selector = selector
        self.abilities = abilities

    def getAbilities(self):
        return [PlaySpell()] + self.abilities

    def resolve(self, game, obj):
        game.process_push(EnchantPermanentRulesResolveProcess(self.selector, obj))

    def selectTargets(self, game, player, obj):
        game.process_push(EnchantPermanentRulesSelectTargets(player, self.selector, obj))
        
    def __str__ (self):
        return "EnchantPermanentRules(%s, %s)" % (str(self.selector), ",".join(map(str, self.abilities)))


g_rules = {}
g_rules["g"] = BasicLandRules("G")
g_rules["r"] = BasicLandRules("R")
g_rules["u"] = BasicLandRules("U")
g_rules["w"] = BasicLandRules("W")
g_rules["b"] = BasicLandRules("B")
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
    elif "land" in obj.state.types and "basic" not in obj.state.supertypes:
        rules = caching_magic_parser("nonBasicLandRules", text)
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

def manaEffect(text):
    # note that it doesn't return object, just the effect, as mana effects don't use stack
    return caching_magic_parser("manaEffect", text)

