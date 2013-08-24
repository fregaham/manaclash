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

from mcio import Output, input_generator
from game import Game
       
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
    c1.append (g.create_card ("Plains", None, set(["basic"]), set(["land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card ("Plains", None, set(["basic"]), set(["land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card ("Hasty Moggie Bird", "W", set(), set(["creature"]), set(["bird"]), set(["flying","haste"]), "when SELF comes into play, each player loses 1 life.", 1, 1))
    c1.append (g.create_card ("Plains", None, set(["basic"]), set(["land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card ("Plains", None, set(["basic"]), set(["land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card ("Moggie Bird", "W", set(), set(["creature"]), set(["bird"]), set(["flying"]), "when SELF comes into play, each player loses 1 life.", 1, 1))
    c1.append (g.create_card ("Plains", None, set(["basic"]), set(["land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card ("Plains", None, set(["basic"]), set(["land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card ("Moggie Bird", "W", set(), set(["creature"]), set(["bird"]), set(["flying"]), "when SELF comes into play, each player loses 1 life.", 1, 1))
    c1.append (g.create_card ("Plains", None, set(["basic"]), set(["land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card ("Plains", None, set(["basic"]), set(["land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card ("Discardie", "W", set(), set(["creature"]), set(["bird"]), set(["flying"]), "whenever SELF deals damage to a player, that player discards a card.", 2, 3))
    c1.append (g.create_card ("Plains", None, set(["basic"]), set(["land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card ("Plains", None, set(["basic"]), set(["land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card ("Hasty Moggie Bird", "W", set(), set(["creature"]), set(["bird"]), set(["flying","haste"]), "when SELF comes into play, each player loses 1 life.", 1, 1))
    c1.append (g.create_card ("Loose Ring", "1", set(), set(["artifact"]), set(), set(), "{T}: SELF deals 4 damage to target creature or player.", None, None))
    #c1.append (g.create_card ("Deal Damage", "W", set(), set(["instant"]), set(), set(), "SELF deals 1 damage to target creature or player.", None, None))
    c1.append (g.create_card ("Pimp of Mercy", "W", set(), set(["creature"]), set(), set(), "when SELF enters the battlefield, you gain 3 life.", 1, 1))
    c1.append (g.create_card ("Angelic Jimmy", "W", set(), set(["creature"]), set(), set(), "{T}: target attacking or blocking creature gets +1/+1 until end of turn.", 1, 1))
    c1.append (g.create_card ("Bleezy", "XW", set(), set(["sorcery"]), set(), set(), "SELF deals X damage to target creature or player.", None, None))

    g.create_player("Alice", c1)

    c2 = []
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card ("Scatchy Zombies", "B", set(), set(["creature"]), set(["zombie"]), set(["haste"]), "", 2, 2))
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card ("Scatchy Zombies", "B", set(), set(["creature"]), set(["zombie"]), set(["haste"]), "", 2, 2))
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card ("Scatchy Zombies", "B", set(), set(["creature"]), set(["zombie"]), set(["haste"]), "", 2, 2))
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card ("Scatchy Zombies", "B", set(), set(["creature"]), set(["zombie"]), set(["haste"]), "", 2, 2))
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card ("Scatchy Zombies", "B", set(), set(["creature"]), set(["zombie"]), set(["haste"]), "", 2, 2))
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card ("Swamp", None, set(["basic"]), set(["land"]), set(), set(), "[B]", None, None))

    g.create_player("Bob", c2)

    process_game(g)


