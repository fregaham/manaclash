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
                    that.username = username;
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


manaclashServices.factory('Game', ['EventBus', 'SessionManager', 
    function(EventBus, SessionManager) {
        var Game = function(EventBus, SessionManager) {
            var that = this;

            that.eventBus = EventBus;
            that.sessionManager = SessionManager;

            that.unregister_id = null;
            that.gameid = null;

            that.gameHandler = function(message) {
                alert(message.toSource());
            }

            that.leaveGame = function() {
                 if (that.unregister_id != null) {
                    that.eventBus.unregisterHandler('game.state.' + that.gameid, that.gameHandler);
                    that.gameid = null;
                    that.unregister_id = null;
                }
            }

            that.joinGame = function(id) {
                that.leaveGame();

                that.gameid = id;
                that.unregister_id = EventBus.registerHandler('game.state.' + id, that.gameHandler);
                that.eventBus.send("game.join", {'sessionID': that.sessionManager.sessionID, 'id': id});
            }

            that.eventBus.myHandler('game.started', function(message) {
                if (message.player1 == that.sessionManager.username || message.player2 == that.sessionManager.username) {
                    that.joinGame(message.id);
                }
            });
        }

        return new Game(EventBus, SessionManager);
    }
]);

