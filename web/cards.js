
// List of available cards
var g_cards_available = [];
var g_cards_decknames = [];
var g_cards_decks = {};
var g_cards_available_map = {};

function cards_init(sess) {
    if (g_cards_available.length == 0) {
        cards_setup();
    }
}

function cards_update_decks_menus() {
    var tbody = $("#cards_cardtable > tbody:last");
    for (var i = 0; i < g_cards_available.length; i++) {
        var card = g_cards_available[i];

        var tr = $("<tr></tr>");
        var tdTitle = $("<td></td>").text(card.title);
        var tdCost = $("<td></td>").text(card.manacost);

        var tdType = $("<td></td>");
        tdType.text(card.supertypes.join(" ") + " " + card.types.join(" "));
        if (card.subtypes.length > 0) {
            tdType.append(" &ndash; ");
        }
        tdType.append(card.subtypes.join(" "));

        var tdPower = $("<td></td>");
        if (card.power != null) {
            tdPower.text(card.power + "/" + card.toughness);
        } 

        var tdText = $("<td></td>");
        tdText.text(card.text);

        tr.append(tdTitle);
        tr.append(tdCost);
        tr.append(tdType);
        tr.append(tdPower);
        tr.append(tdText);
        tr.append($("<td><button class='btn btn-small'><i class='icon-plus'></i></button></td>"));
        tbody.append(tr);

/*       tbody.append("<tr><td>" + " </td> <td>2BB</td> <td>Creature - Specter</td> <td>2/4</td> <td>Flying Whenever Abyssal Specter deals damage to a player, that player discards a card.</td><td><button class="btn btn-small" disabled><i class="icon-plus"></i></button></td></tr>)*/
    }

    $('#cards_cardtable').dataTable({"bAutoWidth": false} );
}

function cards_setup() {
    /* Reads available cards from the server and loads decks from the local storage */
    sess.call("http://manaclash.org/getAvailableCards").then(
        function(result) {
            g_cards_available = result;

            $("#cards_available").empty();

            for (var i = 0; i < g_cards_available.length; i++) {
                var card = g_cards_available[i];
                // $("<option value=\"" + card.title + "\">" + card.title +  "</option>").appendTo($("#cards_available"));

                g_cards_available_map[card.title] = card;
            }
/*
            if(typeof(Storage)!=="undefined") {
                var decks = localStorage.cardsDecks;

                if (decks == null || decks == "") {
                    sess.call("http://manaclash.org/getInitialDecks").then(
                        function (decks) {
                            for (var i = 0; i < decks.length; i++) {
                                var deckname = decks[i][0];
                                var decklist = decks[i][1];

                                var deck = [];
                                for (var j = 0; j < decklist.length; j++) {
                                    deck.push([decklist[j][0], decklist[j][1]]);
                                }
                                g_cards_decknames.push(deckname);
                                g_cards_decks[deckname] = deck;
                            }

                            // cardsSelectDeck();
                        }
                    );
                }
                else {
                    decks = decks.split("\n");
                    var deck = [];
                    var deckname = null;
                    for (var i = 0; i < decks.length; i++) {
                        if (decks[i] != "") {
                            if (decks[i][0] == "n") {
                                if (deck.length > 0) {
                                    g_cards_decknames.push(deckname);
                                    g_cards_decks[deckname] = deck;
                                    deck = [];
                                    deckname = null;
                                }
                                deckname = decks[i].substr(1);
                            }
                            else if (decks[i][0] == "c") {
                                var s = decks[i].substr(1);
                                var num = s.split(" ", 1);
                                var name = $.trim(s.substr(num.length + 1));
                                deck.push([parseInt(num), name]);
                            }
                        }
                    }

                    if (deck.length > 0) {
                        g_cards_decknames.push(deckname);
                        g_cards_decks[deckname] = deck;
                    }
                }
            } */

            cards_update_decks_menus();
        },
        function(){ alert("failed to fetch available cards!"); }
    );
}
