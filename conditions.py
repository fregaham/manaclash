# Copyright 2012 Marek Schmidt
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

from objects import *

class Condition:
    def evaluate (self, game, context):
        return False
    
    def __str__(self):
        return "condition"

class IfXHasNOrLessLife(Condition):
    def __init__ (self, selector, n):
        self.selector = selector
        self.n = n

    def evaluate(self, game, context):
        # assume it is "any player", not "all players" (mostly it's just you or just opponent anyway)
        for player in self.selector.all(game, context):
            if player.life <= self.n:
                return True

        return False

    def __str__ (self):
        return "IfXHasNOrLessLife(%s, %s)" % (self.selector, self.n)

class ExistsUntappedX(Condition):
    def __init__(self, selector):
        self.selector = selector

    def evaluate(self, game, context):
        for obj in self.selector.all(game, context):
            if not obj.tapped:
                return True

        return False

    def __str__ (self):
        return "ExistsUntappedX(%s)" % self.selector

class XControlsYCondition(Condition):
    def __init__ (self, x_selector, y_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector

    def evaluate(self, game, context):
        x = self.x_selector.only(game, context)
        x_id = x.get_id()

        for y in self.y_selector.all(game, context):
            if y.get_controller_id() == x_id:
                return True

        return False

class XControlsYAndZ(Condition):
    def __init__ (self, x_selector, y_selector, z_selector):
        self.x_selector = x_selector
        self.y_selector = y_selector
        self.z_selector = z_selector

    def evaluate(self, game, context):

        x = self.x_selector.only(game, context)
        x_id = x.get_id()

        doesY = False
        doesZ = False
        for y in self.y_selector.all(game, context):
            if y.get_controller_id() == x_id:
                doesY = True
                break

        for z in self.z_selector.all(game, context):
            if z.get_controller_id() == x_id:
                doesZ = True
                break

        return doesY and doesZ

