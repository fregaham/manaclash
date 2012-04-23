# Copyright 2012 Marek Schmidt
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

import threading
from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import File

from autobahn.websocket import listenWS, connectWS
from autobahn.wamp import exportRpc, \
                          WampServerFactory, \
                          WampServerProtocol, \
                          WampClientFactory, \
                          WampClientProtocol

Context = threading.local()
g_factory = None

def player_to_role(game, player):
    for i in range(len(game.players)):
        if game.players[i] == player:
            return "player" + str(i + 1)
   
    raise Exception("No such player in the game.") 

def role_to_player(game, role):
    return game.players[int(role[len("player"):]) - 1]

def object_to_map(game, o):
    ret = {}
    ret["id"] = o.id
    ret["title"] = o.get_state().title
    ret["text"] = o.get_state().text

    return ret

def zone_to_list(game, zone):
    ret = []
    for o in zone.objects:
        ret.append (object_to_map(game, o))
    return ret

def ab_input_generator():
    seed = random.randint(0,2**64)
    random.seed(seed)

    _as = yield None

    while True:

        # send the game state
        state = {}
        state["player"] = player_to_role(_as.game, _as.player)
        state["text"] = _as.text
        state["turn"] = player_to_role(_as.game, _as.game.get_active_player())
        state["phase"] = _as.game.current_phase
        state["step"] = _as.game.current_step
       
        state["in_play"] = zone_to_list(_as.game, _as.game.get_in_play_zone())
        state["stack"] = zone_to_list(_as.game, _as.game.get_stack_zone())

        players = []
        for player in _as.game.players:
            p = {}
            p["role"] = player_to_role(_as.game, player)
            p["name"] = player.name
            p["life"] = player.life
            p["manapool"] = player.manapool
            p["hand"] = zone_to_list(_as.game, _as.game.get_hand(player))
            p["library"] = zone_to_list(_as.game, _as.game.get_library(player))
            p["graveyard"] = zone_to_list(_as.game, _as.game.get_graveyard(player))

            players.append(p)

        state["players"] = players

        actions = None
        query = None
        if isinstance(_as, ActionSet):
            actions = []
            for a in _as.actions:
                am = {}
                am["text"] = a.text
                if a.object is not None:
                    am["object"] = a.object.id
                if a.ability is not None:
                    am["ability"] = a.ability.get_text(a.object)
                if a.player is not None:
                    am["player"] = player_to_role(_as.game, a.player)
                actions.append(am)

        elif isinstance(_as, QueryNumber):
            query = "Enter number: "

        state["actions"] = actions
        state["query"] = query

        action = None
        while action == None:
            i = 0

            if isinstance(_as, ActionSet):
                for a in _as.actions:
                    print ("%d: %s"  % (i, a.text))
                    i += 1
            elif isinstance(_as, QueryNumber):
                print("Enter number: ")


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
                    _input = input()

                if _input == "log":
                    print("seed: %d" % seed)
                    print(repr(log))
                if _input == "exit":
                    return
                if _input == "warranty":
                    print(warranty)
                if _input == "license":
                    lf = open("LICENSE.txt", "r")
                    for line in lf:
                        print(line.rstrip())
                    lf.close()
                selected = int(_input)
                log.append(selected)
            except ValueError:
                selected = -1

            if isinstance(_as, ActionSet):
                if selected >= 0 and selected < len(_as.actions):
                    action = _as.actions[selected]
            elif isinstance(_as, QueryNumber):
                action = selected

        _as = yield action

class Game:
    def __init__ (self, id):
        self.id = id
        self.players = []

    def remove(self, player):
        self.players.remove(player)
        player.user.players.remove(player)

        Context.current_protocol.dispatch("http://manaclash.org/game/" + str(self.id) + "/remove", (player.user.login, player.role))

    def add(self, player):
        self.players.append(player)
        player.user.players.append(player)

        Context.current_protocol.dispatch("http://manaclash.org/game/" + str(self.id) + "/add", (player.user.login, player.role))

    def start(self):
        pass

class Player:
    def __init__ (self, user, game, role):
        self.user = user
        self.game = game
        self.role = role
        self.session_id = None

    def setSessionId(self, session_id):

        # publish a message about player going offline
        if self.session_id is not None and session_id is None:
            Context.current_protocol.dispatch("http://manaclash.org/game/" + str(self.game.id) + "/player/offline", (self.user.login, self.role))

        # publish a messasge about player online
        if self.session_id is None and session_id is not None:
            Context.current_protocol.dispatch("http://manaclash.org/game/" + str(self.game.id) + "/player/online", (self.user.login, self.role))

        self.session_id = session_id

class User:
    def __init__ (self, login, password):
        self.login = login
        self.password = password
        self.players = []

class Client:
    def __init__ (self, session_id):
        self.session_id = session_id
        self.user = None
        self.player = None

    def disconnect(self):
        if self.player is not None:
            self.player.setSessionId(None)
            self.player = None
        self.user = None


client_map = {}
user_map = {}
game_map = {}

