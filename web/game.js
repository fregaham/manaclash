
var g_role = null;
var g_gameuri = null;
var g_timer = null;
var g_timeout = null;
var g_state = null;
var g_playermap = null;
var g_imgprefix = null;
var g_solitaire = false;

// map id -> game object
var g_objects = {};

// Is autopass cancelled?
var g_autopass_cancel = false;
var g_pass_on_next_priority = false;
var g_pass_on_next_priority_step = null;

// map object id -> zone (e.g. "player_hand", "opponent_graveyard", etc.)
var g_zone_map = {};

// currently detailed card id
var g_detail_id = null;

function game_init(sess) {
    $("#autopass").click(function(event) {
        stopTimer();
        g_autopass_cancel = true;
        g_pass_on_next_priority = false;
        g_pass_on_next_priority_step = null;
        $("#autopass").hide();
    });

    $("#autopass").hide();

    $("#query_button").click(function(event) {
        onQueryButton();
    });

    $("#game_messages_expand").click(function(event) {
        expandLog();
    });

    $("#game_messages_send").click(function(event) {
        sendMessage();
    });

    // clear the log
    $("#messages").empty();
}

function subscribeGame(gameUri) {
    sess.subscribe(gameUri + "/state", onGame);
    sess.subscribe(gameUri + "/zoneTransfer", onLogZoneTransfer);
    sess.subscribe(gameUri + "/action", onLogAction);
    sess.subscribe(gameUri + "/number", onLogNumber);
    sess.subscribe(gameUri + "/message", onLogMessage);
    sess.subscribe(gameUri + "/endgame", onEndGame);
    sess.subscribe(gameUri + "/win", onGameWin);

    sess.subscribe(gameUri + "/player/online", onPlayerOnline);
    sess.subscribe(gameUri + "/player/offline", onPlayerOffline);
}

function unsubscribeGame(gameUri) {
    sess.unsubscribe(gameUri + "/state");
    sess.unsubscribe(gameUri + "/zoneTransfer");
    sess.unsubscribe(gameUri + "/action");
    sess.unsubscribe(gameUri + "/number");
    sess.unsubscribe(gameUri + "/message");
    sess.unsubscribe(gameUri + "/endgame");
    sess.unsubscribe(gameUri + "/win");

    sess.unsubscribe(gameUri + "/player/online");
    sess.unsubscribe(gameUri + "/player/offline");
}

function game_takeover(gameId, role) {
    sess.call("http://manaclash.org/takeover", gameId, role).then(
        function(ret) {
            var uri = ret[0];
            var role = ret[1];
            subscribeGame(uri);
            g_role = role;
            g_gameuri = uri;
            sess.call("http://manaclash.org/refresh");
        });
}

function onPlayerOffline(uri, message) {
    var login = message[0];
    var role = message[1];

    var msg = appendLog("" + login + " goes offline");

    if (role == g_role) {
        msg.addClass("player_message");
    }
    else {
        msg.addClass("opponent_message");
    }
}

function onPlayerOnline(uri, message) {
    var login = message[0];
    var role = message[1];

    var msg = appendLog("" + login + " back online");

    if (role == g_role) {
        msg.addClass("player_message");
    }
    else {
        msg.addClass("opponent_message");
    }
}

function onGame(gameUri, state) {
    /* Check the game URI */
    if (gameUri.slice(0, g_gameuri.length) == g_gameuri) {
        var event = gameUri.slice(g_gameuri.length);
        if (event == "/state") {
            onState(state);
        }
    }
}

function endGame() {
    if (window.confirm("Are you sure to end the current game?")) {
        sess.publish(g_gameuri + "/endgame", g_login, false);
    }
}

function onEndGame(uri, login) {
    
    var msg = appendLog("Game ended by " + login);

    if (login == g_login) {
        msg.addClass("player_message");
    }
    else {
        msg.addClass("opponent_message");
    }

    unsubscribeGame(g_gameuri);

    g_gameuri = null;
    g_role = null;
    g_solitaire = false;
}

function onGameWin(uri, role) {
    if (role == null) {
        var msg = appendLog("Game ended in a draw!");
        msg.addClass("player_message");
    }
    else {
        var msg = appendLog("" + getPlayerName(role) + " wins the game!");
        if (role == g_role) {
            msg.addClass("player_message");
        }
        else {
            msg.addClass("opponent_message");
        }
    }
}

