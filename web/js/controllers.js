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


manaclashControllers.controller('GameCtrl', ['$scope', '$window', '$modal', '$http', 'EventBus', 'SessionManager', 'Game',
  function ($scope, $window, $modal, $http, EventBus, SessionManager, Game) {

    $scope.actions = [];
    $scope.opponent_stacks = [];
    $scope.player_stacks = [];
    $scope.stack = [];
    $scope.text = "";
    $scope.action_map = {};

    $scope.passAction = null;
    $scope.passText = null;

    $scope.tableHeight = $window.innerHeight;
    $scope.stacksHeight = 0;

    $scope.player_hand = [];
    $scope.player_graveyard = [];
    $scope.player_library = [];

    $scope.opponent_hand = [];
    $scope.opponent_graveyard = [];
    $scope.opponent_library = [];
  
    angular.element($window).bind('resize', function() {
        $scope.updateTableSize();
        $scope.$digest();
//        $scope.tableHeight = $window.innerHeight;
//        $scope.$digest();
    });

    $scope.updateTableSize = function() {

        var internalHeight = $scope.stacksHeight + 32; // bottom panel

        if ($window.innerHeight > internalHeight) {
            $scope.tableHeight = $window.innerHeight;
        }
        else {
            $scope.tableHeight = internalHeight;
        }
    }

    $scope.action = function(action) {
        EventBus.send("game.action." + Game.gameid, {'sessionID': SessionManager.sessionID, 'type': 'action', 'action': action.index} );
    }

    $scope.doPassAction = function() {
        if ($scope.passAction != null) {
            $scope.action($scope.passAction);
        }
    }

    $scope.objectAction = function(id) {
        if ($scope.hasObjectAction(id)) {
            $scope.action($scope.action_map[id]);
        }
    }

    $scope.createBattlefieldStackRecursive = function(rendered_stack, root_card, left_offset, top_offset, width, height, zindex, enchantments) {

        var rendered_card = {};

        rendered_stack["cards"].push (rendered_card)

        rendered_card["obj"] = $scope.renderCard(root_card);

        rendered_card["klass"] = "";

        rendered_card["left"] = left_offset;
        rendered_card["top"] = top_offset;
/*        rendered_stack["position"] = , "absolute");*/
        rendered_card["z-index"] = zindex;

        if (root_card.tapped) {
            rendered_card["klass"] = "card_tapped";
            width = Math.max(width, left_offset + 142);
            height = Math.max(height, top_offset + 100);
        }
        else {
            width = Math.max(width, left_offset + 100);
            height = Math.max(height, top_offset + 142);
        }

        /* if the card has an action, get the action class */
        /*
        if ($scope.hasObjectAction(root_card.id)) {
            rendered_card["klass"] += " card_action";
        }
        */

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

    $scope.createBattlefieldStack = function(stack, enchantments) {

        console.log("createBattlefieldStack: " + stack.toSource());

        var rendered_stack = {};
        rendered_stack["cards"] = [];

        var width = 0;
        var height = 0;

        var top_offset = 0;
        var zindex = 0;

        for (var j = 0; j < stack.length; ++j) {
            var obj = stack[j];
            var dims = $scope.createBattlefieldStackRecursive(rendered_stack, obj, 0, top_offset, width, height, zindex, enchantments);
            top_offset = dims[0];
            width = dims[1];
            height = dims[2];
            zindex = dims[3];
        }
        /*stack_span.css("width", width + 8);
        stack_span.css("height", height + 8);*/

        rendered_stack.width = width + 8;
        rendered_stack.height = height + 8;

        return rendered_stack;
    }

    $scope.createStacks = function(objects) {

        /* Map object ids to list of enchantments */
        var enchantments = {};

        console.log("objects: " + objects);

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
        role2stacks["player"] = [];
        role2stacks["opponent"] = [];

        var battlestacks = [];
        var id2battlestack = {}; /* map any attacker/blocker linked with any of the object in the battlestack */

        var battleStackHeights = {};
        battleStackHeights["player"] = 0;
        battleStackHeights["opponent"] = 0;

/*        var role2stacks_battle = {};*/

        for (var i = 0; i < objects.length; ++i) {
            var obj = objects[i];

            if (obj.controller !== null && obj.enchanted_id === null) {

                var role = Game.rolemap(obj.controller);
                var battle = (obj.tags.indexOf("attacking") >= 0 || obj.tags.indexOf("blocking") >= 0);

                if (battle) {
                    /* attacking or blocking, display in battlestacks */

                    var battlestack = null;

                    if (obj.id in id2battlestack) {
                        battlestack = id2battlestack[obj.id];
                    }

                    for (var j = 0; j < obj["blockers"].length; ++j) {
                        if (obj["blockers"][j] in id2battlestack) {
                            battlestack = id2battlestack[obj["blockers"][j]];
                        }
                    }

                    for (var j = 0; j < obj["attackers"].length; ++j) {
                        if (obj["attackers"][j] in id2battlestack) {
                            battlestack = id2battlestack[obj["attackers"][j]];
                        }
                    }

                    if (battlestack == null) {
                        battlestack = {};
                        battlestack["player"] = [];
                        battlestack["opponent"] = [];

                        battlestacks.push(battlestack);
                    }

                    var stack = $scope.createBattlefieldStack ([obj], enchantments)
                    battlestack[role].push( stack );

                    if (stack.height > battleStackHeights[role]) {
                        battleStackHeights[role] = stack.height;
                    }

                    id2battlestack[obj.id] = battlestack;
                    for (var j = 0; j < obj["blockers"].length; ++j) {
                        id2battlestack[obj["blockers"][j]] = battlestack;
                    }

                    for (var j = 0; j < obj["attackers"].length; ++j) {
                        id2battlestack[obj["attackers"][j]] = battlestack;
                    }

                    /*for (var j = 0; j < battlestacks.length; ++j) {
                        var bs_opponent_stack = battlestacks[j]["opponent"];
                        var bs_player_stack = battlestacks[j]["player"];

                        for (var l = 0; l < 
                            /* if (obj["blockers"] bs_opponent_stack[k]["cards"][0].obj.id*/
                     /*   }
                    }*/
                }
                else { 

                    var role2stacksmap = role2stacks;

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
        }

        $scope.stacksHeight = 150 + 150; // player hand + stack

        var stackHeight = 0;
        var stacks = role2stacks["player"];
        var rendered_stacks = [];
        for (var i = 0; i < stacks.length; ++i) {
           var stack = $scope.createBattlefieldStack (stacks[i], enchantments);
           rendered_stacks.push (stack);

           if (stack.height > stackHeight) {
               stackHeight = stack.height;
           }
        }

        $scope.stacksHeight += stackHeight;

        $scope.player_stacks = rendered_stacks;

        stackHeight = 0;
        stacks = role2stacks["opponent"];
        rendered_stacks = [];
        for (var i = 0; i < stacks.length; ++i) {
           var stack = $scope.createBattlefieldStack (stacks[i], enchantments);
           rendered_stacks.push (stack);
           if (stack.height > stackHeight) {
               stackHeight = stack.height;
           }
        }

        $scope.stacksHeight += stackHeight;

        $scope.opponent_stacks = rendered_stacks;

        $scope.stacksHeight += battleStackHeights["opponent"];
        $scope.stacksHeight += battleStackHeights["player"];

        /* temporary testing */
/*
        battlestacks.push({'opponent':[{'cards':[{'title':'Foobar','left':0,'top':0,'z-index':'1'}, {'title':'Foobar II','left':110,'top':0,'z-index':'1'}], 'width':230,'height':150}], 'player':[{'cards':[{'title':'Foobar III','left':0,'top':0,'z-index':'1'}], 'width':108,'height':150}]});

        battlestacks.push({'opponent':[{'cards':[{'title':'Gaga','left':0,'top':0,'z-index':'1'}, {'title':'Gaga II','left':110,'top':0,'z-index':'1'}], 'width':230,'height':150}], 'player':[{'cards':[{'title':'Gaga III','left':0,'top':0,'z-index':'1'}], 'width':108,'height':150}]});
*/
        /* end of temporary testing */

        $scope.battlestacks = battlestacks;

        console.log("battlestacks: " + $scope.battlestacks.toSource());

/*        console.log("player_stacks: " + $scope.player_stacks.toSource());*/
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

        if ($scope.hasObjectAction(obj.id)) {
            obj["ui_color"] += " card_action";
        }

        return obj;
    }

    $scope.renderZone = function(cards) {
        var ret = [];
        for (var j = 0; j < cards.length; ++j) {
            ret.push ($scope.renderCard(cards[j]));
        }

        return ret;
    }

    $scope.render = function(message) {

        $scope.actions = [];
        $scope.action_map = {};
        $scope.passAction = null;
        $scope.passText = "Pass";

        if (message["player"] == Game.role) {

            $scope.text = message["text"];

//            $scope.actions = message["actions"];

            for (var i = 0; i < message["actions"].length; ++i) {
//                console.log("XXX adding to action map  " + $scope.actions[i]["object"]);

                var action = message["actions"][i];
                action.index = i;

                if (action["pass"]) {   
                    $scope.passAction = action;
                    $scope.passText = action["text"];
                    console.log("pass : " + $scope.passText);
                }

                if (action["object"] != null) {
                    console.log("XXX adding to action map  " + action["object"]);

                    $scope.action_map[action["object"]] = action;
                }
                else {
                    $scope.actions.push(action);
                }
            }
        }
        else {
            $scope.text = "Waiting for opponent (" + message["text"] + ")";
        }

        var in_play = message["in_play"];
        $scope.createStacks(in_play);

        $scope.updateTableSize();
    
        $scope.stack = [];
        for (var j = 0; j < message["stack"].length; ++j) {
            $scope.stack.push ($scope.renderCard(message["stack"][j]));
        }

        for (var i = 0; i < message["players"].length; ++i) {
            var player = message["players"][i];
            if (player["role"] == Game.role) {
                $scope.player_hand = $scope.renderZone(player["hand"]);
                $scope.player_library = $scope.renderZone(player["library"]);
                $scope.player_graveyard = $scope.renderZone(player["graveyard"]);
            }
            else {
                $scope.opponent_hand = $scope.renderZone(player["hand"]);
                $scope.opponent_library = $scope.renderZone(player["library"]);
                $scope.opponent_graveyard = $scope.renderZone(player["graveyard"]);
            }
        }
    }

    $scope.hasObjectAction = function(id) {

        console.log("XXX hasObjectAction " + id);

        return id in $scope.action_map;
    }

    $scope.zoneOpen = function(role, zoneName) {

        var zone = $scope[role + "_" + zoneName];

        var renderedZoneName = zoneName;
        if (role == "opponent") {
            renderedZoneName = "Opponents " + zoneName;
        }
        else {
            renderedZoneName = "Your " + zoneName;
        }

        var modalInstance = $modal.open({
          templateUrl: 'zone.html',
          controller: 'GameZoneCtrl',
          size: 'lg',
          resolve: {
            objects: function () {
              return zone;
            },
            zoneName: function () {
              return renderedZoneName;
            }
          }
        });

        modalInstance.result.then(function (selectedAction) {
           $scope.objectAction(selectedAction);
          //$scope.selected = selectedItem;
        }, function () {
//          $log.info('Modal dismissed at: ' + new Date());
        });    
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

manaclashControllers.controller('GameZoneCtrl', ['$scope', '$modalInstance', 'objects', 'zoneName', 
  function ($scope, $modalInstance, objects, zoneName) {
    $scope.objects = objects;
    $scope.zoneName = zoneName;

    $scope.zoneClose = function() {
        $modalInstance.dismiss('cancel');
    }

    $scope.objectAction = function(id) {
        $modalInstance.close(id); 
    }
  }]);

