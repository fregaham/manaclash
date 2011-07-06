
class Action:
    def __init__ (self):
        self.player = None
        self.text = None
        self.object = None
        self.ability = None

class PassAction(Action):
    def __init__ (self, player):
        Action.__init__ (self)
        self.player = player
        self.text = "Pass"

class AbilityAction(Action):
    def __init__ (self, player, object, ability, text):
        Action.__init__(self)
        self.player = player
        self.object = object
        self.ability = ability
        self.text = text

class PayCostAction(Action):
    def __init__ (self, player, cost, text):
        Action.__init__ (self)
        self.player = player
        self.cost = cost
        self.text = text

class ActionSet:
    def __init__ (self, game, player, text, actions):
        self.game = game
        self.player = player
        self.text = text
        self.actions = actions


