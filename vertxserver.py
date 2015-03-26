import functools
import vertx
import org.vertx.java.core.sockjs.EventBusBridgeHook

from core.event_bus import EventBus
from core.shared_data import SharedData
from collections import deque
from core.javautils import map_to_vertx, map_from_vertx

from vertxcommon import authorise_handler

server = vertx.create_http_server()

chat_history = deque()
chat_history_max = 32

sockjsaddr2username = SharedData.get_hash('manaclash.sockjsaddr2username')
online_users = {}


@server.request_handler
def request_handler(req):
    file = ''
    if req.path == '/':
        file = 'index.html'
    elif '..' not in req.path:
        file = req.path[1:]

#        print `file`

    file = "web/" + file
    req.response.send_file(file)

sockJSServer = vertx.create_sockjs_server(server)

class MyHook(org.vertx.java.core.sockjs.EventBusBridgeHook):
    def handleSocketCreated(self, j_sock):
        print "handleSocketCreated"
        return True

    def handleSocketClosed(self, j_sock):
        print "handleSocketClosed"
        pass

    def handleSendOrPub(self, j_sock, send, message, address):
        print "handleSendOrPub"
        return True

    def handlePreRegister(self, j_sock, address):
        print "handlePreRegister"
        return True

    def handlePostRegister(self, j_sock, address):
        print "handlePostRegister"

    def handleUnregister(self, j_sock, address):
        print "handleUnregister"
        return True

    def handleAuthorise(self, message, session_id, handler):
        print "handleAuthorise"
        return True

#myHook = MyHook()
#sockJSServer.java_obj.setHook(myHook)

bridge = sockJSServer.bridge({'prefix' : '/eventbus'},
    [
        {'address':'chat'}, {'address':'list'}, {'address':'vertx.basicauthmanager.login'}, {'address':'register'}, {'address':'chat_enter'}, {'address':'openForDuel'}, {'address':'joinDuel'}, {'address':'game.join'}, {'address_re':'game.action.*'}, {'address_re':'game.autopass.*'}
    ],
    [
        {'address':'onchat'}, {'address':'onusers'}, {'address':'game.started'}, {'address_re':'game.state.*'}
    ])

#def my_handler(sock, address):
#   print "my_handler"



#print `bridge.java_obj`

@bridge.socket_created_handler
def bridge_socket_created_handler(socket):
    print "my socket created, address: " + `socket.handler_id()`

@bridge.socket_closed_handler
def bridge_socket_closed_handler(socket):
    handler_id = socket.handler_id()
    if handler_id in sockjsaddr2username:
        username = sockjsaddr2username[handler_id]

        del sockjsaddr2username[handler_id]
        del online_users[username]

        EventBus.publish("user.leave", username)

        #print "%s leaves" % username

#    print "my socket closed"

#@bridge.authorise_handler
#def bridge_authorise_handler(msg, session, handler):
#    print "socket_authorise_handler"

@bridge.send_or_pub_handler
def bridge_send_or_pub_handler(sock, send, message, address):
    print "bridge_send_or_pub_handler: " + `message` + " sock: " + `sock.handler_id()`

    if message["body"].get("sessionID") != None:
        # associate SockJS address with username
        #print "sessionID: " + message["body"]["sessionID"]
        def reply_handler(reply):
            if reply.body["status"] == "ok":
                # sockjsaddr2username[reply.body["username"]] = sock.handler_id()
                username = reply.body["username"]
                sockjsaddr2username[sock.handler_id()] = username

                if username not in online_users:
                    online_users[username] = {"username" : username, "duel": False, "game": None}
                    EventBus.publish("user.enter", username)

        EventBus.send('vertx.basicauthmanager.authorise', {
            "sessionID": message["body"]["sessionID"]
        }, reply_handler)

#    print "bridge_send_or_pub_handler"

#bridge.authorise_handler(bridge_authorise_handler)

