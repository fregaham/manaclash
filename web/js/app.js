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
      when('/game', {
        templateUrl: 'partials/game.html',
        controller: 'GameCtrl'
      }).
      otherwise({
          redirectTo: '/login'
/*          redirectTo: '/game'*/
      });
  }]);

manaclashApp.run(function ($rootScope, $location) {
    $rootScope.$on('$locationChangeSuccess', function(object, newLocation, previousLocation) {
        if ($location.path() == '/game') {
            $rootScope.bgClass = 'bg-table';
        }
        else {
            $rootScope.bgClass = 'bg-default';
        }
    });
});

manaclashApp.filter('reverse', function() {
  return function(items) {
    return items.slice().reverse();
  };
});

