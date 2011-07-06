
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
       
        #print `msg.content`

        if msg.content[0] == "status":
            print msg.content[1]

        elif msg.content[0] == "reqans":

            for opt in msg.content[1]:
                print "%d: %s" % (opt[0], opt[1])

            ans = Message(raw_input())
            send.send(ans)
       
        else:
            print `msg.content`