def register_handler(message):
    username = message.body["username"]
    password = message.body["password"]
    email = message.body["email"]

    assert len(username) < 128
    assert len(password) < 128
    assert len(email) < 1024

    def reply_handler(reply):

        print "reply: " + `reply.body`

        if reply.body["status"] == "ok":
            message.reply({"status":"ok"})
        elif "E11000 duplicate key error" in reply.body["message"]:
            message.reply({"status": "error", "message": "User already exist. Please choose a different username."})
        else:
            message.reply({"status": "error", "message": "Sorry, an error occured trying to register you."})

    EventBus.send('vertx.mongopersistor', {
            'action': 'save',
            'collection': 'users',
            'document': {
                'email': email,
                'username': username,
                'password': password
            }
    }, reply_handler)

def chat_handler(message, username):

    #print `message.address`
    #print `dir(message)`

    m = {"username": username, "message": message.body["message"]}
    chat_history.append (m)

    if len(chat_history) > chat_history_max:
        chat_history.popleft()

    EventBus.publish("onchat", m)

def chat_enter_handler(message, username):
    ch = []
    for c in chat_history:
        ch.append (c)
    message.reply({"messages":ch})

def online_users_handler(message):
    users = []
    for u in online_users.itervalues():
        users.append ( u )

    EventBus.publish("onusers", users)

def open_for_duel_handler(message, username):

    print `message.body`

    if username in online_users:
        online_users[username]["duel"] = message.body["open"]

    online_users_handler(message)    


def read_deck(deckname):

    deck = []

    f = open('decks/' + deckname + '.txt', 'r')
    for line in f:
        count, title = line.rstrip().split(" ", 1)
        deck.append ( (int(count), title.strip()) )

    f.close()

    return deck

def join_duel_handler(message, username):

    msg = {}

    msg["player1"] = username
    msg["player2"] = message.body["username"]

    # temporary hard coded data
       
    #msg["deck1"] = [[20, "Plains"]]
    #msg["deck2"] = [[20, "Swamp"]]

    msg["deck1"] = read_deck("Heavy Hitters")
    msg["deck2"] = read_deck("Speed Scorch")

    print "sending game.start " + `msg`

    EventBus.send("game.start", msg)


def deploy_handler(err, id):

    #print "deploy handler: " + `err`

    if err is None:

        def reply_handler(msg):
            print `msg.body`

        #EventBus.send('vertx.mongopersistor', {
        #    'action': 'command',
        #    'command': "{ createIndexes: 'users', indexes: [{key:'username', unique:true}] }"
        #    }, reply_handler)

        # And a user
        #EventBus.send('vertx.mongopersistor', {
        #    'action': 'save',
        #    'collection': 'users',
        #    'document': {
        #        'firstname': 'Foo',
        #        'lastname': 'Fooish',
        #        'email': 'foo@zemarov.org',
        #        'username': 'foo',
        #        'password': 'foo'
        #    }
        #})
        #EventBus.send('vertx.mongopersistor', {
        #    'action': 'save',
        #    'collection': 'users',
        #    'document': {
        #        'firstname': 'Bar',
        #        'lastname': 'Barish',
        #        'email': 'bar@zemarov.org',
        #        'username': 'bar',
        #        'password': 'bar'
        #    }
        #})

#def login_handler(message):
#    print "Login " + `message.body`

# login_handler_id = EventBus.register_handler('login', handler=login_handler)
EventBus.register_handler('register', handler=register_handler)
EventBus.register_handler('chat', handler=functools.partial(authorise_handler, chat_handler))
EventBus.register_handler('chat_enter', handler=functools.partial(authorise_handler, chat_enter_handler))
EventBus.register_handler('openForDuel', handler=functools.partial(authorise_handler, open_for_duel_handler))
EventBus.register_handler('joinDuel', handler=functools.partial(authorise_handler, join_duel_handler))

EventBus.register_handler('user.leave', handler=online_users_handler)
EventBus.register_handler('user.enter', handler=online_users_handler)

vertx.deploy_module('io.vertx~mod-mongo-persistor~2.1.0', {"address": "vertx.mongopersistor"},  handler=deploy_handler)
vertx.deploy_module('io.vertx~mod-auth-mgr~2.0.0-final')

vertx.deploy_worker_verticle("vertxworker.py", {})
# vertx.deploy_module('io.vertx~mod-mailer~2.0.0-final')

server.listen(8080, 'localhost')


print "XXX after server.listen"
