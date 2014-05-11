'use strict';

/* Controllers */

var manaclashControllers = angular.module('manaclashControllers', ['manaclashServices']);

manaclashControllers.controller('LoginCtrl', ['$scope', '$http', 'EventBus', 'SessionManager', '$location', '$timeout',
  function ($scope, $http, EventBus, SessionManager, $location, $timeout) {
    $scope.username = 'foo';
    $scope.password = 'bar';

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

manaclashControllers.controller('LobbyCtrl', ['$scope', '$http', 'EventBus',
  function ($scope, $http, EventBus) {
  }]);

