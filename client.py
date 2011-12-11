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
from qpid.messaging import *


if __name__ == "__main__":
    broker = sys.argv[1]
    send_address = sys.argv[2]
    recv_address = sys.argv[3]

    print `(broker, send_address, recv_address)`
    connection = Connection(broker)
    connection.open()
    session = connection.session()

    send = session.sender(send_address)
    recv = session.receiver(recv_address)

    while True:
        msg = recv.fetch()

        session.acknowledge()
       
        # print `msg.content`

        type = msg.content["type"]

        if type == "status":
            print msg.content["text"]

        elif type == "reqans":

            for opt in msg.content["opts"]:
                print "%d: %s" % (opt[0], opt[1])

            ans = Message(raw_input())
            send.send(ans)
       
        else:
            print `msg.content`


