
from abilities import *

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

    def resolve(self, game, obj):
        print "resolving permanenet %s" % obj.state.title
        game.doZoneTransfer(obj, game.get_in_play_zone())

class DamageAssignmentRules(ObjectRules):
    def resolve(self, game, obj):
        game.doAssignDamage(obj.damage_assignment_list)
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

def parse(state):
    if state.text == "" or state.text == "None":
        if "artifact" in state.types or "creature" in state.types or "enchantment" in state.types:
            return BasicPermanentRules()

    return g_rules[state.text]


