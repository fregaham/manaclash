
function lobby_init(sess) {
    sess.subscribe("http://manaclash.org/chat", lobby_onChat);
    sess.subscribe("http://manaclash.org/chat_history", lobby_onChatHistory);

    $("#lobby_chat_input").keydown(function (e){
        if(e.keyCode == 13) {
            lobby_chat_send();
        }
    })

    $("#lobby_open_duel_radio").button();
    $("#lobby_open_duel_no").button("toggle");

    $("#lobby_open_duel_yes").click(function (e) {
        lobby_open_duel(true);
    });

    $("#lobby_open_duel_no").click(function (e) {
        lobby_open_duel(false);
    });

    sess.subscribe("http://manaclash.org/users", lobby_onUsers);
    sess.subscribe("http://manaclash.org/games", lobby_onGames);
}

function lobby_open_duel(open) {
    sess.call("http://manaclash.org/availableForDuel", open)
}

function lobby_join_duel(username) {
    sess.call("http://manaclash.org/joinDuel", username);
}

function lobby_chat_format(message) {
    var date = new Date(message[0] * 1000);
    var login = message[1];
    var content = message[2];
    var msg = $("<div class='message'></div>");

    var date_formatted = date.toLocaleDateString() + " " + date.toLocaleTimeString();
    if (date.toLocaleDateString() == (new Date()).toLocaleDateString()) {
        date_formatted = date.toLocaleTimeString();
    }

    msg.append(date_formatted + " ");
    $("<b></b>").text(login + ": ").appendTo(msg);
    $("<span></span>").text(content).appendTo(msg);
    return msg;
}

function lobby_onChat(topicUri, message) {
    var msg = lobby_chat_format(message);
    msg.prependTo($("#lobby_chat_messages"));
}

function lobby_onChatHistory(topicUri, messages) {
    for (var i = 0; i < messages.length; i++) {
        var msg = lobby_chat_format(messages[i]);
        msg.prependTo($("#lobby_chat_messages"));
    }
}

function lobby_chat_send() {
    if ($("#lobby_chat_input").val().length > 0) {
        sess.publish("http://manaclash.org/chat", $("#lobby_chat_input").val(), false);
        $("#lobby_chat_input").val("");
    }
}


function lobby_onUsers(topicUri, msg) {

    $("#lobby_available_players").empty();
    $("#lobby_duel_players").empty();

    $("<li class='nav-header'>Players open to a duel</li>").appendTo($("#lobby_duel_players"));
    $("<li class='nav-header'>Available Players</li>").appendTo($("#lobby_available_players"));

    var duel = msg["duel"];
    var available = msg["available"];

    for (var i = 0; i < duel.length; i++) {
        var user = duel[i]; 

        var li = $("<li></li>");
        var a = $("<a href='#'></a>").text(user);

        var button = $("<button type='button' class='btn pull-right btn-small' style='margin-top:-3px'>Join Duel</button>");
        button.hide();
        button.appendTo(a);

        button.click(function (user, e) {
            lobby_join_duel(user);
        }.partial(user));

        a.appendTo(li);
        li.appendTo($("#lobby_duel_players"));

        /* Clicking shows/hides additional details and the Join Duel button */
        li.click(function(event) {

            var current = this;
            $("li.active", $("#lobby_duel_players")).each(function() {
                if(this != current) {
                    var li = $(this);
                    var button = $("button", li);

                    button.hide();
                    li.removeClass("active");               
                }
            });
            $("li.active", $("#lobby_available_players")).each(function() {
                if(this != current) {
                    var li = $(this);
                    var button = $("button", li);

                    button.hide();
                    li.removeClass("active");               
                }
            });
            $("li.active", $("#lobby_games_in_progress")).each(function() {
                if(this != current) {
                    var li = $(this);
                    var button = $("button", li);

                    button.hide();
                    li.removeClass("active");               
                }
            });

            var li = $(current);
            var button = $("button", li);

            if (button.is(":visible")) {
                button.hide();
                li.removeClass("active");
            }
            else{
                button.show();
                li.addClass("active");
            }
        });

    }

    for (var i = 0; i < available.length; i++) {
        var user = available[i]; 
        var li = $("<li></li>");
        var a = $("<a href='#'></a>").text(user);

        var button = $("<button type='button' class='btn pull-right btn-small' style='margin-top:-3px'>Challenge</button>");
        button.hide();
        button.appendTo(a);

        a.appendTo(li);
        li.appendTo($("#lobby_available_players"));

        /* Clicking shows/hides additional details and the Challenge button */
        li.click(function(event) {

            var current = this;
            $("li.active", $("#lobby_duel_players")).each(function() {
                if(this != current) {
                    var li = $(this);
                    var button = $("button", li);

                    button.hide();
                    li.removeClass("active");               
                }
            });

            $("li.active", $("#lobby_available_players")).each(function() {
                if(this != current) {
                    var li = $(this);
                    var button = $("button", li);

                    button.hide();
                    li.removeClass("active");               
                }
            });
            $("li.active", $("#lobby_games_in_progress")).each(function() {
                if(this != current) {
                    var li = $(this);
                    var button = $("button", li);

                    button.hide();
                    li.removeClass("active");               
                }
            });

            var li = $(current);
            var button = $("button", li);

            if (button.is(":visible")) {
                button.hide();
                li.removeClass("active");
            }
            else{
                button.show();
                li.addClass("active");
            }
        });
    }
}

function lobby_onGames(topicUri, games) {
    $("#lobby_games_in_progress").empty();

    $("<li class='nav-header'>Games in progress</li>").appendTo($("#lobby_games_in_progress"));

    games = games["games"];
  
    for (var i = 0; i < games.length; i++) {
        var game = games[i]; 

        var li = $("<li></li>");

        var players = game["players"];

        if (g_gameuri == null) {
            if (players.length == 2) {
                for (var j = 0; j < players.length; j++) {
                    var player = players[j];

                    if (player["login"] == g_login) {
                        game_takeover(game.id, player.role);
                    }
                }
            }
        }

        //alert (players);

        var players_text = "";
        if (players.length == 0) {
            continue;
        }
        else if (players.length == 1) {
            players_text = players[0]["login"];
        }
        else if (players.length == 2) {
            players_text = players[0]["login"] + " vs " + players[1]["login"];
        }

        var a = $("<a href='#'></a>").text(players_text);

/*        var button = $("<button type='button' class='btn pull-right btn-small' style='margin-top:-3px'>Watch</button>");
        button.hide();
        button.appendTo(a);

        button.click(function (user, e) {
            lobby_join_duel(user);
        }.partial(user));*/

        a.appendTo(li);
        li.appendTo($("#lobby_games_in_progress"));

        /* Clicking shows/hides additional details and the Join Duel button */
        li.click(function(event) {

            var current = this;
            $("li.active", $("#lobby_duel_players")).each(function() {
                if(this != current) {
                    var li = $(this);
                    var button = $("button", li);

                    button.hide();
                    li.removeClass("active");               
                }
            });
            $("li.active", $("#lobby_available_players")).each(function() {
                if(this != current) {
                    var li = $(this);
                    var button = $("button", li);

                    button.hide();
                    li.removeClass("active");               
                }
            });
            $("li.active", $("#lobby_games_in_progress")).each(function() {
                if(this != current) {
                    var li = $(this);
                    var button = $("button", li);

                    button.hide();
                    li.removeClass("active");               
                }
            });


            var li = $(current);
            var button = $("button", li);

            if (button.is(":visible")) {
                button.hide();
                li.removeClass("active");
            }
            else{
                button.show();
                li.addClass("active");
            }
        });
    }
}

