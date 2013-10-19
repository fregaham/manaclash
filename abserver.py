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

from objects import Player
from mcio import Output
from game import Game
from process import MainGameProcess
from oracle import getParseableCards, createCardObject
from actions import *
from abilities import BasicManaAbility

import os
import os.path
import time
import random
import threading
import traceback

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

from autobahn.resource import WebSocketResource, HTTPChannelHixie76Aware

Context = threading.local()
g_factory = None

# read the oracle
g_card_names = []
g_cards = {}

for fname in os.listdir("oracle"):
    print ("reading %s " % fname)
    oracleFile = open(os.path.join("oracle", fname), "r")
    for card in getParseableCards(oracleFile):
        print card.name
        g_cards[card.name] = card
        g_card_names.append (card.name)

    oracleFile.close()

# read the initial decks
g_decks = {}
for fname in os.listdir("decks"):
    f = open(os.path.join("decks", fname), "r")
    if fname.endswith(".txt"):
        fname = fname[:-len(".txt")]
    deck = []
    for line in f:
        line = line.decode("utf8")
        count, card = line.split(None, 1)
        count = int(count)
        card = card.rstrip()

        if card in g_cards:
            deck.append ( (count, card) )
    g_decks[fname] = deck

    f.close()

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
    ret["enchanted_id"] = o.enchanted_id
        
    ret["targets"] = []
    for target in o.targets.values():
        ret["targets"].append(target.get_id())

    if o.get_state().controller_id != None:
        ret["controller"] = player_to_role(game, game.objects[o.get_state().controller_id])
    else:
        ret["controller"] = None

    ret["blockers"] = []
    ret["attackers"] = []

    ret["show_to"] = map(lambda x: player_to_role(game, game.objects[x]), o.get_state().show_to)
    
    for obj in game.declared_attackers:
        if o.id == obj.get_id():
            # Try to find a blocker
            for blocker_id, attacker_ids in game.declared_blockers_map.iteritems():
                for attacker_id in attacker_ids:
                    if o.id == attacker_id:
                        ret["blockers"].append(blocker_id)

    ret["attackers"] = game.declared_blockers_map.get(o.id, [])

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

def game_state(game):
    state = {}
    state["turn"] = player_to_role(game, game.get_active_player())
    state["phase"] = game.current_phase
    state["step"] = game.current_step
   
    state["in_play"] = zone_to_list(game, game.get_in_play_zone())
    state["stack"] = zone_to_list(game, game.get_stack_zone())

    state["revealed"] = []
    for o in game.revealed:
        state["revealed"].append( object_to_map(game, game.objects[o]) )

    players = []
    for player in game.players:
        p = {}
        p["role"] = player_to_role(game, player)
        p["name"] = player.name
        p["life"] = player.life
        p["manapool"] = player.manapool
        p["hand"] = zone_to_list(game, game.get_hand(player))
        p["library"] = zone_to_list(game, game.get_library(player))
        p["graveyard"] = zone_to_list(game, game.get_graveyard(player))

        players.append(p)

    state["players"] = players

    return state
   
def ab_game_state(_as):
    # send the game state
    state = game_state(_as.game)
    state["player"] = player_to_role(_as.game, _as.player)
    state["text"] = _as.text

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
                    am["player_object"] = player_to_role(_as.game, a.object) 
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

    return state
   

def ab_game_action(ab_game, client_player, client_message):

    _as = ab_game.current_actions
    actions = ab_game.current_state["actions"]
    game = ab_game.game

    action = None

    # is the message from the proper client?
    if client_player.user == ab_game.current_player.user and client_message is not None:
        if isinstance(_as, ActionSet):
            if client_message >= 0 and client_message < len(_as.actions):
                action = _as.actions[client_message]
                am = actions[client_message]
                g_factory.dispatch("http://manaclash.org/game/" + str(ab_game.id) + "/action", (ab_game.current_player.role, am))
        elif isinstance(_as, QueryNumber):
            try:
                action = int(client_message)
                g_factory.dispatch("http://manaclash.org/game/" + str(ab_game.id) + "/number", (ab_game.current_player.role, action))
            except ValueError:
                action = None

    if action is None:
        g_factory.dispatch("http://manaclash.org/game/" + str(ab_game.id) + "/state", state)

    else:
        _as = game.next(action)
  
        ab_game.current_actions = _as

        ab_game.current_state = ab_game_state(ab_game.current_actions)

        # Get the current ab_player by the role
        ab_game.current_player = None
        for ab_player in ab_game.players:
            if ab_player.role == ab_game.current_state["player"]:
                ab_game.current_player = ab_player

        g_factory.dispatch("http://manaclash.org/game/" + str(ab_game.id) + "/state", ab_game.current_state)


