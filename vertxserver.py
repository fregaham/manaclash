import functools
import vertx
from core.event_bus import EventBus
from core.shared_data import SharedData

server = vertx.create_http_server()
shared_hash = SharedData.get_hash('manaclash.chat')

@server.request_handler
def request_handler(req):
    file = ''
    if req.path == '/':
        file = 'index.html'
    elif '..' not in req.path:
        file = req.path[1:]

        print `file`

    file = "web/" + file
    req.response.send_file(file)

sockJSServer = vertx.create_sockjs_server(server)
sockJSServer.bridge({'prefix' : '/eventbus'},
    [
        {'address':'chat'}, {'address':'list'}, {'address':'vertx.basicauthmanager.login'}, {'address':'register'}
    ],
    [])


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

def authorise_handler(fun, message):
    def reply_handler(reply):
        if reply.body["status"] == "ok":
            fun(message, reply.body["username"])

    EventBus.send('vertx.basicauthmanager.authorise', {
        "sessionID": message.body["sessionID"]
    }, reply_handler)

def chat_handler(message, username):
    print "chat by: " + username + " message:" + message.body["message"]

def deploy_handler(err, id):

    print "deploy handler: " + `err`

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
register_handler_id = EventBus.register_handler('register', handler=register_handler)
chat_handler_id = EventBus.register_handler('chat', handler=functools.partial(authorise_handler, chat_handler))

vertx.deploy_module('io.vertx~mod-mongo-persistor~2.1.0', {"address": "vertx.mongopersistor"},  handler=deploy_handler)
vertx.deploy_module('io.vertx~mod-auth-mgr~2.0.0-final')
# vertx.deploy_module('io.vertx~mod-mailer~2.0.0-final')

server.listen(8080, 'localhost')