/*
    Renders the card elements
    objSpan, the root span of the card
    obj the object representing the card, as got from the server
*/
function displayCardContents(objSpan, obj, tags) {
    // color
    var color = "colorless";
    var colors = ["red", "blue", "white", "black", "green", "multicolor"];
    for (var i = 0; i < colors.length; i++) {
        if (obj.tags.indexOf(colors[i]) >= 0) {
            color = colors[i];
        }
    }

    if (color == "colorless" && obj.types.indexOf("land") >= 0) {
        color = "land";
    }

    var land_subtypes = ["forest", "swamp", "island", "plains", "mountain"];
    for (var i = 0; i < land_subtypes.length; i++) {
        if (color == "land" && obj.subtypes.indexOf(land_subtypes[i]) >= 0) {
            color = land_subtypes[i];
        }
    }

    objSpan.addClass("card_" + color);

    var contentDiv = $("<div class='card_content'></div>");
    contentDiv.appendTo(objSpan);

    var headerSpan = $("<span class='header'/>");
    headerSpan.appendTo(contentDiv);

    var titleSpan = $("<span class='title'></span>");
    titleSpan.text(obj.title);
    titleSpan.appendTo(headerSpan);
   
    var costSpan = $("<span class='manacost'></span>");
    costSpan.text(obj.manacost);
    costSpan.appendTo(headerSpan);

    var bodySpan = $("<span class='body'/>");
    bodySpan.appendTo(contentDiv);

    var typeSpan = $("<span class='types'></span>");
    typeSpan.text(obj.supertypes.join(" ") + " " + obj.types.join(" "));

    if (obj.subtypes.length > 0) {
        typeSpan.append(" &ndash; ");
    }

    typeSpan.append(obj.subtypes.join(" "));
    typeSpan.appendTo(bodySpan);

    var textSpan = $("<span class='text'></span>");
    if (tags) {
        var tagsSpan = $("<span></span>");
        // tagSpan.text(obj.tags.join(" "));
        for (var i = 0; i < obj.tags.length; i++) {
            var tagSpan = $("<span></span>");
            tagSpan.text(obj.tags[i]);
            tagsSpan.append(tagSpan);
            tagsSpan.append("<br/>");
        }
        var tSpan = $("<span></span>");
        tSpan.text(obj.text);

        if (obj.tags.length > 0) {
            textSpan.append(tagsSpan);
            textSpan.append($("<br/>"));
        }
        textSpan.append(tSpan);
    }
    else {
        textSpan.text(obj.text);
    }
    textSpan.appendTo(bodySpan);

    if (obj.power != null) {
        var powerSpan = $("<span class='power'></span>");
        powerSpan.text(obj.power + "/" + obj.toughness);
        powerSpan.appendTo(textSpan);
    }
}

