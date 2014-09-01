'use strict';

/* Controllers */

var manaclashControllers = angular.module('manaclashControllers', ['manaclashServices']);

manaclashControllers.controller('MainController', ['$rootScope', '$scope', '$location', 
  function ($rootScope, $scope, $location) {
    $scope.bgClass = function() {
       return $rootScope.bgClass;
    }
  }]);


manaclashControllers.controller('LoginCtrl', ['$scope', '$http', 'EventBus', 'SessionManager', '$location', '$timeout',
  function ($scope, $http, EventBus, SessionManager, $location, $timeout) {
    $scope.username = 'foo';
    $scope.password = 'foo';

    $scope.error = '';

    $scope.login = function() {
       SessionManager.login($scope.username, $scope.password, function () {
          $timeout(function() { $location.path('/lobby'); });
       },

       function () {
          $scope.$apply (function() {
             $scope.error = "Wrong username / password";
          });
       });
    };
  }]);

manaclashControllers.controller('RegisterCtrl', ['$scope', '$http', 'EventBus', 'SessionManager', '$location', '$timeout',
  function ($scope, $http, EventBus, SessionManager, $location, $timeout) {
    $scope.username = '';
    $scope.email = '';
    $scope.password = '';
    $scope.password2 = '';

    $scope.register = function() {
        if ($scope.password != $scope.password2) {
          $scope.error = "Passwords must match!";
        }
        else {
            //alert("Registering");
            EventBus.send("register", {'username': $scope.username, 'password': $scope.password, 'email': $scope.email}, function (reply) {
                if (reply["status"] != "ok") {
                    $scope.$apply (function() {
                        $scope.error = reply["message"];
                    });
                }
                else {
                    SessionManager.login($scope.username, $scope.password, 
                        function () {
                            $timeout(function() { $location.path('/lobby'); });
                        }, 
                        function () {
                            $scope.$apply (function() {
                                $scope.error = "Error logging in with the new username. Please try again later.";
                            });
                        }
                    );
                }
            });
        }
    }
  }]);

manaclashControllers.controller('LobbyCtrl', ['$scope', '$http', '$timeout', '$location', 'EventBus', 'SessionManager','Game',
  function ($scope, $http, $timeout, $location, EventBus, SessionManager, Game) {
    $scope.message = '';
    $scope.messages = [];

    $scope.users = [];
    $scope.openForDuel = false;

    EventBus.myHandler('onchat', function(message) {
        $scope.$apply (function() {
            $scope.messages.push(message);
        });

/*        alert('chat ' + message["username"] + ": " + message["message"] );*/
    });

    EventBus.myHandler('onusers', function(message) {
        $scope.$apply (function() {
            $scope.users = message;
        });
    });

    EventBus.send("chat_enter", {'sessionID': SessionManager.sessionID}, function(reply) {
        $scope.$apply (function() {
            $scope.messages = reply["messages"];
        });
    });

    $scope.chat = function() {
        if ($scope.message) {
            EventBus.send("chat", {'sessionID': SessionManager.sessionID, 'message': $scope.message})
            $scope.message = '';
        }
    }

    $scope.onOpenForDuel = function(t) {
        EventBus.send("openForDuel", {'sessionID': SessionManager.sessionID, 'open':t})
    }

    $scope.joinDuel = function(username) {
        EventBus.send("joinDuel", {'sessionID': SessionManager.sessionID, 'username': username})
    }

    $scope.onJoinHandler = function(id) {
        $timeout(function() { $location.path('/game'); });
    }

    Game.joinHandler = $scope.onJoinHandler;
  }]);