def ab_input_generator(ab_game):
    seed = random.randint(0,2**64)
    random.seed(seed)

    _as = yield None

    while True:

        # send the game state
        state = game_state(_as.game)
        state["player"] = player_to_role(_as.game, _as.player)
        state["text"] = _as.text

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
                        am["player_object"] = player_to_role(_as.game, a.object) 
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

            message = ab_game.queue.get()
            if message is None:
                return

            client_player, client_message = message

            # is the message from the proper client?
            if client_player.user == ab_game.current_player.user and client_message is not None:
                if isinstance(_as, ActionSet):
                    if client_message >= 0 and client_message < len(_as.actions):
                        action = _as.actions[client_message]
                        am = actions[client_message]
                        g_factory.dispatch("http://manaclash.org/game/" + str(ab_game.id) + "/action", (ab_game.current_player.role, am))
                elif isinstance(_as, QueryNumber):
                    try:
                        action = int(client_message)
                        g_factory.dispatch("http://manaclash.org/game/" + str(ab_game.id) + "/number", (ab_game.current_player.role, action))
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

        special = None
        if zoneFrom.type == "library" and zoneTo.type =="hand":
            special = "draw"

        elif zoneFrom.type == "hand" and zoneTo.type == "library":
            special = "put"

        g_factory.dispatch("http://manaclash.org/game/" + str(self.abgame.id) + "/zoneTransfer", (zone_to_string(game, zoneFrom), zone_to_string(game, zoneTo), object_to_map(game, obj), special))

    def gameEnds(self, winner):
        g_factory.dispatch("http://manaclash.org/game/" + str(self.abgame.id) + "/win", player_to_role(self.abgame.game, winner))

class ABGame:
    def __init__ (self, id):
        self.id = id
        self.players = []
        self.current_player = None
        self.current_state = None
        self.queue = Queue()
        self.game = None
        self.solitaire = False
        self.current_actions = None

    def remove(self, player):
        self.players.remove(player)
        player.user.players.remove(player)

        if player.client is not None:
            player.client.setPlayer(None)

        g_factory.dispatch("http://manaclash.org/game/" + str(self.id) + "/remove", (player.user.login, player.role))

    def add(self, player):
        self.players.append(player)
        player.user.players.append(player)

        if player.client is not None:
            player.client.setPlayer(player)

        g_factory.dispatch("http://manaclash.org/game/" + str(self.id) + "/add", (player.user.login, player.role))

    def start(self):

        print "game " + str(self.id) + " starting"

        output = ABOutput(self)

        self.game = Game(output)
        self.game.create()

        c1 = []
        for count, name in self.players[0].deck:
            for i in range(count):
                card = g_cards.get(name)
                if card is not None:
                    cardObject = createCardObject(self.game, card)
                    c1.append(cardObject)
                else:
                    print ("Card %s doesn't exist!" % name)

        random.shuffle(c1)

        self.game.create_player(self.players[0].user.login, c1)

        c2 = []
        for count, name in self.players[1].deck:
            for i in range(count):
                card = g_cards.get(name)
                if card is not None:
                    cardObject = createCardObject(self.game, card)
                    c2.append(cardObject)
                else:
                    print ("Card %s doesn't exist!" % name)

        random.shuffle(c2)
        self.game.create_player(self.players[1].user.login, c2)

        self.game.process_push(MainGameProcess())

        self.current_actions = self.game.next(None)

        self.current_state = ab_game_state(self.current_actions)

        # Get the current ab_player by the role
        self.current_player = None
        for ab_player in self.players:
            if ab_player.role == self.current_state["player"]:
                self.current_player = ab_player

        g_factory.dispatch("http://manaclash.org/game/" + str(self.id) + "/state", self.current_state)

    def end(self):
        g_factory.dispatch("http://manaclash.org/game/" + str(self.id) + "/state", self.current_state)
        players = self.players[:]
        for player in players:
            self.remove(player)
        self.game = None
        self.current_state = None
        self.current_player = None

        dispatchGames()
        reactor.callLater(1, startDuels)

        

