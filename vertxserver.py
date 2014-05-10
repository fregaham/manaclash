import functools
import vertx
from core.event_bus import EventBus

server = vertx.create_http_server()

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
        {'address':'chat'}, {'address':'list'}, {'address':'login'}
    ],
    [])

def deploy_handler(err, id):
    if err is None:
        # And a user
        EventBus.send('vertx.mongopersistor', {
            'action': 'save',
            'collection': 'users',
            'document': {
                'firstname': 'Foo',
                'lastname': 'Fooish',
                'email': 'foo@zemarov.org',
                'username': 'foo',
                'password': 'foo'
            }
        })
        EventBus.send('vertx.mongopersistor', {
            'action': 'save',
            'collection': 'users',
            'document': {
                'firstname': 'Bar',
                'lastname': 'Barish',
                'email': 'bar@zemarov.org',
                'username': 'bar',
                'password': 'bar'
            }
        })

def login_handler(message):
    print "Login " + `message.body`

login_handler_id = EventBus.register_handler('login', handler=login_handler)

vertx.deploy_module('io.vertx~mod-mongo-persistor~2.0.0-final', handler=deploy_handler)
vertx.deploy_module('io.vertx~mod-auth-mgr~2.0.0-final')


server.listen(8080, 'localhost')