manaclashControllers.controller('GameCtrl', ['$scope', '$http', 'EventBus', 'SessionManager', 'Game',
  function ($scope, $http, EventBus, SessionManager, Game) {

    $scope.actions = [];
    $scope.opponent_stacks = [];
    $scope.player_stacks = [];
    $scope.hand = [];

    $scope.action = function(action) {
        EventBus.send("game.action." + Game.gameid, {'sessionID': SessionManager.sessionID, 'type': 'action', 'action': action.index} );
    }

    $scope.createBattlefieldStackRecursive = function(rendered_stack, root_card, left_offset, top_offset, width, height, zindex, enchantments) {

        rendered_card = {}

        rendered_stack["cards"].push (rendered_card)

        rendered_card["obj"] = root_card

        rendered_card["left"] = left_offset;
        rendered_card["top"] = top_offset;
/*        rendered_stack["position"] = , "absolute");*/
        rendered_card["z-index"] = zindex;

        if (root_card.tapped) {
            width = Math.max(width, left_offset + 142);
            height = Math.max(height, top_offset + 100);
        }
        else {
            width = Math.max(width, left_offset + 100);
            height = Math.max(height, top_offset + 142);
        }

        /* We set the zone name here, so the auras of different controllers get into the right zone in the zone_map */
        /* g_zone_map[root_card.id] = zone_name;*/

        top_offset += 17;
        zindex ++;

        if (root_card.id in enchantments) {
            left_offset += 5;
            for (var i = 0; i < enchantments[root_card.id].length; ++i) {
                var enchantment_card = enchantments[root_card.id][i];
                var dims = this.createBattlefieldStackRecursive(rendered_stack, enchantment_card, left_offset, top_offset, width, height, zindex, enchantments);
                top_offset = dims[0];
                width = dims[1];
                height = dims[2];
                zindex = dims[3];
            }
        }

        return [top_offset, width, height, zindex];
    }

    $scope.createBattlefieldStack = function(stack, enchantments, rendered_stacks) {
        for (var i = 0; i < stack.length; ++i) {

            var rendered_stack = {};
            rendered_stack["cards"] = [];

            var width = 0;
            var height = 0;

            var top_offset = 0;
            var zindex = 0;

            for (var j = 0; j < stack[i].length; ++j) {
                var obj = stack[i][j];
                var dims = _displayBattlefieldStackRecursive(rendered_stack, obj, 0, top_offset, width, height, zindex, enchantments);
                top_offset = dims[0];
                width = dims[1];
                height = dims[2];
                zindex = dims[3];
            }
            /*stack_span.css("width", width + 8);
            stack_span.css("height", height + 8);*/

            rendered_stack.width = width + 8;
            rendered_stack.height = height + 8;

            rendered_stacks.push(rendered_stack);
        }
    }

    $scope.createStacks = function(objects) {

        /* Map object ids to list of enchantments */
        var enchantments = {};

        for (var i = 0; i < objects.length; ++i) {
            var obj = in_play[i];
            if (obj.enchanted_id !== null) {
                if (!(obj.enchanted_id in enchantments)) {
                    enchantments[obj.enchanted_id] = [];
                }
                enchantments[obj.enchanted_id].push(obj);
            }
        }

        /* role to list of Stacks (list) of non-aura objects of the same name  */
        var role2stacks = {};
/*        var role2stacks_battle = {};*/

        for (var i = 0; i < objects.length; ++i) {
            var obj = objects[i];

            if (obj.controller !== null && obj.enchanted_id === null) {
                var role = Game.rolemap(obj.controller);
/*                var battle = (obj.tags.indexOf("attacking") >= 0 || obj.tags.indexOf("blocking") >= 0); */

                var role2stacksmap = role2stacks;
/*                if (battle) {
                    role2stacksmap = role2stacks_battle;
                }*/

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

        $scope.player_stacks = role2stacks["player"];
        $scope.opponent_stacks = role2stacks["opponent"];
    }

    $scope.renderCard = function(obj) {
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

        obj["ui_color"] = color;

        var types = obj.supertypes.join(" ") + " " + obj.types.join(" ");
        if (obj.subtypes.length > 0) {
            types += " – ";
        }

        types += obj.subtypes.join(" ");

        obj["ui_types"] = types;

        return obj;
    }

    $scope.render = function(message) {
        /* alert("" + message["player"] + " " + Game.role);* /

        var in_play = message["in_play"];
        $scope.createStacks(in_play);

        /* $scope.hand = message["players"][""]["hand"]*/

        for (var i = 0; i < message["players"].length; ++i) {
            var player = message["players"][i];
            if (player["role"] == Game.role) {

                $scope.hand = [];
                for (var j = 0; j < player["hand"].length; ++j) {
                    $scope.hand.push ($scope.renderCard(player["hand"][j]));
                }
                $scope.hand = player["hand"];
            }
        }

        $scope.actions = [];
        if (message["player"] == Game.role) {
            $scope.actions = message["actions"];

            for (var i = 0; i < $scope.actions.length; ++i) {
                $scope.actions[i].index = i;
            }
        }
    }

    Game.statusHandler = function(message) {
        $scope.$apply (function() {
            $scope.render(message);
            /* $scope.messages.push(message); */
        });
    }

    /* Game has already been initialized, display current state */
    if (Game.state != null) {
        $scope.render(Game.state);
    }

    console.log("game controller initialized");

  }]);


