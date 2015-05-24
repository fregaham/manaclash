'use strict';

var cardsService = angular.module('cardsService', ['manaclashServices']);

cardsService.factory('Cards', ['EventBus',
    function(EventBus) {
        var Cards = function(EventBus) {
            var that = this;

            that.eventBus = EventBus;

            that.cards = null;

            that.readCards = function(callback) {
                that.eventBus.send("cards", {}, function (readReply) {
                    that.cards = readReply;

                    if (callback != null) {
                        callback(that.cards);
                    }
                });
            }
        };

        return new Cards(EventBus);
    }]);