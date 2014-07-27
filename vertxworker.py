
import os
import uuid
import functools

import vertx
from core.event_bus import EventBus
from core.shared_data import SharedData
from collections import deque
from core.javautils import map_to_vertx, map_from_vertx

from mcio import Output, input_generator
from game import Game
from process import MainGameProcess
from oracle import getParseableCards, createCardObject, parseOracle
import random

from vertxcommon import authorise_handler

def parse_deckfile(deckfile):
    f = open(deckfile, 'r')

    for line in f:
        line = line.decode("utf8").rstrip()
        n, name = line.split(None, 1)

        yield (int(n), name)

    f.close()

# read the oracle
cards = {}
for fname in os.listdir("oracle"):
    print ("reading %s " % fname)
    oracleFile = open(os.path.join("oracle", fname), "r")
    for card in parseOracle(oracleFile):
        print card.name
        cards[card.name] = card

    oracleFile.close()

games = {}

def game_handler(message):
    pass

def game_start_handler(message):

    print "XXX game_start_handler"

    gameid = str(uuid.uuid1())

    player1 = message.body["player1"]
    player2 = message.body["player2"]

    deck1 = message.body["deck1"]
    deck2 = message.body["deck2"]

    unregister_id = EventBus.register_handler('game.' + gameid, handler=game_handler)

    games[gameid] = {'id': gameid, 'unregister_id' : unregister_id, 'player1': player1, 'player2': player2, 'player1_joined': False, 'player2_joined': False}

    output = Output()
    g = Game(output)

    games[gameid]['game'] = g

    g.create()

    c1 = []
    c2 = []
    
    for count, name in deck1:
        for i in range(count):
            card = cards.get(name)
            if card is not None:
                cardObject = createCardObject(g, card)
                c1.append(cardObject)
            else:
                print ("Card %s doesn't exist!" % name)

    for count, name in deck2:
        for i in range(count):
            card = cards.get(name)
            if card is not None:
                cardObject = createCardObject(g, card)
                c2.append(cardObject)
            else:
                print ("Card %s doesn't exist!" % name)
 
    random.shuffle(c1)
    random.shuffle(c2)

    g.create_player("Player1", c1)
    g.create_player("Player2", c2)

    g.process_push(MainGameProcess())

    print "sending game.started"

    #message.reply(gameid)
    EventBus.publish('game.started', {'id':gameid, 'player1': player1, 'player2': player2})

def player_to_role(game, player):
    for i in range(len(game.players)):
        if game.players[i] == player:
            return "player" + str(i + 1)

    raise Exception("No such player in the game.")

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
    for target_lki_id in o.targets.values():
        target = game.lki(target_lki_id)
        ret["targets"].append(target.get_id())

    if o.get_state().controller_id != None:
        ret["controller"] = player_to_role(game, game.objects[o.get_state().controller_id])
    else:
        ret["controller"] = None

    ret["blockers"] = []
    ret["attackers"] = []

    ret["show_to"] = map(lambda x: player_to_role(game, game.objects[x]), o.get_state().show_to)

    for lki_id in game.declared_attackers:
        obj = game.lki(lki_id)
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


def game_state(game, _as):

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

    state["player"] = player_to_role(game, game.obj(_as.player_id))
    state["text"] = _as.text

    actions = None
    query = None
    if isinstance(_as, ActionSet):
        actions = []
        for a in _as.actions:
            am = {}
            am["text"] = a.text
            if a.object_id is not None:
                # We don't treat players as objects on the client side
                if isinstance(game.obj(a.object_id), Player):
                    am["player_object"] = player_to_role(game, game.obj(a.object_id))
                else:
                    am["object"] = a.object_id
            if a.ability is not None:
                am["ability"] = a.ability.get_text(game, game.obj(a.object_id))
                if isinstance(a.ability, BasicManaAbility):
                    am["manaability"] = True
            if a.player_id is not None:
                am["player"] = player_to_role(game, game.obj(a.player_id))
            actions.append(am)

    elif isinstance(_as, QueryNumber):
        query = "Enter number: "

    state["actions"] = actions
    state["query"] = query

    return state

def game_send_state(game):
    state = game_state(game["game"], game["actions"])
    EvnetBus.publish('game.state.' + game["id"], state)

def game_input(game, action):
    game["actions"] = game["game"].next(action)
    game_send_state(game)

def game_join_handler(message, username):
    gameid = message.body["id"]
    game = games[gameid]

    if game["player1_joined"] and game["player2_joined"]:
        # already joined, just publish game state then
        game_send_state(game)
        return
    
    if game["player1"] == username:
        game["player1_joined"] = True
    
    if game["player2"] == username:
        game["player2_joined"] = True

    if game["player1_joined"] and game["player2_joined"]:
        game_input(game, None)

EventBus.register_handler('game.start', handler=game_start_handler)
EventBus.register_handler('game.join', handler=functools.partial(authorise_handler, game_join_handler))