class ABPlayer:
    def __init__ (self, client, user, game, role, deck):
        self.client = client
        self.user = user
        self.game = game
        self.role = role
        self.deck = deck

    def setClient(self, client):

        # publish a message about player going offline
        if self.client is not None and client is None:
            g_factory.dispatch("http://manaclash.org/game/" + str(self.game.id) + "/player/offline", (self.user.login, self.role))

        # publish a messasge about player online
        if self.client is None and client is not None:
            g_factory.dispatch("http://manaclash.org/game/" + str(self.game.id) + "/player/online", (self.user.login, self.role))

        self.client = client

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

        # available for duel?
        self.duel = False

        self.deck = None

    def disconnect(self):
        if self.player is not None:
            self.player.setClient(None)
            self.player = None
        self.user = None
        self.setDuel(False)

    def setPlayer(self, player):
        if self.player is not None:
            self.player.setClient(None)
        self.player = player
        if self.player is not None:
            self.player.setClient(self)

    def setDuel(self, duel):
        global available_for_duel
        self.duel = duel
        if duel is False:
            if self in available_for_duel:
                available_for_duel.remove(self)
        else:
            if self not in available_for_duel:
                available_for_duel.append(self)

    def setDeck(self, deck):
        self.deck = deck

client_map = {}
user_map = {}
game_map = {}
available_for_duel = []

duels = []

last_game_id = 0

chat_messages = []

def startGame(game_id):
    game = game_map.get(game_id)
    if game is not None:
        game.start()

#    game = game_map.get(game_id)
#    if game is not None:
#        t = threading.Thread(target=game.start)
#        t.daemon = True
#        t.start()


def joinGame(game, client, user, role, deck):
    player = ABPlayer(client, user, game, role, deck)

    game.add(player)
    dispatchGames()
    dispatchUsers()

    if len(game.players) == 2:
        reactor.callLater(1, startGame, game.id)


def startDuels():
    """ Check if we can start any duels and start them if so """
    global duels
#    global random_solitaire_clients
    global game_map

    # filter disconnected clients
    new_duels = []
    for cs in duels:
        connected = True
        for c in cs:
            if c.user is None:
                connected = False

        if connected:
            new_duels.append(cs)

    duels = new_duels

    for game in game_map.itervalues():
        if len(game.players) == 0:
            if len(duels) == 0:
                break

            print "XXX: will start game"

            game.solitaire = False
            # start the game
            client1, client2 = duels.pop()
            deck1, deck2 = client1.deck, client2.deck

            joinGame(game, client1, client1.user, "player1", deck1)
            joinGame(game, client2, client2.user, "player2", deck2)

            print "XXX: game should be started"


#    for game in game_map.itervalues():
#        if len(game.players) == 0:
#            if len(random_solitaire_clients) == 0:
#                break

#            game.solitaire = True
#            client, deck1, deck2 = random_solitaire_clients[0]
#            random_solitaire_clients = random_solitaire_clients[1:]

#            joinGame(game, client, client.user, "player1", deck1)
#            joinGame(game, None, client.user, "player2", deck2)
           

def dispatchUsers(exclude=[], eligible=None):

    global available_for_duel
    message = {}
    
    message["duel"] = map(lambda client:client.user.login, filter(lambda client:client.user is not None and client.player is None, available_for_duel))
    message["available"] = map(lambda client:client.user.login, filter(lambda client:client.user is not None and client.player is None, client_map.values()))
    message["playing"] = map(lambda client:client.user.login, filter(lambda client:client.user is not None and client.player is not None, client_map.values()))

    g_factory.dispatch("http://manaclash.org/users", message, exclude, eligible)

