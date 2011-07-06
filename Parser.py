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

class ASTNode:
    pass

class Card(ASTNode):
    def __init__ (self):
        self.name = None
        self.supertypes = []
        self.subtypes = []
        self.types = []
        self.abilities = []
        self.power = None
        self.toughness = None
        self.cost = None

def is_cost (str):
    s = "BRGWUX"
    for c in str:
        if c.isdigit() or c in s:
            pass
        else:
            return False

    return True

def parse_type (str):
    if "-" in str:
        type, subtype = str.split("-", 1)
    else:
        # no subtype
        subtype = ""
        type = str

    types = type.split(" ")
    subtypes = subtype.split(" ")
    
    super_string = ["Legendary"]

    ret_supertypes = []
    ret_types = []
    ret_subtypes = []

    for type in types:
        type = type.strip()
        if type in super_strings:
            ret_supertypes.append (type)
        else:
            ret_types.append (type)

    for type in subtypes:
        type = type.strip()
        ret_subtypes.append (type)

    return (ret_supertypes, ret_types, ret_subtypes)

def parse_oracle (f):
    card = Card()
    state = "name"
    for line in f:
        l = line.rstrip ()

        if state == "name":
            card.name = l
            state = "type"
        elif state == "type":
            if is_cost (l):
                card.cost = l
            else:
                # type
                card.supertypes, card.types, card.subtypes = parse_types (l)
                state = "abilities"
        
