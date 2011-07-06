
from objects import *
from abilities import *

class Output:
    def deleteObject(self, obj):
        print "Deleting %s" % obj

    def createPlayer(self, id):
        print "Creating player %d" % id

    def createCard(self, id):
        print "Creating card %d" % id

    def createZone(self, id, owner, name):
        print "Creating zone %d %s %s" % (id, str(owner), name)

def input_generator ():
    print "pre first yield"
    _as = yield None
    print "post first yield: " + `_as`

    log = []

    while True:
        print ("player %s: %s" % (_as.player.name, _as.text))
        print ("turn %s, phase: %s, step: %s" % (_as.game.get_active_player().name, _as.game.current_phase, _as.game.current_step))
        print ("battlefield: %s" % (" ".join(map(lambda x:str(x),_as.game.get_in_play_zone().objects))))
        print ("stack: %s" % (" ".join(map(lambda x:"["+str(x)+"]",_as.game.get_stack_zone().objects))))
        print ("library: %d graveyard: %d" % (len(_as.game.get_library(_as.player).objects), len(_as.game.get_graveyard(_as.player).objects) ))
        print ("hand: %s" % (" ".join(map(lambda x:"["+str(x)+"]",_as.game.get_hand(_as.player).objects))))
        print ("manapool: %s" % (_as.player.manapool))
        print ("life: %d" % (_as.player.life))
        action = None
        while action == None:
            i = 0
            for a in _as.actions:
                print ("%d: %s"  % (i, a.text))
                i += 1

            try:

                # automatically pass if only mana abilities possible in a
                # priority

                autopass = True
                if _as.text != "You have priority":
                    autopass = False
                for a in _as.actions:
                    if a.text != "Pass" and not isinstance(a.ability, BasicManaAbility):
                        autopass = False

                if autopass:
                    _input = "0"
                else:
                    _input = raw_input()

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


def test_input_generator (sequence):
    print "pre first yield"
    _as = yield None
    print "post first yield: " + `_as`

    while True:
        print ("player %s: %s" % (_as.player.name, _as.text))
        print ("turn %s, phase: %s, step: %s" % (_as.game.get_active_player().name, _as.game.current_phase, _as.game.current_step))
        print ("battlefield: %s" % (" ".join(map(lambda x:str(x),_as.game.get_in_play_zone().objects))))
        print ("stack: %s" % (" ".join(map(lambda x:"["+str(x)+"]",_as.game.get_stack_zone().objects))))
        print ("library: %d graveyard: %d" % (len(_as.game.get_library(_as.player).objects), len(_as.game.get_graveyard(_as.player).objects) ))
        print ("hand: %s" % (" ".join(map(lambda x:"["+str(x)+"]",_as.game.get_hand(_as.player).objects))))
        print ("manapool: %s" % (_as.player.manapool))
        print ("life: %d" % (_as.player.life))
        action = None
        while action == None:
            i = 0
            for a in _as.actions:
                print ("%d: %s" % (i, a.text))
                i += 1

            try:
                #selected = int(raw_input())

                if (len(sequence) == 0):
                    return

                selected = sequence[0]
                sequence = sequence[1:]
            except ValueError, x:
                selected = -1

            if selected >= 0 and selected < len(_as.actions):
                action = _as.actions[selected]

        _as = yield action



