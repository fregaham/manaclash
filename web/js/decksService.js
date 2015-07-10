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
            };

            that.getDeckname = function() {
                return that.deckname;
            };

            that.getDecks = function() {
                return that.decks;
            };

            that.renameDeck = function(newname) {

                that.decks[newname] = that.decks[that.deckname];
                delete that.decks[that.deckname];

                that.deckname = newname;
            };

            that.save = function() {
                that.eventBus.send("deck.save", {'sessionID': that.sessionManager.sessionID, 'deckname': that.deckname, 'decks':that.decks});
            }
        };

        return new Decks(EventBus, SessionManager);
    }]);