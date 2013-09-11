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
from actions import *

class Dialog:
    def doModal (self, game, context):
        pass
    
    def __str__(self):
        return "dialog"

class ChooseCreatureTypeProcess:
    def __init__ (self, context):
        self.context_id = context.get_id()

    def next(self, game, action):
        context = game.obj(self.context_id)
        player = game.objects[context.get_controller_id()]
        if action is None:
            return QueryString(game, player, "Choose Creature Type")
        else:
            context.modal = action.lower()

class ChooseCreatureType(Dialog):

    def doModal(self, game, context):
        game.process_push(ChooseCreatureTypeProcess(context))

    def __str__ (self):
        return "ChooseCreatureType()"

class ChooseColorProcess:
    def __init__ (self, context):
        self.context_id = context.get_id()

    def next(self, game, action):
        context = game.obj(self.context_id)
        player = game.objects[context.get_controller_id()]
        if action is None:
            colors = ["black", "blue", "green", "red", "white"]

            actions = []
            for name in colors:
                a = Action()
                a.text = name
                actions.append(a)

            return ActionSet (game, player, ("Choose a color"), actions)
        else:
            context.modal = action.text.lower()

class ChooseColor(Dialog):
    def doModal(self, game, context):
        game.process_push(ChooseColorProcess(context))

