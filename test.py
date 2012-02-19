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

from ManaClash import *
from game import *
from process import *
from mcio import *

import unittest

def test_common(g):
    g.create()

    c1 = []
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Hasty Suntail Hawk", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying",u"haste"]), "", 1, 1))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Suntail Hawk", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying"]), "", 1, 1))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Suntail Hawk", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying"]), "", 1, 1))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Suntail Hawk", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying"]), "", 1, 1))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Hasty Suntail Hawk", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying",u"haste"]), "", 1, 1))

    p1 = g.create_player("Alice", c1)

    c2 = []
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Scatchy Zombies", "B", set(), set([u"creature"]), set([u"zombie"]), set([u"haste"]), "", 2, 2))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Scatchy Zombies", "B", set(), set([u"creature"]), set([u"zombie"]), set([u"haste"]), "", 2, 2))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Scatchy Zombies", "B", set(), set([u"creature"]), set([u"zombie"]), set([u"haste"]), "", 2, 2))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Scatchy Zombies", "B", set(), set([u"creature"]), set([u"zombie"]), set([u"haste"]), "", 2, 2))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Scatchy Zombies", "B", set(), set([u"creature"]), set([u"zombie"]), set([u"haste"]), "", 2, 2))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))

    p2 = g.create_player("Bob", c2)

    process_game(g)

    return (p1, p2)


class ManaClashTest(unittest.TestCase):

    def test1(self):
        ig = test_input_generator([0, 0, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        n = ig.next()
        o = Output()
        g = Game(ig, o)
        test_common(g)

    def test2(self):
        ig = test_input_generator([0, 0, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0,0, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 0, 0, 1, 3,1, 2, 0, 0, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0])
        n = ig.next()
        o = Output()
        g = Game(ig, o)
        alice, bob = test_common(g)    
        alice_graveyard = g.get_graveyard(alice)
        bob_graveyard = g.get_graveyard(bob)
        assert len(alice_graveyard.objects) == 2 
        assert alice_graveyard.objects[0].state.title == "Suntail Hawk"
        print alice_graveyard.objects[1].state.title
        assert alice_graveyard.objects[1].state.title == "Hasty Suntail Hawk"
    
        assert len(bob_graveyard.objects) == 1
        assert bob_graveyard.objects[0].state.title == "Scatchy Zombies"

if __name__ == "__main__":
    unittest.main()