/*
    Creates and returns a card <span/> from the server card object
    Also creates a "card_detail" span for this card and appends it hidden into the card_detail container
*/
function displayCard(obj) {

    // Store all objects in a map
    g_objects[obj.id] = obj;

    var objSpan = $("<span class='" + (obj.tapped ? "card_small card_tapped" : "card_small") + "' id='obj_" + obj.id + "'></span>");
    var detailSpan = $("<span class='card_detail' id='detail_" + obj.id + "'></span>");

    /* We should see it if our role is in the show_to list or if the card is shown to anybody and we play solitaire */
    if (obj.show_to.indexOf(g_role) >= 0 || (obj.show_to.length > 0 && g_solitaire)) {

        var fulltext =  "#" + obj.id + " " + obj.title + " " + obj.manacost + " " + obj.supertypes.join(" ") + " " + obj.types.join(" ");
        if (obj.subtypes.length > 0) {
            fulltext += " - ";
        }
        fulltext += obj.subtypes.join(" ") + " ";

        fulltext += obj.text;

        if (obj.power != null) {
            fulltext += " " + obj.power + "/" + obj.toughness;
        }

        objSpan.attr("title", fulltext);

        // Try to display as an image, only if we have configured image URLs and the card is not an "effect" nor "damage assignment"
        if (g_imgprefix != null && g_imgprefix != "" && obj.tags.indexOf("effect") < 0 && obj.tags.indexOf("damage assignment") < 0) {
            var img = $("<img/>");
            var imgstring = obj.title + ".jpg";
            img.attr("src", g_imgprefix + imgstring);
            img.attr("alt", "");

            img.appendTo(objSpan);
        }
        else {
            displayCardContents(objSpan, obj, false);
        }

        displayCardContents(detailSpan, obj, true);
    }
    else {
        // backside
        var img = $("<img/>");
        img.attr("src", "mc_back.png");
        img.appendTo(objSpan);

        img = $("<img/>");
        img.attr("src", "mc_back.png");
        img.css("width", "190px");
        img.appendTo(detailSpan);
    }

    detailSpan.hide();
    detailSpan.appendTo($("#card_details"));

    /* Display card details on the currently hovered card, also, highlight any card targets, blockers and attackers */
    objSpan.hover(
        function(id) {
            // hide the old detail and unhighlight targets
            if (g_detail_id != null) {
                $("#detail_" + g_detail_id).hide();

                var obj = g_objects[g_detail_id];
                for (var i = 0; i < obj.targets.length; ++i) {
                    $("#obj_" + obj.targets[i]).removeClass("targeted");
                }
                for (var i = 0; i < obj.blockers.length; ++i) {
                    $("#obj_" + obj.blockers[i]).removeClass("targeted");
                }
                for (var i = 0; i < obj.attackers.length; ++i) {
                    $("#obj_" + obj.attackers[i]).removeClass("targeted");
                }
            }
            $("#detail_" + id).show();
            $("#card_details").stop(true, true);
            $("#card_details").fadeIn("fast");
            g_detail_id = id;

            var obj = g_objects[id];
            for (var i = 0; i < obj.targets.length; ++i) {
                $("#obj_" + obj.targets[i]).addClass("targeted");
            }
            for (var i = 0; i < obj.blockers.length; ++i) {
                $("#obj_" + obj.blockers[i]).addClass("targeted");
            }
            for (var i = 0; i < obj.attackers.length; ++i) {
                $("#obj_" + obj.attackers[i]).addClass("targeted");
            }

        }.partial(obj.id),
        function(id) {
            $("#card_details").fadeOut("fast");

            var obj = g_objects[id];
            for (var i = 0; i < obj.targets.length; ++i) {
                $("#obj_" + obj.targets[i]).removeClass("targeted");
            }
            for (var i = 0; i < obj.blockers.length; ++i) {
                $("#obj_" + obj.blockers[i]).removeClass("targeted");
            }
            for (var i = 0; i < obj.attackers.length; ++i) {
                $("#obj_" + obj.attackers[i]).removeClass("targeted");
            }

        }.partial(obj.id)
    );

    return objSpan;
}

function displayZone(zone_name, state_zone, div) {
    for (var i = 0; i < state_zone.length; ++i) {
        var obj = state_zone[i];

        var objSpan = displayCard(obj);
        objSpan.appendTo(div);

        g_zone_map[obj.id] = zone_name;
    }
}

function _displayBattlefieldStackRecursive(stack_span, root_card, left_offset, top_offset, width, height, zindex, enchantments, zone_name) {

    var card_span = displayCard(root_card);
    card_span.appendTo(stack_span);
    card_span.css("left", left_offset);
    card_span.css("top", top_offset);
    card_span.css("position", "absolute");
    card_span.css("z-index", zindex);
    if (root_card.tapped) {
        width = Math.max(width, left_offset + 142);
        height = Math.max(height, top_offset + 100);
    }
    else {
        width = Math.max(width, left_offset + 100);
        height = Math.max(height, top_offset + 142);
    }

    /* We set the zone name here, so the auras of different controllers get into the right zone in the zone_map */
    g_zone_map[root_card.id] = zone_name;

    top_offset += 17;
    zindex ++;

    if (root_card.id in enchantments) {
        left_offset += 5;
        for (var i = 0; i < enchantments[root_card.id].length; ++i) {
            var enchantment_card = enchantments[root_card.id][i];
            var dims = _displayBattlefieldStackRecursive(stack_span, enchantment_card, left_offset, top_offset, width, height, zindex, enchantments, zone_name);
            top_offset = dims[0];
            width = dims[1];
            height = dims[2];
            zindex = dims[3];
        }
    }

    return [top_offset, width, height, zindex];
}

