from core.event_bus import EventBus

def authorise_handler(fun, message):
    def reply_handler(reply):
        if reply.body["status"] == "ok":
            fun(message, reply.body["username"])

    EventBus.send('vertx.basicauthmanager.authorise', {
        "sessionID": message.body["sessionID"]
    }, reply_handler)


