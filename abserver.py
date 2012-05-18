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

# TEMPORARY
import mc


from objects import Player
from mcio import Output
from game import Game
from process import process_game
from oracle import parseOracle
from actions import *
from abilities import BasicManaAbility

import random
import threading
from Queue import Queue
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

# read the oracle
g_cards = {}
oracleFile = open("oracle/8th_edition.txt", "r")
for card in parseOracle(oracleFile):
    g_cards[card.name] = card
oracleFile.close()

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
    ret["power"] = o.get_state().power
    ret["toughness"] = o.get_state().toughness
    ret["manacost"] = o.get_state().manacost
    ret["tags"] = [x for x in o.get_state().tags]
    ret["types"] = [x for x in o.get_state().types]
    ret["supertypes"] = [x for x in o.get_state().supertypes]
    ret["subtypes"] = [x for x in o.get_state().subtypes]
    ret["tapped"] = o.tapped

    if o.get_state().controller_id != None:
        ret["controller"] = player_to_role(game, game.objects[o.get_state().controller_id])
    else:
        ret["controller"] = None

    return ret

def zone_to_string(game, zone):
    if zone.player_id == None:
        return zone.type
    else:
        return game.objects[zone.player_id].name + "'s " + zone.type

def zone_to_list(game, zone):
    ret = []
    for o in zone.objects:
        ret.append (object_to_map(game, o))
    return ret

def ab_input_generator(ab_game):
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
                    # We don't treat players as objects on the client side
                    if isinstance(a.object, Player):
                        am["player"] = player_to_role(_as.game, a.object) 
                    else:
                        am["object"] = a.object.id
                if a.ability is not None:
                    am["ability"] = a.ability.get_text(_as.game, a.object)
                    if isinstance(a.ability, BasicManaAbility):
                        am["manaability"] = True
                if a.player is not None:
                    am["player"] = player_to_role(_as.game, a.player)
                actions.append(am)

        elif isinstance(_as, QueryNumber):
            query = "Enter number: "

        state["actions"] = actions
        state["query"] = query

        # Get the current ab_player by the role
        ab_game.current_player = None
        for ab_player in ab_game.players:
            if ab_player.role == state["player"]:
                ab_game.current_player = ab_player

        ab_game.current_state = state

        action = None
        while action == None:
            i = 0

            g_factory.dispatch("http://manaclash.org/game/" + str(ab_game.id) + "/state", state)

            client_player, client_message = ab_game.queue.get()

            # is the message from the proper client?
            if client_player == ab_game.current_player and client_message is not None:
                if isinstance(_as, ActionSet):
                    if client_message >= 0 and client_message < len(_as.actions):
                        action = _as.actions[client_message]
                        am = actions[client_message]
                        g_factory.dispatch("http://manaclash.org/game/" + str(ab_game.id) + "/action", (client_player.role, am))
                elif isinstance(_as, QueryNumber):
                    try:
                        action = int(client_message)
                        g_factory.dispatch("http://manaclash.org/game/" + str(ab_game.id) + "/number", (client_player.role, action))
                    except ValueError:
                        action = None

        ab_game.current_player = None
        _as = yield action

class ABOutput(Output):

    def __init__ (self, abgame):
        self.abgame = abgame

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

    def zoneTransfer(self, zoneFrom, zoneTo, obj):
        game = self.abgame.game
        g_factory.dispatch("http://manaclash.org/game/" + str(self.abgame.id) + "/zoneTransfer", (zone_to_string(game, zoneFrom), zone_to_string(game, zoneTo), object_to_map(game, obj)))

class ABGame:
    def __init__ (self, id):
        self.id = id
        self.players = []
        self.current_player = None
        self.current_state = None
        self.queue = Queue()
        self.game = None

    def remove(self, player):
        self.players.remove(player)
        player.user.players.remove(player)

        g_factory.dispatch("http://manaclash.org/game/" + str(self.id) + "/remove", (player.user.login, player.role))

    def add(self, player):
        self.players.append(player)
        player.user.players.append(player)

        g_factory.dispatch("http://manaclash.org/game/" + str(self.id) + "/add", (player.user.login, player.role))

    def start(self):
        output = ABOutput(self)
        ig = ab_input_generator(self)

        n = ig.next()
        self.game = Game(ig, output)
        self.game.create()

        c1 = mc.red_deck(self.game, g_cards)
        random.shuffle(c1)
        self.game.create_player(self.players[0].user.login, c1)

        c2 = mc.blue_deck(self.game, g_cards)
        random.shuffle(c2)
        self.game.create_player(self.players[1].user.login, c2)

        process_game(self.game)
        

class ABPlayer:
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

class ABUser:
    def __init__ (self, login, password):
        self.login = login
        self.password = password
        self.players = []

class ABClient:
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

        self.registerHandlerForPub("http://manaclash.org/game/", self, MyServerProtocol.onGamePrefixPub, prefixMatch=True)

    def noPub(self, url, foo, message):
        return False

    def onUsersSub(self, url, foo):
        # send a list of current users to the client subscribing for http://manaclash.org/users
        reactor.callLater(0, self.dispatchUsers, [], [self])
        return True

    def onGamesSub(self, url, foo):
        reactor.callLater(0, self.dispatchGames, [], [self])
        return True

    def onGamePrefixPub(self, url, foo, message):

        print "onGamePrefixPub url='" + url + "'"

        if "/" in foo:
            # TODO: check spoofed sender etc
            # some game sub-message, such as a player-to-player message
            return message
        else:
            # pure game message
            #game_id = int(url[len("http://manaclash.org/game/"):])
            game_id = int(foo)

            print "game_id: " + str(game_id)

            game = game_map.get(game_id)
            if game is not None:
                print "game is not None"
                if game.current_player is not None:
                    print "game.current_player is not None"
                    if game.current_player.session_id == self.session_id:
                        print "game.current_player.session_id == self.session_id"
                        # send the message to the game
                        game.queue.put( (game.current_player, message) )
                        return message

    def onLogin(self, login, password):
        Context.current_protocol = self
        #print self.session_id
        #print "onPub " + `url` + ", " + `foo` + ", " + `message`
        print "client ", self.session_id, " is ", login, ", password: ", password

        client = client_map.get(self.session_id)
        if client is None:
            client = ABClient(self.session_id)
            client_map[self.session_id] = client
        else:
            # disconnect 
            client.disconnect()

        # create a new user or check password if such user exists
        user = user_map.get(login)
        if user is None:
            user = ABUser(login, password)
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
            game = ABGame(game_id)

            player = ABPlayer(client.user, game, "player1")
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
                player = ABPlayer(client.user, game, "player2")
                player.setSessionId(self.session_id)

                game.add(player)
                self.dispatchGames()

                reactor.callLater(1, self.startGame, game.id)

                return "http://manaclash.org/game/" + str(game.id)

        return False

    def startGame(self, game_id):
        game = game_map.get(game_id)
        if game is not None:
            t = threading.Thread(target=game.start)
            t.daemon = True
            t.start()

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

