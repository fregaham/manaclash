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

class QueryNumber:
    def __init__(self, game, player, text):
        self.game = game
        self.player = player
        self.text = text

class QueryString:
    def __init__ (self, game, player, text):
        self.game = game
        self.player = player
        self.text = text

