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
        self.player_id = None
        self.text = None
        self.object_id = None
        self.ability = None

class PassAction(Action):
    def __init__ (self, player_id):
        Action.__init__ (self)
        self.player_id = player_id
        self.text = "Pass"

class AbilityAction(Action):
    def __init__ (self, player_id, object_id, ability, text):
        Action.__init__(self)
        self.player_id = player_id
        self.object_id = object_id
        self.ability = ability
        self.text = text

class PayCostAction(Action):
    def __init__ (self, player_id, cost, text):
        Action.__init__ (self)
        self.player_id = player_id
        self.cost = cost
        self.text = text

class ActionSet:
    def __init__ (self, player_id, text, actions):
        self.player_id = player_id
        self.text = text
        self.actions = actions

class QueryNumber:
    def __init__(self, player_id, text):
        self.player = player
        self.text = text

class QueryString:
    def __init__ (self, player_id, text):
        self.player_id = player_id
        self.text = text

