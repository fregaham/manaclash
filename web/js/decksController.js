'use strict';

var decksController = angular.module('decksController', ['manaclashServices', 'decksService']);

decksController.controller('DecksController', ['$scope', '$http', 'EventBus', 'SessionManager', 'Decks', '$location', '$timeout',
    function ($scope, $http, EventBus, SessionManager, Decks, $location, $timeout) {
        $scope.deckname = null;
        $scope.deck = [];
        $scope.decks = {};

        $scope.$on('$viewContentLoaded', function() {
            Decks.readDecks(function(deckname, decks) {
                $scope.$apply (function() {
                    $scope.deckname = deckname;
                    $scope.decks = decks;
                    $scope.deck = decks[deckname];
                });
            })
        });

        $scope.deckInc = function(cardName) {
            var found = false;

            for (var i = 0; i < $scope.deck.length; ++i) {
                if ($scope.deck[i][1] == cardName) {
                    $scope.deck[i][0] += 1;
                    found = true;
                    break;
                }
            }

            if (!found) {
                $scope.deck.append([1, cardName]);
            }
        }

        $scope.deckDec = function(cardName) {
            for (var i = 0; i < $scope.deck.length; ++i) {
                if ($scope.deck[i][1] == cardName) {
                    $scope.deck[i][0] -= 1;

                    if ($scope.deck[i][0] <= 0) {
                        $scope.deck.splice(i, 1);
                    }

                    break;
                }
            }
        }
    }]);