function _displayBattlefieldStack(stack, enchantments, div, zone_name) {
    for (var i = 0; i < stack.length; ++i) {
        var stack_span = $("<span class='card_stack'></span>");
        var width = 0;
        var height = 0;

        var top_offset = 0;
        var zindex = 0;

        for (var j = 0; j < stack[i].length; ++j) {
            var obj = stack[i][j];
            var dims = _displayBattlefieldStackRecursive(stack_span, obj, 0, top_offset, width, height, zindex, enchantments);
            top_offset = dims[0];
            width = dims[1];
            height = dims[2];
            zindex = dims[3];
        }
        stack_span.css("width", width + 8);
        stack_span.css("height", height + 8);

        stack_span.appendTo(div);
    }
}

function displayBattlefield(objects, in_play_divs, in_play_battle_divs, rolemap) {

    /* Map object ids to list of enchantments */
    var enchantments = {};

    for (var i = 0; i < objects.length; ++i) {
        var obj = objects[i];
        if (obj.enchanted_id !== null) {
            if (!(obj.enchanted_id in enchantments)) {
                enchantments[obj.enchanted_id] = [];
            }
            enchantments[obj.enchanted_id].push(obj);
        }
    }

    /* role to list of Stacks (list) of non-aura objects of the same name  */
    var role2stacks = {};
    var role2stacks_battle = {};

    for (var i = 0; i < objects.length; ++i) {
        var obj = objects[i];

        if (obj.controller !== null && obj.enchanted_id === null) {
            var role = rolemap[obj.controller];
            var battle = (obj.tags.indexOf("attacking") >= 0 || obj.tags.indexOf("blocking") >= 0);

            var role2stacksmap = role2stacks;
            if (battle) {
                role2stacksmap = role2stacks_battle;
            }

            if (!(role in role2stacksmap)) {
               role2stacksmap[role] = [];
            }

            /* Look if there is already a stack of cards with the same name */
            var stacks = role2stacksmap[role];
            var found = false;
            for (var j = 0; j < stacks.length; ++j) {
                var stack = stacks[j];
                if (stack[0].title == obj.title) {

                    /* Add the object to this stack */
                    stack.push(obj);

                    found = true;
                    break;
                }
            }

            /* No stack with this title yet, create a new one */
            if (!found) {
                var stack = [];
                stack.push(obj);
                stacks.push(stack);
            }
        }
    }

    for (var role in role2stacks) {
        _displayBattlefieldStack(role2stacks[role], enchantments, in_play_divs[role], role + "_in_play");
    }

    for (var role in role2stacks_battle) {
        _displayBattlefieldStack(role2stacks_battle[role], enchantments, in_play_battle_divs[role], role + "_in_play_battle");
    }
}

function selectAction(i) {
    stopTimer();
    sess.publish(g_gameuri, i);

    g_autopass_cancel = false;

    $("#pass").attr("disabled", "disabled");

    /* clear the "action_zone_button" classes from any zone_buttons */
    $(".action_zone_button").removeClass("action_zone_button");
    $(".action_zone").removeClass("action_zone");
    $(".player_action").removeClass("player_action");

    /* clear the player header click handlers */
    $("#player_header").off("click");
    $("#opponent_header").off("click");
}

function selectActions(actions) {
    var actions_div = $("#actions");
    actions_div.empty();

    var pass = $("#pass");
    pass.attr("disabled", "disabled");

    /* clear the "action_zone_button" classes from any zone_buttons */
    $(".action_zone_button").removeClass("action_zone_button");
    $(".action_zone").removeClass("action_zone");
    $(".player_action").removeClass("player_action");
    $(".action").off("click");
    $(".action").removeClass("action");

    /* clear the player header click handlers */
    $("#player_header").off("click");
    $("#opponent_header").off("click");

    for (var i = 0; i < actions.length; ++i) {

        var action = actions[i];

        var action_span = $("<button></button>").appendTo(actions_div);
        action_span.text(action["text"]);
        action_span.addClass('action_button');
        action_span.click({'i':action._index}, function(event) {
            selectAction(event.data.i);
        });
    }
}

