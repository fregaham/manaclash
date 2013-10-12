
// List of available cards
var g_cards_available = [];
var g_cards_decknames = [];
var g_cards_decks = {};
var g_cards_available_map = {};
var g_cards_deckname = null;

function cards_init(sess) {
    if (g_cards_available.length == 0) {
        cards_setup();
    }
}

function cards_update_decks_available_cards() {
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

function cards_update_decklist_dropdown(toggle, list) {
    toggle.empty();
    toggle.text(g_cards_deckname);
    toggle.append($(" <span class='caret'>"));

    list.empty();
    for (var i = 0; i < g_cards_decknames.length; ++i) {
        var deckname = g_cards_decknames[i];
        var a = $("<a href='#' role='menuitem'></a>");
        a.text(deckname);

        a.click(function(deckname, event) {
            cards_select_deck(deckname);
        }.partial(deckname));

        var li = $("<li role='presentation'></li>");
        li.append(a);
        list.append(li);
    }
}

function cards_update_deck_table() {
    var tbody = $("#cards_decktable > tbody:last");
    tbody.empty();

    var deck = g_cards_decks[g_cards_deckname];
    for (var i = 0; i < deck.length; ++i) {
        var count = deck[i][0];
        var cardname = deck[i][1];

        var card = g_cards_available_map[cardname];

        var tr = $("<tr></tr>");
        var tdTitle = $("<td></td>").text(card.title);
        var tdCost = $("<td></td>").text(card.manacost);
        var tdCount = $("<td></td>").text(count);
        var tdButtons = $("<td></td>");


        tr.append(tdTitle);
        tr.append(tdCost);
        tr.append(tdCount);
        tr.append(tdButtons);
        
        tbody.append(tr);
    }
    
}

function cards_select_deck(deckname) {
    g_cards_deckname = deckname;
    localStorage.cardsDeckname = deckname;
    cards_update_decks();    
}

function cards_update_decks() {
    cards_update_decklist_dropdown($("#lobby_deck_dropdown"), $("#lobby_deck_list"));
    cards_update_decklist_dropdown($("#cards_deck_dropdown"), $("#cards_deck_list"));
    cards_update_deck_table();
}

function cards_update_all() {
    cards_update_decks_available_cards();
    cards_update_decks();
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

                            g_cards_deckname = decks[0][0];
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
                                    if (g_cards_decknames.indexOf(deckname) == -1) {
                                        g_cards_decknames.push(deckname);
                                        g_cards_decks[deckname] = deck;
                                    }
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
                        if (g_cards_decknames.indexOf(deckname) == -1) {
                            g_cards_decknames.push(deckname);
                            g_cards_decks[deckname] = deck;
                        }
                    }

                    g_cards_deckname = localStorage.cardsDeckname;
                    if (g_cards_deckname == null) {
                        g_cards_deckname = g_cards_decks[g_cards_decknames[0]];
                    }
                }
            }

            cards_update_all();
        },
        function(){ alert("failed to fetch available cards!"); }
    );
}
