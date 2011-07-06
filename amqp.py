from qpid.messaging import *

class AMQPOutput(Output):
    def __init__ (self, send):
        self.send = send

    def deleteObject(self, obj):
        msg = Message(content={"type":"delete", "id":obj.id})
        self.send.send(msg)

    def createPlayer(self, id):
        msg = Message(content={"type": "createPlayer", "id":id})
        self.send.send(msg)

    def createCard(self, id):
        msg = Message(content={"type":"createCard", "id":id})
        self.send.send(msg)

    def createZone(self, id, owner, name):
        msg = Message(content={"type":"createZone", "id":id, "owner":owner, "name":name})
        self.send.send(msg)

def amqp_input_generator(session, send, recv):
    print "pre first yield"
    _as = yield None
    print "post first yield: " + `_as`

    log = []

    while True:

        msg = ""

        msg += ("player %s: %s" % (_as.player.name, _as.text)) + "\n"
        msg += ("turn %s, phase: %s, step: %s" % (_as.game.get_active_player().name, _as.game.current_phase, _as.game.current_step)) + "\n"
        msg += ("battlefield: %s" % (" ".join(map(lambda x:str(x),_as.game.get_in_play_zone().objects)))) + "\n"
        msg += ("stack: %s" % (" ".join(map(lambda x:"["+str(x)+"]",_as.game.get_stack_zone().objects)))) + "\n"
        msg += ("library: %d graveyard: %d" % (len(_as.game.get_library(_as.player).objects), len(_as.game.get_graveyard(_as.player).objects) )) + "\n"
        msg += ("hand: %s" % (" ".join(map(lambda x:"["+str(x)+"]",_as.game.get_hand(_as.player).objects)))) + "\n"
        msg += ("manapool: %s" % (_as.player.manapool)) + "\n"
        msg += ("life: %d" % (_as.player.life)) + "\n"

        print msg

        send.send(Message(content=["status", msg]))

        action = None
        while action == None:
            i = 0

            opts = []

            for a in _as.actions:
                #print ("%d: %s"  % (i, a.text))
                opts.append ( [i, a.text] )
                i += 1

            try:
                send.send(Message(content=["reqans", opts]))

                msg = recv.fetch()
                _input = msg.content
                session.acknowledge()

                #_input = raw_input()

                if _input == "log":
                    print `log`
                if _input == "exit":
                    return
                selected = int(_input)
                log.append(selected)
            except ValueError, x:
                selected = -1

            if selected >= 0 and selected < len(_as.actions):
                action = _as.actions[selected]

        _as = yield action


