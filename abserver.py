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

class Game:
    def __init__ (self, id):
        self.id = id
        self.players = []

    def remove(self, player):
        self.players.remove(player)
        player.user.players.remove(player)

        threading.local().current_protocol.dispatch("http://manaclash.org/game/" + self.id + "/remove", (player.user.login, player.role))

    def add(self, player):
        self.players.append(player)
        player.user.players.append(player)

        threading.local().current_protocol.dispatch("http://manaclash.org/game/" + self.id + "/add", (player.user.login, player.role))

class Player:
    def __init__ (self, user, game, role):
        self.user = user
        self.game = game
        self.role = role
        self.session_id = None

    def setSessionId(self, session_id):

        # publish a message about player going offline
        if self.session_id is not None and session_id is None:
            threading.local().current_protocol.dispatch("http://manaclash.org/game/" + self.game.id + "/player/offline", (self.user.login, self.role))

        # publish a messasge about player online
        if self.session_id is None and session_id is not None:
            threading.local().current_protocol.dispatch("http://manaclash.org/game/" + self.game.id + "/player/online", (self.user.login, self.role))

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

        self.registerMethodForRpc("http://manaclash.org/login", self, MyServerProtocol.onLogin)

        self.registerHandlerForSub("http://manaclash.org/users", self, MyServerProtocol.onUsersSub, prefixMatch=False)
        #self.registerHandlerForPub("http://manaclash.org/login", self, MyServerProtocol.onLoginPub, prefixMatch=False)

    def onUsersSub(self, url, foo):
        # send a list of current users to the client subscribing for http://manaclash.org/users
        reactor.callLater(0, self.dispatchUsers, [], [self])
        return True

    def onLogin(self, login, password):
        threading.local().current_protocol = self
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

    def dispatchUsers(self, exclude=[], eligible=None):
        self.dispatch("http://manaclash.org/users", map(lambda client:client.user.login, filter(lambda client:client.user is not None, client_map.values())), exclude, eligible)

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

    factory = WampServerFactory("ws://localhost:9000", debugWamp = True)
    factory.protocol = MyServerProtocol
    factory.setProtocolOptions(allowHixie76 = True)
    listenWS(factory)

    #factory = WampClientFactory("ws://localhost:9000")
    #factory.protocol = MyClientProtocol
    #connectWS(factory)

    webdir = File("web")
    web = Site(webdir)
    reactor.listenTCP(8080, web)

    reactor.run()

