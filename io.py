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

from objects import *
from abilities import *
from actions import *

greeting = """ManaClash  Copyright (C) 2011  Marek Schmidt
    This program comes with ABSOLUTELY NO WARRANTY; for details type `warranty'
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `license' for details.
"""

warranty = """Disclaimer of Warranty.

  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  Limitation of Liability.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

  Interpretation of Sections 15 and 16.

  If the disclaimer of warranty and limitation of liability provided
above cannot be given local legal effect according to their terms,
reviewing courts shall apply local law that most closely approximates
an absolute waiver of all civil liability in connection with the
Program, unless a warranty or assumption of liability accompanies a
copy of the Program in return for a fee.
"""

class Output:
    def deleteObject(self, obj):
        print "Deleting %s" % obj

    def createPlayer(self, id):
        print "Creating player %d" % id

    def createCard(self, id):
        print "Creating card %d" % id

    def createZone(self, id, owner, name):
        print "Creating zone %d %s %s" % (id, str(owner), name)

    def createEffectObject(self, id):
        print "Creating effect %d" % id

    def createDamageAssignment(self, id):
        print "Creating damage assignment %d" % id

class NullOutput(Output):
    def deleteObject(self, obj):
        pass

    def createPlayer(self, id):
        pass

    def createCard(self, id):
        pass

    def createZone(self, id, owner, name):
        pass

    def createEffectObject(self, id):
        pass

    def createDamageAssignment(self, id):
        pass

def input_generator ():

    print greeting

    _as = yield None

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

            if isinstance(_as, ActionSet):
                for a in _as.actions:
                    print ("%d: %s"  % (i, a.text))
                    i += 1
            elif isinstance(_as, QueryNumber):
                print "Enter number: "


            try:

                # automatically pass if only mana abilities possible in a
                # priority

                autopass = True
                if _as.text != "You have priority":
                    autopass = False
                if isinstance(_as, ActionSet):
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
                if _input == "warranty":
                    print warranty
                if _input == "license":
                    lf = open("LICENSE.txt", "r")
                    for line in lf:
                        print line.rstrip()
                    lf.close()
                selected = int(_input)
                log.append(selected)
            except ValueError, x:
                selected = -1

            if isinstance(_as, ActionSet):
                if selected >= 0 and selected < len(_as.actions):
                    action = _as.actions[selected]
            elif isinstance(_as, QueryNumber):
                action = selected

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