def dispatchGames(exclude=[], eligible=None):
    message = {}

    games = []
    for game in game_map.values():
        gm = {}
        gm["id"] = game.id
        gm["uri"] = "http://manaclash.org/game/" + str(game.id)

        players = []
        for p in game.players:
            pm = {}
            pm["login"] = p.user.login
            pm["role"] = p.role
            players.append(pm)

        gm["solitaire"] = game.solitaire

        gm["players"] = players

        games.append(gm)

    message["games"] = games

    # just the logins

    x2login = lambda x:x[0].user.login
    userfilter = lambda x:x[0].user != None

#    message["duel"] = map(x2login, filter(userfilter, random_duel_clients))
#    message["solitaire"] = map(x2login, filter(userfilter, random_solitaire_clients))

    g_factory.dispatch("http://manaclash.org/games", message, exclude, eligible)

def dispatchChatHistory(exclude=[], eligible=None):
    g_factory.dispatch("http://manaclash.org/chat_history", chat_messages[:], exclude, eligible)

class MyServerProtocol(WampServerProtocol):

    def unsetPlayer(self, client):
        # remove the game if all this is the only connected player in the game
        if client.player is not None and client.player.game is not None:
            game = client.player.game
            n = 0
            for player in game.players:
                if player.client is not None and player.client.session_id != self.session_id:
                    n += 1

            if n == 0:
                game.end()

        client.setPlayer(None)

    def connectionLost(self, reason):

        client = client_map.get(self.session_id)
        if client is not None:

            self.unsetPlayer(client)

            client.disconnect()
            del client_map[self.session_id]

        # send an actual list of connected users
        dispatchUsers()

        WampServerProtocol.connectionLost(self, reason)

    def onSessionOpen(self):
        ## register a single, fixed URI as PubSub topic
        self.registerForPubSub("http://manaclash.org/chat")
        self.registerForPubSub("http://manaclash.org/chat_history")

        self.registerForPubSub("http://manaclash.org/users")
        self.registerForPubSub("http://manaclash.org/games")
        self.registerForPubSub("http://manaclash.org/game/", prefixMatch=True)

        self.registerMethodForRpc("http://manaclash.org/setDeck", self, MyServerProtocol.onSetDeck)
        self.registerMethodForRpc("http://manaclash.org/availableForDuel", self, MyServerProtocol.onAvailableForDuel)
        self.registerMethodForRpc("http://manaclash.org/joinDuel", self, MyServerProtocol.onJoinDuel)
        self.registerMethodForRpc("http://manaclash.org/solitaire", self, MyServerProtocol.onSolitaire)