function getPlayerName(player) {
    if (g_solitaire) {
        return g_playermap[player].role;
    }
    else {
        return g_playermap[player].name;
    }
}

function onState(state) {
/*    if (g_waiting_for_game) {
        g_waiting_for_game = false;
        view("view_game");
    }*/
    
    if (g_solitaire) {
        $("#opponent_hand_zone_button").hide();
    }
    else {
        $("#opponent_hand_zone_button").show();
    }

    g_state = state;
    g_zone_map = {};

    var table = $("#table");
    table.empty();

    $('#text').empty();

    $("#phase").empty();
    $("#phase").text(state["phase"]);

    $("#step").empty();
    $("#step").text(state["step"]);

    $("#card_details").empty();

    var in_play = [];
    var in_play_battle = [];
    var player_hand = [];
    var players = [];
    // playerN -> player|opponent
    var rolemap = {};
    
    // playerN -> player object
    g_playermap = {};

    if (g_role == "player1") {
        players.push("player");
        players.push("opponent");
    }
    else {
        players.push("opponent");
        players.push("player");
    }

    player_divs = [];
   
    for (var i = 0; i < players.length; ++i) {
        player_divs[players[i]] = $("<div></div>");
        rolemap["player" + (i+1)] = players[i];
    }

    var stack = $("<div id='zone_stack'></div>");
    displayZone("stack", state["stack"], stack);

    $("#revealed_zone").empty();
    displayZone("revealed", state["revealed"], $("#revealed_zone"));

    player_divs["opponent"].appendTo(table);
    stack.appendTo(table);
    player_divs["player"].appendTo(table);

    /* opponent hand is only shown in solitaire mode */
    player_hand["opponent"] = $("<div></div>").appendTo(player_divs["opponent"]);
    in_play["opponent"] = $("<div></div>").appendTo(player_divs["opponent"]);
    in_play_battle["opponent"] = $("<div></div>").appendTo(player_divs["opponent"]);

    in_play_battle["player"] = $("<div></div>").appendTo(player_divs["player"]);
    in_play["player"] = $("<div></div>").appendTo(player_divs["player"]);
    player_hand["player"] = $("<div></div>").appendTo(player_divs["player"]);

    displayBattlefield(state["in_play"], in_play, in_play_battle, rolemap);

    for (var i = 0; i < state["players"].length; ++i) {
        var player = state["players"][i];

        g_playermap["player" + (i+1)] = player;

        $("#" + rolemap[player.role] + "_name").empty();

        /* Player names are useless in solitaire */
        $("#" + rolemap[player.role] + "_name").text(getPlayerName("player" + (i+1)));

        if (player.library.length == 0) {
            $("#" + rolemap[player.role] + "_library").empty();
            $("#" + rolemap[player.role] + "_library").addClass("empty_stack");
        }
        else {
            if ($("#" + rolemap[player.role] + "_library").children().length == 0) {
                $("#" + rolemap[player.role] + "_library").removeClass("empty_stack");
                var img = $("<img src='./mc_back.png'/>");
                img.css("width", 40);
                img.css("height", 58);
                img.appendTo($("#" + rolemap[player.role] + "_library"));
            }
        }

        $("#" + rolemap[player.role] + "_library").attr("title", "Library: " + player.library.length);

        if (player.graveyard.length == 0) {
            $("#" + rolemap[player.role] + "_graveyard").empty();
            $("#" + rolemap[player.role] + "_graveyard").addClass("empty_stack");
        }
        else {
            $("#" + rolemap[player.role] + "_graveyard").removeClass("empty_stack");

            var topcard = $("<span class='card_small card_graveyard'></span>");
            displayCardContents(topcard, player.graveyard[player.graveyard.length - 1], false);
            topcard.appendTo($("#" + rolemap[player.role] + "_graveyard"));
        }

        $("#" + rolemap[player.role] + "_graveyard").attr("title", "Graveyard: " + player.graveyard.length);

        $("#" + rolemap[player.role] + "_life").empty(); 
        $("#" + rolemap[player.role] + "_life").text(player.life);

        $("#" + rolemap[player.role] + "_manapool").empty(); 
        $("#" + rolemap[player.role] + "_manapool").text(player.manapool);

        $("#" + rolemap[player.role] + "_graveyard_zone").empty(); 
        $("#" + rolemap[player.role] + "_library_zone").empty(); 

        displayZone(rolemap[player.role] + "_graveyard", player["graveyard"], $("#" + rolemap[player.role] + "_graveyard_zone"));
        displayZone(rolemap[player.role] + "_library", player["library"], $("#" + rolemap[player.role] + "_library_zone"));

        /* We show both hands in the play zone if we play solitaire */
        if (rolemap[player.role] == "player" || g_solitaire) {
            displayZone(rolemap[player.role] + "_hand", player["hand"], player_hand[rolemap[player.role]]);

            $("#" + rolemap[player.role] + "_hand").empty(); 
            $("#" + rolemap[player.role] + "_hand").text(player.hand.length);
        }
        else {
            $("#" + rolemap[player.role] + "_hand_zone").empty();
            displayZone(rolemap[player.role] + "_hand", player["hand"], $("#" + rolemap[player.role] + "_hand_zone"));

            if ($("#" + rolemap[player.role] + "_hand").children().length != player.hand.length) {

                $("#" + rolemap[player.role] + "_hand").empty();
                $("#" + rolemap[player.role] + "_hand").attr("title", "Hand: " + player.hand.length);

                if (40 * player.hand.length < 180) {
                    $("#" + rolemap[player.role] + "_hand").css("left", 10 + ((180 - 40 * player.hand.length) / 2));
                    $("#" + rolemap[player.role] + "_hand").css("width", 40 * player.hand.length);
                }
                else {
                    $("#" + rolemap[player.role] + "_hand").css("left", 10);
                    $("#" + rolemap[player.role] + "_hand").css("width", 180);
                }

                for (var j = 0; j < player.hand.length; j++) {
                    var img = $("<img src='./mc_back.png'/>");
                    
                    img.css("position", "absolute");
                    img.css("width", 40);
                    img.css("height", 58);

                    if (40 * player.hand.length < 180) {
                        img.css("left", 40 * j);
                    }
                    else {
                        img.css("left", ((180 - 40) / (player.hand.length - 1)) * j);
                    }

                    img.appendTo($("#" + rolemap[player.role] + "_hand"));
                }
            }
        }
    }

    $("#turn").empty();

    $("#turn").text(getPlayerName(state["turn"]));

    var actions_div = $("#actions");
    actions_div.empty();

    var query = $("#query");
    query.hide();

    var pass = $("#pass");
    pass.attr("disabled", "disabled");

    if (state["text"] != "You have priority" && state["player"] != null) {
        appendLog("" + getPlayerName(state["player"]) + ", " + state["text"]);
    }

    console.log("onState " + getPlayerName(state["player"])  + " " + state["phase"] + ", " + state["step"] + " " + state["text"]);

    /* It is our "turn" now, or we play solitaire and every turn is 'our' turn */
    if (g_role == state["player"] || g_solitaire) {

        if (state["revealed"].length > 0) {
            showZone($("#revealed_zone"));
        }
        else {
            if ($("#revealed_zone").is(":visible")) {
                showZone(null);
            }
        }

        $("#text").text(getPlayerName(state["player"]) + ", " + state["text"]);

        if (state["actions"] != null) {

            var autopass = true;
            var haspass = false;

            if (state["text"] != "You have priority") {
                autopass = false;
            }


            /* maps object ids/player roles to list of actions, we set _index property of the action object */
            var player2actions = {}
            var obj2actions = {};
            var otheractions = [];

            for (var i = 0; i < state["actions"].length; ++i) {
                var action = state["actions"][i];
                action._index = i;
                if (action["player_object"] != null) {
                    var role = rolemap[action["player_object"]];
                    if (role in player2actions) {
                        player2actions[role].push(action);
                    }
                    else {
                        player2actions[role] = [];
                        player2actions[role].push(action);
                    }
                }
                else if (action["object"] == null) {
                    otheractions.push(action);
                }
                else {
                    if (action["manaability"] == null || action["manaability"] == false) {
                        autopass = false;
                    }

                    var objid = action["object"];
                    if (objid in obj2actions) {
                        obj2actions[objid].push(action);
                    }
                    else {
                        obj2actions[objid] = [];
                        obj2actions[objid].push(action);
                    }
                }
            }

            for (var role in player2actions) {
                var actions = player2actions[role];
                $("#" + role + "_header").addClass("player_action");
                if (actions.length == 1) {
                    $("#" + role + "_header").on("click", {'i':actions[0]._index}, function(event) {
                            selectAction(event.data.i);
                        }
                    );
                }
                else {
                    $("#" + role + "_header").on("click", {'actions':actions}, function(event) {
                            selectActions(event.data.actions);
                        }
                    );
                }
            }

            for (var objid in obj2actions) {
                var actions = obj2actions[objid];

                var action_obj = $('#obj_' + objid);
                action_obj.addClass('action');

                /* Highlight the zone button if the object is in a zone that is not visible by default  */
                if (g_zone_map[objid] !== undefined) {
                    var zone = $("#" + g_zone_map[objid]);
                    if (zone !== undefined) {
                        zone.addClass("action_zone");
                    }
                }

                if (actions.length == 1) {
                    var action = actions[0];
                    action_obj.click({'i':action._index}, function(event) {
                        selectAction(event.data.i);
                    });
                }
                else {
                    action_obj.click({'actions':actions}, function(event) {
                        selectActions(event.data.actions);
                    });
                }
            }

            for (var i = 0; i < otheractions.length; ++i) {
                var action = otheractions[i];
                /* action with no object, display it as a button in the actions list */
                if (action["text"] != "Pass") {
                    autopass = false;
                    var action_span = $("<button></button>").appendTo(actions_div);
                    action_span.text(action["text"]);
                    action_span.addClass('action_button');
                    action_span.click({'i':action._index}, function(event) {
                        selectAction(event.data.i);
                    });
                }
                else {
                    haspass = true;
                    pass.removeAttr("disabled");
                }
            }

            // auto select no more attackers if none available
            if (state["actions"].length == 1 && state["actions"][0]["text"] == "No more attackers" && state["step"] == "declare attackers" && state["text"] == "Select attackers") {
                autopass = true;
            }

            // auto select no more blockers if none available
            if (state["actions"].length == 1 && state["actions"][0]["text"] == "No more blockers" && state["step"] == "declare blockers" && state["text"] == "Select blockers") {
                autopass = true;
            }

            if (autopass && !g_autopass_cancel) {
                console.log("onState autopass");

                stopTimer();
                // $("#autopass").hide();
                g_pass_on_next_priority = false;
                g_pass_on_next_priority_step = null;

                sess.publish(g_gameuri, 0);
            }
            else if (state["text"] == "You have priority" && g_pass_on_next_priority && (state["phase"] + " " + state["step"]) == g_pass_on_next_priority_step ) {
                console.log("onState passing due to g_pass_on_next_priority");

                stopTimer();
                // $("#autopass").hide();
                g_pass_on_next_priority = false;
                g_pass_on_next_priority_step = null;

                sess.publish(g_gameuri, 0);
            }
            else {
                g_pass_on_next_priority = false;
                g_pass_on_next_priority_step = null;

                if (!g_autopass_cancel && state["text"] == "You have priority" && haspass && !((state["turn"] == g_role || g_solitaire) && (state["phase"] == "precombat main" || state["phase"] == "postcombat main"))) {

                    // If there is an existing timer started by the other player's priority wait...
                    if (g_timer == null) {

                        console.log("onState priority, no timer yet");

                        g_timeout = 3;
                        g_timer = setTimeout('onTimer()', 1000);

                        g_pass_on_next_priority_step = state["phase"] + " " + state["step"];

                        setAutopassPriorityMessasge();
                    }
                    else {
                        console.log("onState priority, existing timer");

                        setAutopassPriorityMessasge();
                    }
                }
                else {
                    console.log("onState priority, main phase");

                    stopTimer();
                    $("#autopass").hide();
                }
            }
        }
        else if (state["query"] != null) {
            stopTimer();

            $("#query_text").empty();
            $("#query_text").text(state["query"]);
            $("#query_input").val("");
            query.show();
        }
    } 
    else {
        if (state["player"] != null) {
            $("#text").append("Waiting for " + getPlayerName(state["player"]));

            if (state["text"] == "You have priority") {

                console.log("onState other player priority");

                stopTimer();
                g_timeout = 3;
                g_timer = setTimeout('onTimer()', 1000);
                g_pass_on_next_priority = false;
                g_pass_on_next_priority_step = state["phase"] + " " + state["step"];

                setAutopassPriorityMessasge();
            }
            else {
                console.log("onState other player wait");

                stopTimer();
                // It is not our turn
                $("#autopass").empty();
                $("<div class='autopass_wait'></div>").text("Waiting for " + getPlayerName(state["player"])).appendTo($("#autopass"));
                $("#autopass").show();
            }
        }
        else {
            stopTimer();
            // game ended, do nothing
            $("#autopass").hide();
        }
    }
}

