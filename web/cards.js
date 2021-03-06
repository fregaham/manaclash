
// List of available cards
var g_cards_available = [];
var g_cards_decknames = [];
var g_cards_decks = {};
var g_cards_available_map = {};
var g_cards_deckname = null;

var g_cards_solitaire_deck1 = null;
var g_cards_solitaire_deck2 = null;

// maps card title to card list plus buttons (to be able to enable/disable them)
var g_cards_plusbuttons = {};

function cards_init(sess) {
    if (g_cards_available.length == 0) {
        cards_setup();
    }

    $("#cards_deck_rename_input").keydown(function (e){
        if(e.keyCode == 13) {
            cards_deck_rename_confirm();
        }
    });
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

        var button = $("<button class='btn btn-small'><i class='icon-plus'></i></button>");
        tdButton = $("<td></td>");


        button.appendTo(tdButton);

        tr.append(tdButton);
        tbody.append(tr);

        button.click(function(card, event) {
            cards_deck_add_card(card);
        }.partial(card.title));

        g_cards_plusbuttons[card.title] = button.get(0);

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

function cards_update_decklist_navtabs(navtab, title, selected, selectFunction) {
    navtab.empty();
    $("<li class='nav-header'></li>").text(title).appendTo(navtab);

    for (var i = 0; i < g_cards_decknames.length; ++i) {
        var deckname = g_cards_decknames[i];
        var a = $("<a href='#' role='menuitem'></a>");
        a.text(deckname);

        a.click(selectFunction.partial(deckname));

        var li = $("<li></li>");
        li.append(a);
        navtab.append(li);

        if (selected == deckname) {
            li.addClass("active");
        }
    }
}

function cards_update_deck_table() {
    var tbody = $("#cards_decktable > tbody:last");
    tbody.empty();

    var deck = g_cards_decks[g_cards_deckname];

    if (deck == null) {
        return;
    }

    for (var i = 0; i < deck.length; ++i) {
        var count = deck[i][0];
        var cardname = deck[i][1];

        var card = g_cards_available_map[cardname];

        var fulltext =  card.title + " " + card.manacost + "\n " + card.supertypes.join(" ") + " " + card.types.join(" ");
        if (card.subtypes.length > 0) {
            fulltext += " - ";
        }
        fulltext += card.subtypes.join(" ") + " ";

        fulltext += "\n" + card.text;

        if (card.power != null) {
            fulltext += "\n " + card.power + "/" + card.toughness;
        }


        var a_title = $("<a href='#' data-toggle='tooltip' data-trigger='click' data-placement='left'></a>").text(card.title);
        a_title.attr("title", fulltext);

        a_title.tooltip();

        var tr = $("<tr></tr>");
        var tdTitle = $("<td></td>").append(a_title);
        var tdCost = $("<td></td>").text(card.manacost);
        var tdCount = $("<td></td>").text(count);
        var tdButtons = $("<td></td>");

        var btnPlus = $("<button class='btn btn-small'><i class='icon-plus'></i></button>");
        var btnMinus = $("<button class='btn btn-small'><i class='icon-minus'></i></button>");
        var btnGroup = $("<div class='btn-group'></div>");

        btnGroup.append(btnPlus);
        btnGroup.append(btnMinus);        
        tdButtons.append(btnGroup);

        tr.append(tdTitle);
        tr.append(tdCost);
        tr.append(tdCount);
        tr.append(tdButtons);
        
        tbody.append(tr);

        btnPlus.click(function(card, event) {
            cards_deck_add_card(card);
        }.partial(cardname));

        btnMinus.click(function(card, event) {
            cards_deck_remove_card(card);
        }.partial(cardname));

        if (count >= 4 && cardname != "Plains" && cardname != "Swamp" && cardname != "Mountain" && cardname != "Island" && cardname != "Forest") {
            btnPlus.attr("disabled", "disabled");
            var cardsButton = g_cards_plusbuttons[cardname];
            if (cardsButton != null) {
                $(cardsButton).attr("disabled", "disabled");
            }
        }
    }
    
}

function cards_select_deck(deckname) {
    g_cards_deckname = deckname;
    localStorage.cardsDeckname = deckname;
    cards_update_decks();    

    cards_set_server_deck();
}

function cards_update_decks() {
    cards_update_decklist_dropdown($("#lobby_deck_dropdown"), $("#lobby_deck_list"));
    cards_update_decklist_dropdown($("#cards_deck_dropdown"), $("#cards_deck_list"));
    cards_update_deck_table();

    cards_update_decklist_navtabs($("#lobby_solitaire_deck1"), "Deck 1", g_cards_solitaire_deck1, function (deck, e) {
        g_cards_solitaire_deck1 = deck;
        cards_update_decks();
    });

    cards_update_decklist_navtabs($("#lobby_solitaire_deck2"), "Deck 2", g_cards_solitaire_deck2, function (deck, e) {
        g_cards_solitaire_deck2 = deck;
        cards_update_decks();
    });

    cards_save();
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

function cards_save() {
    if(typeof(Storage)!=="undefined") {

        localStorage.cardsDeckname = g_cards_deckname;
        var decks = "";
        for (var i = 0; i < g_cards_decknames.length; i++) {
            decks += "n" + g_cards_decknames[i] + "\n";
            for (var j = 0; j < g_cards_decks[g_cards_decknames[i]].length; j++) {
                decks += "c" + g_cards_decks[g_cards_decknames[i]][j][0] + " " + g_cards_decks[g_cards_decknames[i]][j][1] + "\n";
            }
        }

        localStorage.cardsDecks = decks;
    }
}

function cards_deck_add_card(card) {
    var deck = g_cards_decks[g_cards_deckname];
    var found = false;
    for (var i = 0; i < deck.length; ++i) {
        var count = deck[i][0];
        var cardname = deck[i][1];
       
        if (cardname == card) {
            if (count < 4 || card == "Plains" || card == "Mountain" || card == "Swamp" || card == "Forest" || card == "Island") {
                deck[i][0] = count + 1;
            }

            found = true;
        }
    }

    if (!found) {
        deck.push([1, card]);
    }

    cards_update_decks();
}

function cards_deck_remove_card(card) {
    var deck = g_cards_decks[g_cards_deckname];
    for (var i = 0; i < deck.length; ++i) {
        var count = deck[i][0];
        var cardname = deck[i][1];

        if (cardname == card) {
            if (count > 1) {
                deck[i][0] = count - 1;
            }
            else {
                deck.splice(i, 1);
            }
        }
    }

    var cardsButton = g_cards_plusbuttons[card];
    if (cardsButton != null) {
        $(cardsButton).removeAttr("disabled");
    }

    cards_update_decks();
}

function cards_deck_rename() {
    $("#cards_deck_rename_input").val(g_cards_deckname);
    $('#cards_deck_rename_modal').modal('toggle');
}

function cards_deck_rename_confirm() {

    var newdeckname = $("#cards_deck_rename_input").val();

    var deck = g_cards_decks[g_cards_deckname];
    var i = g_cards_decknames.indexOf(g_cards_deckname);
    g_cards_decknames.splice(i, 1, newdeckname);
    g_cards_decks[newdeckname] = deck;
    g_cards_decks[g_cards_deckname] = null;

    g_cards_deckname = newdeckname;

    cards_update_decks();

    $("#cards_deck_rename_modal").modal("hide");
}

function cards_deck_delete() {
    $('#cards_deck_delete_modal').modal('toggle');
}

function cards_deck_delete_confirm() {

    var deck = g_cards_decks[g_cards_deckname];
    var i = g_cards_decknames.indexOf(g_cards_deckname);
    g_cards_decknames.splice(i, 1);

    g_cards_decks[g_cards_deckname] = null;

    g_cards_deckname = g_cards_decknames[0];

    cards_update_decks();

    $("#cards_deck_delete_modal").modal("hide");
}

function cards_deck_new_confirm() {
    var newdeckname = $("#cards_deck_new_input").val();
    if (newdeckname != null && newdeckname != "") {
        g_cards_decknames.push(newdeckname);
        g_cards_decks[newdeckname] = [];
        g_cards_deckname = newdeckname;

        cards_update_decks();

        $("#cards_deck_new_modal").modal("hide");
    }
}

/* Sends the current deck to the server */
function cards_set_server_deck() {
    var deck = g_cards_decks[g_cards_deckname];
    sess.call("http://manaclash.org/setDeck", deck);
}
