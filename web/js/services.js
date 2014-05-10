var manaclashServices = angular.module('manaclashServices', []);

manaclashServices.factory('EventBus', [
  function() {
    return new vertx.EventBus('http://localhost:8080/eventbus');
  }
]);