function onPass() {
    selectAction(0);
}

function onQueryButton() {
    selectAction($("#query_input").val());
}

function setAutopassPriorityMessasge() {
    $("#autopass").empty();

    if (g_state["step"]) {
        $("<div class='autopass_priority'></div>").text(g_state["phase"]).append("<br/>").append(g_state["step"]).append("<br/>" + g_timeout).appendTo($("#autopass"));
    }
    else {
        $("<div class='autopass_priority'></div>").text(g_state["phase"]).append("<br/>" + g_timeout).appendTo($("#autopass"));
    }
    $("#autopass").show();
}

function stopTimer() {
    if (g_timer != null) {
        clearTimeout(g_timer);
    }
    g_timer = null;
    g_timeout = null;
}

function onTimer() {

    console.log("onTimer");

    if (g_timeout == null) {
        return;
    }

    g_timeout--;

    if (g_timeout <= 0) {
        stopTimer();

        // two options, one, we are waiting on our own pass, or the wait started during the opponents' priority wait and 
        if (g_role == g_state["player"] && g_state["text"] == "You have priority") {

            console.log("onTimer autopassing");

            $("#pass").attr("disabled", "disabled");
            sess.publish(g_gameuri, 0);
            // $("#autopass").empty();
        }
        else {
            console.log("onTimer setting g_pass_on_next_priority");

            // we want to pass but cannot yet.
            $("#autopass").empty();
            $("<div class='autopass_wait'></div>").text("Waiting for " + getPlayerName(g_state["player"])).appendTo($("#autopass"));
            $("#autopass").show();
            g_pass_on_next_priority = true;
        }
    }
    else {
        console.log("onTimer --");

        setAutopassPriorityMessasge();
        setTimeout('onTimer()', 1000);
    }
}

