var manaclashServices = angular.module('manaclashServices', []);

manaclashServices.factory('EventBus', [
  function() {
    return new vertx.EventBus('http://localhost:8080/eventbus');
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

