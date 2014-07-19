'use strict';

/* Controllers */

var manaclashControllers = angular.module('manaclashControllers', ['manaclashServices']);

manaclashControllers.controller('LoginCtrl', ['$scope', '$http', 'EventBus', 'SessionManager', '$location', '$timeout',
  function ($scope, $http, EventBus, SessionManager, $location, $timeout) {
    $scope.username = 'foo';
    $scope.password = 'foo';

    $scope.error = '';

    $scope.login = function() {
       SessionManager.login($scope.username, $scope.password, function () {
          $timeout(function() { $location.path('/lobby'); });
       },

       function () {
          $scope.$apply (function() {
             $scope.error = "Wrong username / password";
          });
       });
    };
  }]);

manaclashControllers.controller('RegisterCtrl', ['$scope', '$http', 'EventBus', 'SessionManager', '$location', '$timeout',
  function ($scope, $http, EventBus, SessionManager, $location, $timeout) {
    $scope.username = '';
    $scope.email = '';
    $scope.password = '';
    $scope.password2 = '';

    $scope.register = function() {
        if ($scope.password != $scope.password2) {
          $scope.error = "Passwords must match!";
        }
        else {
            //alert("Registering");
            EventBus.send("register", {'username': $scope.username, 'password': $scope.password, 'email': $scope.email}, function (reply) {
                if (reply["status"] != "ok") {
                    $scope.$apply (function() {
                        $scope.error = reply["message"];
                    });
                }
                else {
                    SessionManager.login($scope.username, $scope.password, 
                        function () {
                            $timeout(function() { $location.path('/lobby'); });
                        }, 
                        function () {
                            $scope.$apply (function() {
                                $scope.error = "Error logging in with the new username. Please try again later.";
                            });
                        }
                    );
                }
            });
        }
    }
  }]);

manaclashControllers.controller('LobbyCtrl', ['$scope', '$http', 'EventBus', 'SessionManager',
  function ($scope, $http, EventBus, SessionManager) {
    $scope.message = '';
    $scope.messages = [];

    $scope.users = [];
    $scope.openForDuel = false;

    EventBus.myHandler('onchat', function(message) {
        $scope.$apply (function() {
            $scope.messages.push(message);
        });

/*        alert('chat ' + message["username"] + ": " + message["message"] );*/
    });

    EventBus.myHandler('onusers', function(message) {
        $scope.$apply (function() {
            $scope.users = message;
        });
    });

    EventBus.send("chat_enter", {'sessionID': SessionManager.sessionID}, function(reply) {
        $scope.$apply (function() {
            $scope.messages = reply["messages"];
        });
    });

    $scope.chat = function() {
        if ($scope.message) {
            EventBus.send("chat", {'sessionID': SessionManager.sessionID, 'message': $scope.message})
            $scope.message = '';
        }
    }

    $scope.onOpenForDuel = function(t) {
        EventBus.send("openForDuel", {'sessionID': SessionManager.sessionID, 'open':t})
    }
  }]);


