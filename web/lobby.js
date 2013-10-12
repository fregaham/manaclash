
function lobby_init(sess) {
    sess.subscribe("http://manaclash.org/chat", lobby_onChat);
    sess.subscribe("http://manaclash.org/chat_history", lobby_onChatHistory);

    $("#lobby_chat_input").keydown(function (e){
        if(e.keyCode == 13) {
            lobby_chat_send();
        }
    })

    sess.subscribe("http://manaclash.org/users", lobby_onUsers);
//    sess.subscribe("http://manaclash.org/games", lobby_onGames);
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

function lobby_onUsers(topicUri, users) {

    $("#lobby_available_players").empty();

    $("<li class='nav-header'>Available Players</li>").appendTo($("#lobby_available_players"));

    for (var i = 0; i < users.length; i++) {
        var li = $("<li></li>");
        var a = $("<a href='#'></a>").text(users[i]);

        var button = $("<button type='button' class='btn pull-right btn-small' style='margin-top:-3px'>Challenge</button>");
        button.hide();
        button.appendTo(a);

        a.appendTo(li);
        li.appendTo($("#lobby_available_players"));

        /* Clicking shows/hides additional details and the Challenge button */
        li.click(function(event) {

            var current = this;
            $("li.active", $("#lobby_available_players")).each(function() {
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


