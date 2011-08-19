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

class ObjectState:
    def __init__ (self):
        self.title = None
        self.colors = set()
        self.power = None
        self.toughness = None
        self.owner_id = None
        self.controller_id = None
        self.tags = set()
        self.types = set()
        self.supertypes = set()
        self.subtypes = set()
        self.abilities = []
        self.manacost = None
        self.text = None

    def copy (self):
        ret = ObjectState ()
        ret.title = self.title
        ret.colors = self.colors.copy()
        ret.power = self.power
        ret.toughness = self.toughness
        ret.owner_id = self.owner_id
        ret.controller_id = self.controller_id
        ret.tags = self.tags.copy()
        ret.text = self.text
        ret.types = self.types.copy()
        ret.supertypes = self.supertypes.copy()
        ret.subtypes = self.subtypes.copy()
        ret.abilities = self.abilities[:]
        ret.manacost = self.manacost
        return ret

class Object:
    def __init__ (self):
        self.id = None
        self.initial_state = ObjectState()
        self.controller_id = None
        self.owner_id = None
        self.state = ObjectState()
        self.zone_id = None
        self.timestamp = None
        self.tapped = False
        self.rules = None
        self.damage = 0
        self.targets = {}
        self.x = None
        self.enchanted_id = None

    def get_id(self):
        return self.id

    def get_self_id(self):
        return self.id

    # little hack, this is useful for spell effects, which are their own source, if they resolve, there is no need for lki
    def get_source_lki(self):
        return self

    def get_state (self):
        return self.state

    def get_object(self):
        return self

    def copy(self):
        ret = Object()
        return ret._copy(self)

    def is_moved(self):
        return False

    def get_controller_id(self):
        return self.state.controller_id

    def _copy(self, src):
        self.id = src.id
        self.initial_state = src.initial_state.copy()
        self.controller_id = src.controller_id
        self.owner_id = src.owner_id
        self.state = src.state.copy()
        self.zone_id = src.zone_id
        self.timestamp = src.timestamp
        self.tapped = src.tapped
        self.rules = src.rules
        self.damage = src.damage
        self.targets = src.targets.copy()
        self.x = src.x
        self.enchanted_id = src.enchanted_id

    def __str__ (self):

        ret = "["
        if self.state.power != None:
            ret += "#%s %s {%s} `%s' %d/%d" % (str(self.id), self.state.title, ", ".join(self.state.tags), self.state.text, self.state.power, self.state.toughness)
        else:
            ret += "#%s %s {%s} `%s'" % (str(self.id), self.state.title, ", ".join(self.state.tags), self.state.text)

        if self.enchanted_id != None:
            ret += " enchanting %s" % (str(self.enchanted_id))

        if self.tapped:
            ret += " tapped"

        ret += "]"

        return ret

class Zone(Object):
    def __init__ (self, type=None, player_id=None):
        Object.__init__ (self)
        self.type = type
        self.player_id = player_id
        self.objects = []

    def copy(self):
        return Zone()._copy(self)

    def _copy(self, src):
        Object._copy(self, src)
        self.type = src.type
        self.player_id = src.player_id
        self.objects = src.objects[:]

class Player (Object):
    def __init__ (self, name):
        Object.__init__ (self)
        self.hand_id = None
        self.library_id = None
        self.graveyard_id = None
        self.life = 20
        self.name = name
        self.manapool = ""
        self.maximum_hand_size = 0
        self.land_play_limit = 0
        self.land_played = 0

    def copy(self):
        return Player(self.name)._copy(self)

    def _copy(self, src):
        Object._copy(self, src)
        self.hand_id = src.hand_id
        self.library_id = src.library_id
        self.graveyard_id = src.graveyard_id
        self.life = src.life
        self.name = src.name
        self.manapool = src.manapool
        self.maximum_hand_size = src.maximum_hand_size
        self.land_play_limit = src.land_play_limit
        self.land_played = src.land_played

class DamageAssignment (Object):
    def __init__ (self, damage_assignment_list, combat):
        Object.__init__ (self)
        self.damage_assignment_list = damage_assignment_list
        self.initial_state.title = "damage assignment"
        self.initial_state.text = "damage assignment"
        self.combat = combat

    def copy(self):
        return DamageAssignment(self.damage_assignment_list, self.combat)._copy(self)

    def _copy(self, src):
        Object._copy(self, src)
        self.damage_assignment_list = src.damage_assignment_list
        self.combat = src.combat

class EffectObject(Object):
    def __init__ (self, source_lki, controller_id, text, slots):
        Object.__init__ (self)

        assert isinstance(source_lki, Object)

        self.source_lki = source_lki
        self.controller_id = controller_id
        self.initial_state.title = "Effect"
        self.initial_state.text = text

        self.slots = slots

    def get_self_id(self):
        return self.source_lki.get_id()

    def get_source_lki(self):
        return self.source_lki

    def get_controller_id(self):
        return self.controller_id

    def get_slots(self):
        return self.slots

    def get_slot(self, key):
        return self.slots.get(key)

    def copy(self):
        return EffectObject(self.source_lki, self.controller_id, self.text, self.slots)._copy(self)

    def _copy(self, src):
        Object._copy(self, src)

class LastKnownInformation(Object):
    def __init__ (self, game, object):
        self.game = game
        self.object = object
        self._state = None
        self.moved = False
        self.game.add_event_handler ("pre_zone_transfer", self.onPreMoveObject)

    def get_id(self):
        return self.object.id

    def get_self_id(self):
        return self.object.id

    def get_object (self):
        return self.object

    def get_state (self):
        if self._state == None:
            return self.object.get_state ()
        else:
            return self._state

    def onPreMoveObject (self, object, zone_from, zone_to):
        if self._state is None and object == self.object:
            self._state = self.object.get_state()
            self.moved = True

    def is_moved(self):
        return self.moved


