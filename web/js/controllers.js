'use strict';

/* Controllers */

var manaclashControllers = angular.module('manaclashControllers', ['manaclashServices']);

manaclashControllers.controller('LoginCtrl', ['$scope', '$http', 'EventBus',
  function ($scope, $http, EventBus) {
    $scope.username = 'foo';
    $scope.password = 'bar';

    $scope.login = function() {
       EventBus.send("login", { "username" : $scope.username, "password": $scope.password } )
       //alert($scope.username + $scope.password);
    };
  }]);