last_game_id = 0

class MyServerProtocol(WampServerProtocol):

    def connectionLost(self, reason):

        client = client_map.get(self.session_id)
        if client is not None:
            client.disconnect()
            del client_map[self.session_id]

        # send an actual list of connected users
        self.dispatchUsers()

        WampServerProtocol.connectionLost(self, reason)

    def onSessionOpen(self):
        ## register a single, fixed URI as PubSub topic
        self.registerForPubSub("http://manaclash.org/users")
        self.registerForPubSub("http://manaclash.org/games")
        self.registerForPubSub("http://manaclash.org/game/", prefixMatch=True)

        self.registerMethodForRpc("http://manaclash.org/login", self, MyServerProtocol.onLogin)
        self.registerMethodForRpc("http://manaclash.org/games/create", self, MyServerProtocol.onGameCreate)
        self.registerMethodForRpc("http://manaclash.org/games/join", self, MyServerProtocol.onGameJoin)

        self.registerHandlerForSub("http://manaclash.org/users", self, MyServerProtocol.onUsersSub, prefixMatch=False)
        self.registerHandlerForSub("http://manaclash.org/games", self, MyServerProtocol.onGamesSub, prefixMatch=False)

        self.registerHandlerForPub("http://manaclash.org/users", self, MyServerProtocol.noPub, prefixMatch=False)
        self.registerHandlerForPub("http://manaclash.org/games", self, MyServerProtocol.noPub, prefixMatch=False)

    def noPub(self, url, foo, message):
        return False

    def onUsersSub(self, url, foo):
        # send a list of current users to the client subscribing for http://manaclash.org/users
        reactor.callLater(0, self.dispatchUsers, [], [self])
        return True

    def onGamesSub(self, url, foo):
        reactor.callLater(0, self.dispatchGames, [], [self])
        return True

    def onLogin(self, login, password):
        Context.current_protocol = self
        #print self.session_id
        #print "onPub " + `url` + ", " + `foo` + ", " + `message`
        print "client ", self.session_id, " is ", login, ", password: ", password

        client = client_map.get(self.session_id)
        if client is None:
            client = Client(self.session_id)
            client_map[self.session_id] = client
        else:
            # disconnect 
            client.disconnect()

        # create a new user or check password if such user exists
        user = user_map.get(login)
        if user is None:
            user = User(login, password)
            user_map[login] = user
        else:
            if user.password != password:
                user = None

        client.user = user

        if client.user is not None:
            self.dispatchUsers()

        return client.user is not None

    def onGameCreate(self):
        Context.current_protocol = self

        global last_game_id

        client = client_map.get(self.session_id)
        if client is not None and client.user is not None and client.player is None:
            last_game_id += 1

            game_id = last_game_id
            game = Game(game_id)

            player = Player(client.user, game, "player1")
            player.setSessionId(self.session_id)

            game.add(player)

            game_map[game_id] = game

            self.dispatchGames()
            return "http://manaclash.org/game/" + str(game_id)

        return None

    def onGameJoin(self, game_id, role):
        Context.current_protocol = self

        assert role == "player2"

        client = client_map.get(self.session_id)
        if client is not None and client.user is not None and client.player is None:
            game = game_map.get(game_id)
            if game is not None and len(game.players) < 2:
                player = Player(client.user, game, "player2")
                player.setSessionId(self.session_id)

                game.add(player)
                self.dispatchGames()
                return "http://manaclash.org/game/" + str(game.id)

        return False

    def dispatchUsers(self, exclude=[], eligible=None):
        self.dispatch("http://manaclash.org/users", map(lambda client:client.user.login, filter(lambda client:client.user is not None, client_map.values())), exclude, eligible)

    def dispatchGames(self, exclude=[], eligible=None):
        message = []
        for game in game_map.values():
            gm = {}
            gm["id"] = game.id

            players = []
            for p in game.players:
                pm = {}
                pm["login"] = p.user.login
                pm["role"] = p.role
                players.append(pm)

            gm["players"] = players

            message.append(gm)
        self.dispatch("http://manaclash.org/games", message, exclude, eligible)

#class MyClientProtocol(WampClientProtocol):

#    def onLogin(self, topicUri, login):
#        print "onLogin", self.session_id, topicUri, login
#        client_map[self.session_id] = login

#    def onSessionOpen(self):
#        global server_ids
#        server_ids.append(self.session_id)
#        self.subscribe("http://manaclash.org/login", self.onLogin)



if __name__ == '__main__':
    log.startLogging(sys.stdout)

    g_factory = WampServerFactory("ws://localhost:9000", debugWamp = True)
    g_factory.protocol = MyServerProtocol
    g_factory.setProtocolOptions(allowHixie76 = True)
    listenWS(g_factory)

    #factory = WampClientFactory("ws://localhost:9000")
    #factory.protocol = MyClientProtocol
    #connectWS(factory)

    webdir = File("web")
    web = Site(webdir)
    reactor.listenTCP(8080, web)

    reactor.run()
