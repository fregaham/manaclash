'use strict';

var decksController = angular.module('decksController', ['manaclashServices', 'decksService', 'cardsService']);

decksController.controller('DecksController', ['$scope', '$http', 'EventBus', 'SessionManager', 'Decks', 'Cards', '$location', '$timeout', '$modal',
    function ($scope, $http, EventBus, SessionManager, Decks, Cards, $location, $timeout, $modal) {
        $scope.deckname = null;
        $scope.deck = [];
        $scope.decks = {};
        $scope.cards = null;

        $scope.filter = null;

        $scope.cardPopoverTemplate = "cardPopoverTemplate.html";
        $scope.currentCard = null;

        $scope.back = function() {
            $location.path('/lobby');
        };

        $scope.setCurrentCard = function(cardName) {
            $scope.currentCard = Cards.cards[cardName];
        };

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
                $timeout (function() {
                    var cards = [];
                    for (var i = 0; i < Decks.availableCards.length; ++i) {
                        var card = Cards.cards[Decks.availableCards[i]];
                        cards.push(card);
                    }

                    $scope.cards = cards;
                });
            }

            if (Decks.decks != null) {
                $timeout(function () {
                    $scope.deckname = Decks.deckname;
                    $scope.decks = Decks.decks;
                    $scope.deck = Decks.decks[$scope.deckname];
                });
            }
        };

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

            Decks.save();
        };

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

            Decks.save();
        };

        $scope.rename = function() {
            var modalInstance = $modal.open({
                templateUrl: 'deckRename.html',
                controller: 'DecksRenameCtrl',
                // size: 'lg',
                resolve: {
                    deckName: function () {
                        return $scope.deckname;
                    }
                }
            });

            modalInstance.result.then(function (newName) {
                Decks.renameDeck(newName);
                Decks.save();
                $scope.refreshCards();
            }, function () {
                // nop
            });
        };

        $scope.save = function() {
            Decks.save();
        };

        $scope.selectDeck = function(dname) {
            Decks.selectDeck(dname);
            Decks.save();
            $scope.refreshCards();
        };

        $scope.newDeck = function() {

            var modalInstance = $modal.open({
                templateUrl: 'deckNew.html',
                controller: 'DecksRenameCtrl',
                resolve: {
                    deckName: function () {
                        return "New Deck";
                    }
                }
            });

            modalInstance.result.then(function (newName) {
                $scope.decks[newName] = [];
                Decks.selectDeck(newName);
                Decks.save();
                $scope.refreshCards();
            }, function () {
                // nop
            });
        };

        $scope.delete = function() {
            var modalInstance = $modal.open({
                templateUrl: 'deckDelete.html',
                controller: 'DecksDeleteCtrl',
                resolve: {
                    deckName: function () {
                        return $scope.deckname;
                    }
                }
            });

            modalInstance.result.then(function () {
                Decks.delete();
                Decks.save();
                $scope.refreshCards();
            }, function () {
                // nop
            });
        };

    }]);

decksController.controller('DecksRenameCtrl', ['$scope', '$modalInstance', 'deckName',
    function ($scope, $modalInstance, deckName) {
        $scope.deckName = deckName;

        $scope.cancel = function() {
            $modalInstance.dismiss('cancel');
        };

        $scope.save = function() {
            $modalInstance.close($scope.deckName);
        }
    }]);

decksController.controller('DecksDeleteCtrl', ['$scope', '$modalInstance', 'deckName',
    function ($scope, $modalInstance, deckName) {
        $scope.deckName = deckName;

        $scope.cancel = function() {
            $modalInstance.dismiss('cancel');
        };

        $scope.ok = function() {
            $modalInstance.close();
        }
    }]);
