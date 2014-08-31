from core.event_bus import EventBus

def authorise_handler(fun, message):
    def reply_handler(reply):
        print "authorise handler callback: " + `reply.body`
        if reply.body["status"] == "ok":
            print "authorise handler calling fun!"
            fun(message, reply.body["username"])

    EventBus.send('vertx.basicauthmanager.authorise', {
        "sessionID": message.body["sessionID"]
    }, reply_handler)