#        self.registerMethodForRpc("http://manaclash.org/cancel_duel", self, MyServerProtocol.onCancelDuel)

        self.registerMethodForRpc("http://manaclash.org/login", self, MyServerProtocol.onLogin)

        self.registerMethodForRpc("http://manaclash.org/takeover", self, MyServerProtocol.onTakeover)
        self.registerMethodForRpc("http://manaclash.org/refresh", self, MyServerProtocol.onRefresh)

        self.registerMethodForRpc("http://manaclash.org/getAvailableCards", self, MyServerProtocol.getAvailableCards)
        self.registerMethodForRpc("http://manaclash.org/getInitialDecks", self, MyServerProtocol.getInitialDecks)

        self.registerHandlerForSub("http://manaclash.org/chat",  self, MyServerProtocol.onChatSub, prefixMatch=False)
        self.registerHandlerForSub("http://manaclash.org/chat_history",  self, MyServerProtocol.onChatHistorySub, prefixMatch=False)

        self.registerHandlerForSub("http://manaclash.org/users", self, MyServerProtocol.onUsersSub, prefixMatch=False)
        self.registerHandlerForSub("http://manaclash.org/games", self, MyServerProtocol.onGamesSub, prefixMatch=False)

        self.registerHandlerForPub("http://manaclash.org/chat",  self, MyServerProtocol.onChatPub, prefixMatch=False)
        self.registerHandlerForPub("http://manaclash.org/chat_histroy", self, MyServerProtocol.noPub, prefixMatch=False)
        self.registerHandlerForPub("http://manaclash.org/users", self, MyServerProtocol.noPub, prefixMatch=False)
        self.registerHandlerForPub("http://manaclash.org/games", self, MyServerProtocol.noPub, prefixMatch=False)

        self.registerHandlerForPub("http://manaclash.org/game/", self, MyServerProtocol.onGamePrefixPub, prefixMatch=True)

    def noPub(self, url, foo, message):
        return False

    def getAvailableCards(self):
        ret = []
        for name in g_card_names:
            card = g_cards[name]
            o = {}
            o["title"] = card.name
            o["manacost"] = card.cost
            o["text"] = card.rules
            o["power"] = card.power
            o["toughness"] = card.toughness
            o["types"] = [x for x in card.types]
            o["subtypes"] = [x for x in card.subtypes]
            o["supertypes"] = [x for x in card.supertypes]
            o["tags"] = []

            if "U" in card.cost:
                o["tags"].append("blue")
            if "G" in card.cost:
                o["tags"].append("green")
            if "W" in card.cost:
                o["tags"].append("white")
            if "B" in card.cost:
                o["tags"].append("black")
            if "R" in card.cost:
                o["tags"].append("red")
            if len(o["tags"]) > 1:
                o["tags"].append("multicolor")

            ret.append(o)
        return ret

    def getInitialDecks(self):
        return g_decks.items()

    def onUsersSub(self, url, foo):
        # send a list of current users to the client subscribing for http://manaclash.org/users
        reactor.callLater(0, dispatchUsers, [], [self])
        return True

    def onGamesSub(self, url, foo):
        reactor.callLater(0, dispatchGames, [], [self])
        return True

    def onChatSub(self, url, foo):
        return True

    def onChatHistorySub(self, url, foo):
        reactor.callLater(0, dispatchChatHistory, [], [self])
        return True

    def onChatPub(self, url, foo, message):
        global chat_messages

        client = client_map.get(self.session_id)
        if client is not None:
            if client.user is not None:
                message = [int(time.time()), client.user.login, message]

                if len(chat_messages) > 32:
                    chat_messages = chat_messages[1:] + [message]
                else:
                    chat_messages = chat_messages + [message]

                return message

        return None

    def onGamePrefixPub(self, url, foo, message):

        if "/" in foo:
            client = client_map.get(self.session_id)
            game_id = int(foo[:foo.find("/")])
            game = game_map.get(game_id)
            if game is not None and client != None and client.player != None and client.player.game == game:
                if foo.endswith("/endgame"):
                    game.end()
                    return client.user.login
                else:
                    # some game sub-message, such as a player-to-player message
                    return message
            else:
                return None

        else:
            # pure game message
            #game_id = int(url[len("http://manaclash.org/game/"):])
            game_id = int(foo)
            client = client_map.get(self.session_id)

            game = game_map.get(game_id)
            if game is not None:
                if game.current_player is not None:
                    # we check the user is the same as the game's current player's user
                    if game.current_player.user is not None and game.current_player.user == client.user:
                        # send the message to the game
                        # game.queue.put( (game.current_player, message) )

                        try:
                            ab_game_action(game, game.current_player, message)
                        except Exception, x:
                            traceback.print_exc()

                        return message

    def onLogin(self, login, password):
        Context.current_protocol = self
        print "client ", self.session_id, " is ", login, ", password: ", password

        client = client_map.get(self.session_id)
        if client is None:
            client = ABClient(self.session_id)
            client_map[self.session_id] = client
        else:
            # disconnect 
            self.unsetPlayer(client)
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
            dispatchUsers()
            dispatchGames([], [self])

        return client.user is not None


    def onRandomDuel(self, deck):
        global random_duel_clients

        client = client_map.get(self.session_id)
        # We don't allow users to play more than one game at a time
        if client is not None and client.user is not None and (client.player is not None or len(client.user.players) > 0):
            return False

        # check that the client is not already in the list
        for c, d in random_duel_clients:
            if client == c:
                return False

        if client is not None and client.user is not None and client.player is None:
            random_duel_clients.append( (client, deck) )
            reactor.callLater(0, dispatchGames, [], [self])
            reactor.callLater(1, startDuels)
            return True

        return False

    def onAvailableForDuel(self, available):
        client = client_map.get(self.session_id)
        if client is not None and client.user is not None and client.deck is not None:
            client.setDuel(available)

            reactor.callLater(0, dispatchUsers)

            return True

        return False

    def onJoinDuel(self, username):

        global available_for_duel

        client = client_map.get(self.session_id)

        print "XXX: onJoinDuel(%s)" % username

        if client is not None and client.user is not None and client.deck is not None:
            for other_client in available_for_duel:
                if other_client.user is not None and other_client.user.login == username:

                    print "XXX: appending duels"

                    global duels
                    duels.append ([other_client, client])

                    startDuels() 

