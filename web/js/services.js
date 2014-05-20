var manaclashServices = angular.module('manaclashServices', []);

manaclashServices.factory('EventBus', [
  function() {
    eb = new vertx.EventBus('http://localhost:8080/eventbus');

    eb.myHandlers = [];

    eb.myHandler = function(address, callback) {
        if (eb.myInit) {
            eb.registerHandler(address, callback);
        }
        else {
            eb.myHandlers.push_back({'address': address, 'callback': callback});
        }
    }

    eb.onopen = function() {
        eb.myInit = true;
        eb.myHandlers.forEach(function (ac) {
            alert("registering handler");
            eb.registerHandler(ac["address"], ac["callback"]);
        });
        eb.myHandlers = [];
    };

    return eb;
  }
]);

manaclashServices.factory('SessionManager', ['EventBus',
  function(EventBus) {
    var SessionManager = function (EventBus) {
        var that = this;
        that.eventBus = EventBus;

        that.login = function(username, password, ok_callback, error_callback) {
            that.eventBus.send("vertx.basicauthmanager.login", { "username" : username, "password": password }, function (loginReply) {

                if (loginReply["status"] == "ok") {
                    that.sessionID = loginReply["sessionID"];
                    ok_callback();
                }
                else {
                    error_callback();
                }
            });
        }
    }

    return new SessionManager(EventBus);
  }
]);

