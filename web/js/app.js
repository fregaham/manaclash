'use strict';

/* App Module */

var manaclashApp = angular.module('manaclashApp', [
  'ngRoute',
  'manaclashControllers',
  'manaclashServices',
  'ui.bootstrap'
]);


manaclashApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/login', {
        templateUrl: 'partials/login.html',
        controller: 'LoginCtrl'
      }).
      when('/register', {
        templateUrl: 'partials/register.html',
        controller: 'RegisterCtrl'
      }).
      when('/lobby', {
        templateUrl: 'partials/lobby.html',
        controller: 'LobbyCtrl'
      }).
      otherwise({
        redirectTo: '/login'
      });
  }]);

manaclashApp.filter('reverse', function() {
  return function(items) {
    return items.slice().reverse();
  };
});

