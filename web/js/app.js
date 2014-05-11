'use strict';

/* App Module */

var manaclashApp = angular.module('manaclashApp', [
  'ngRoute',
  'manaclashControllers',
  'manaclashServices'
]);


manaclashApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/login', {
        templateUrl: 'partials/login.html',
        controller: 'LoginCtrl'
      }).
      when('/lobby', {
        templateUrl: 'partials/lobby.html',
        controller: 'LobbyCtrl'
      }).
      otherwise({
        redirectTo: '/login'
      });
  }]);


