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

import sys

from io import Output, input_generator
from game import Game
from process import process_game
       
if __name__ == "__main__":

    #broker = sys.argv[1]
    #send_address = sys.argv[2]
    #recv_address = sys.argv[3]

    #print `(broker, send_address, recv_address)`
    #connection = Connection(broker)
    #connection.open()
    #session = connection.session()

    #send = session.sender(send_address)
    #recv = session.receiver(recv_address)

    #output = AMQPOutput(send)

    #ig = amqp_input_generator(session, send, recv)

    output = Output()
    ig = input_generator()

    n = ig.next()
    g = Game(ig, output)
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

    g.create_player("Alice", c1)

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

    g.create_player("Bob", c2)

    process_game(g)


