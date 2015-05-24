'use strict';

var decksService = angular.module('decksService', ['manaclashServices']);

decksService.factory('Decks', ['EventBus', 'SessionManager',
    function(EventBus, SessionManager) {
        var Decks = function(EventBus, SessionManager) {
            var that = this;

            that.eventBus = EventBus;
            that.sessionManager = SessionManager;

            that.deckname = null;
            that.decks = null;

            that.availableCards = null;

            that.readDecks = function(callback) {
                that.eventBus.send("deck.read", {'sessionID': that.sessionManager.sessionID}, function (readReply) {
                    that.deckname = readReply["deckname"];
                    that.decks = readReply["decks"];
                    that.availableCards = readReply["available"];

                    // alert(that.availableCards.toSource());

                    if (callback != null) {
                        callback(that.deckname, that.decks, that.availableCards);
                    }
                });
            }

            that.getDeckname = function() {
                return that.deckname;
            }

            that.getDecks = function() {
                return that.decks;
            }
        };

        return new Decks(EventBus, SessionManager);
    }]);