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

