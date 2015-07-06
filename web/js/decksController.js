'use strict';

var decksController = angular.module('decksController', ['manaclashServices', 'decksService', 'cardsService']);

decksController.controller('DecksController', ['$scope', '$http', 'EventBus', 'SessionManager', 'Decks', 'Cards', '$location', '$timeout',
    function ($scope, $http, EventBus, SessionManager, Decks, Cards, $location, $timeout) {
        $scope.deckname = null;
        $scope.deck = [];
        $scope.decks = {};
        $scope.cards = null;

        $scope.filter = null;

        $scope.cardPopoverTemplate = "cardPopoverTemplate.html";
        $scope.currentCard = null;

        $scope.setCurrentCard = function(cardName) {
            $scope.currentCard = Cards.cards[cardName];
        }

        $scope.$on('$viewContentLoaded', function() {
            Decks.readDecks(function(deckname, decks, availableCards) {
                $scope.refreshCards();
            });

            Cards.readCards(function(cards) {
                $scope.refreshCards();
            });
        });

        $scope.refreshCards = function() {

            // alert("Cards.cards: " + Cards.cards + ", Decks.availableCards: " + Decks.availableCards);

            if (Cards.cards != null && Decks.availableCards != null) {
                $scope.$apply (function() {
                    var cards = [];
                    for (var i = 0; i < Decks.availableCards.length; ++i) {
                        var card = Cards.cards[Decks.availableCards[i]];
                        cards.push(card);
                    }

                    $scope.cards = cards;
                });
            }

            if (Decks.decks != null) {
                $scope.$apply(function () {
                    $scope.deckname = Decks.deckname;
                    $scope.decks = Decks.decks;
                    $scope.deck = Decks.decks[$scope.deckname];
                });
            }
        }

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
                $scope.deck.push([1, cardName]);
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