function showZone(zone) {
    $("#player_graveyard_zone").hide();
    $("#player_library_zone").hide();
    $("#opponent_graveyard_zone").hide();
    $("#opponent_library_zone").hide();
    $("#opponent_hand_zone").hide();
    $("#revealed_zone").hide();

    if (zone != null) {
        zone.show();
        $("#zones").show();
    }
    else {
        $("#zones").hide();
    }
}

// Logs

function appendLog(log) {
    var msg = $("<div class='message'></div>");
    msg.text(log);
    msg.appendTo($("#messages"));

    $("#messages").scrollTop($("#messages")[0].scrollHeight);

    return msg;
}

function onLogZoneTransfer(uri, zoneTransfer) {
    if (zoneTransfer[3] != null) {
        appendLog("card moved from " + zoneTransfer[0] + " to " + zoneTransfer[1]);
    }
    else {
        appendLog("" + zoneTransfer[2].title + " moved from " + zoneTransfer[0] + " to " + zoneTransfer[1]);
    }
}

function onLogAction(uri, actionMessage) {
    if (actionMessage[1]["text"] != "Pass") {
        appendLog("" + getPlayerName(actionMessage[0]) + " " + actionMessage[1]["text"]);
    }
}

function onLogNumber(uri, actionMessage) {
    appendLog("" + getPlayerName(actionMessage[0]) + " " + actionMessage[1]);
}

/* Messages sent by players */
function onLogMessage(uri, message) {
    var msg = appendLog("" + getPlayerName(message[0]) + " " + message[1]);
    if (message[0] == g_role) {
        msg.addClass("player_message");
    }
    else {
        msg.addClass("opponent_message");
    }
}

function sendMessage() {
    sess.publish(g_gameuri + "/message", [g_role, $("#game_messages_input").val()], false);
}

function expandLog() {
    $("#game_messages").toggleClass("game_messages_expanded");
    $("#messages").scrollTop($("#messages")[0].scrollHeight);
}