#                    reactor.callLater(0, dispatchUsers)
#                    reactor.callLater(0, dispatchGames)

                    return True

        return False
                

    def onSetDeck(self, deck):
        client = client_map.get(self.session_id)
        if client is not None and client.user is not None:
            # TODO: verify
            client.setDeck(deck)
            return True

        return False

    def onCancelDuel(self):
        global random_duel_clients
        global random_solitaire_clients

        client = client_map.get(self.session_id)

        if client is not None and client.user is not None:
            new_random_duel_clients = []
            for c, d in random_duel_clients:
                if client == c:
                    pass
                else:
                    new_random_duel_clients.append ( (c, d) )
            random_duel_clients = new_random_duel_clients

            new_solitaire_clients = []
            for c, d1, d2 in random_solitaire_clients:
                if client == c:
                    pass
                else:
                    new_solitaire_clients.append ( (c, d1, d2) )
            random_solitaire_clients = new_solitaire_clients

        reactor.callLater(0, dispatchGames, [], [self])


    def onSolitaire(self, deck1, deck2):
        global random_solitaire_clients
        client = client_map.get(self.session_id)
        # We don't allow users to play more than one game at a time
        if client is not None and client.user is not None and (client.player is not None or len(client.user.players) > 0):
            return False

        random_solitaire_clients.append ( (client, deck1, deck2) )

        reactor.callLater(1, startDuels)

        return True

    def onTakeover(self, game_id, role):
        Context.current_protocol = self

        client = client_map.get(self.session_id)

        # do we try to takeover a game/role we are already connected with?
        if client.player is not None and client.player.game.id == game_id and role == client.player.role:
            return ["http://manaclash.org/game/" + str(client.player.game.id), role]

        # disconnect the client from her current game
        if client is not None and client.user is not None and client.player is not None:
            self.unsetPlayer(client)

        # check that the player we are taking over exists and is the same user
        if client is not None and client.user is not None:
            game = game_map.get(game_id)
            if game is not None:
                for player in game.players:
                    if player.role == role:
                        if player.user.login == client.user.login:
                            client.setPlayer(player)
                            return ["http://manaclash.org/game/" + str(game.id), role]

        return None

    def onRefresh(self):
        dispatchUsers([], [self])
        dispatchGames([], [self])

        client = client_map.get(self.session_id)
        if client is not None and client.user is not None and client.player is not None and client.player.game is not None:
            game = client.player.game
            if game.current_state != None:
                g_factory.dispatch("http://manaclash.org/game/" + str(game.id) + "/state", game.current_state, [], [self])




#class MyClientProtocol(WampClientProtocol):

#    def onLogin(self, topicUri, login):
#        print "onLogin", self.session_id, topicUri, login
#        client_map[self.session_id] = login

#    def onSessionOpen(self):
#        global server_ids
#        server_ids.append(self.session_id)
#        self.subscribe("http://manaclash.org/login", self.onLogin)

def create_game():
    global last_game_id, game_map
    
    last_game_id += 1

    game_id = last_game_id
    game = ABGame(game_id)
    game_map[game_id] = game
    

if __name__ == '__main__':


    # Create game tables
    for i in range(4):
        create_game()

    log.startLogging(sys.stdout)

    g_factory = WampServerFactory("ws://localhost:8080")
    g_factory.protocol = MyServerProtocol

    g_factory.startFactory()

    resource = WebSocketResource(g_factory)

    root = File("web")

    root.putChild("ws", resource)

    site = Site(root)
    site.protocol = HTTPChannelHixie76Aware
    reactor.listenTCP(8080, site)

    reactor.run()


