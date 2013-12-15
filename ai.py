# Copyright 2013 Marek Schmidt
# 
# This file is part of ManaClash
#
# ManaClash is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ManaClash is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ManaClash.  If not, see <http://www.gnu.org/licenses/>.
#
# 

from actions import Action, ActionSet, PassAction, QueryNumber

from mcio import NullOutput

class TreeNode:
    def __init__ (self, game, player_id, action, actions, depth):
        self.game = game
        self.player_id = player_id
        self.action = action
        self.actions = actions
        self.depth = depth

        self.nodes = {}

        self._score = 0.0

    def expand(self):

        if self.game.end:
            return

        if isinstance(self.action, PassAction) and self.action.text.startswith("Cancel"):
            # ignore cancel action, consider being a dead-end
            return


        if isinstance(self.actions, ActionSet):

            texts = set()

            filtered_actions = []

            mana_texts = set(["[G]","[W]","[B]","[R]","[U]"])

            for action in self.actions.actions:

                # optimization, ignore options that look the same
                if action.text in texts:
                    continue

                if action.text in mana_texts and not (self.actions.text == "Play Mana Abilities" or self.actions.text.startswith("Pay")):
                    continue

                filtered_actions.append (action)
                texts.add(action.text)

            for action in filtered_actions:

                game_next = self.game.copy()
                game_next.output = NullOutput()
                actions_next = game_next.next(action)

                # depth of a non-forking (linear) action is the same as parent
                next_depth = self.depth if len(filtered_actions) == 1 else self.depth + 1

                self.nodes[action] = TreeNode(game_next, self.actions.player_id, action, actions_next, next_depth)

        elif isinstance(self.actions, QueryNumber):
            # 0 to 10 should be enough for most situations
            for action in range(10):
                game_next = self.game.copy()
                game_next.output = NullOutput()
                actions_next = game_next.next(action)

                self.nodes[action] = TreeNode(game_next, self.actions.player_id, action, actions_next, self.depth + 1)
        else:
            raise Exception("not implemented other types than actionset")

    def best_action(self):
        best_score = float('-inf')
        best_action = None
        for action, node in self.nodes.iteritems():

            if isinstance(action, Action):
                print "\taction: %s score: %f leaves: %d" % (action.text, node._score, node.leaves_count())
            else:
                print "\taction: %s score: %f leaves: %d" % (`action`, node._score, node.leaves_count())

            if node._score > best_score:
                best_score = node._score
                best_action = action

        return best_action

    def isLeaf(self):
        return len(self.nodes) == 0

    def leaves_count(self):
        if self.isLeaf():
            return 1
       
        c = 0 
        for _, node in self.nodes.iteritems():
            c += node.leaves_count()

        return c

    def score(self, fn, maximizing_player_id):
        if self.isLeaf():
            self._score = fn(self, maximizing_player_id)
            return self._score
        
        if self.actions.player_id == maximizing_player_id:
            bestValue = float('-inf')
            for _, node in self.nodes.iteritems():
                val = node.score(fn, maximizing_player_id)
                bestValue = max(bestValue, val)

            self._score = bestValue
            return bestValue
        else:
            bestValue = float('inf')
            for _, node in self.nodes.iteritems():
                val = node.score(fn, maximizing_player_id)
                bestValue = min(bestValue, val)

            self._score = bestValue
            return bestValue
        

def expand_to_depth(root, depth, expansions_limit = -1):
    stack = [root]

    expansions = 0

    while len(stack) > 0 and (expansions < expansions_limit or expansions_limit < 0):
        node = stack.pop()
        if node.depth < depth:
            if node.isLeaf():
                node.expand()
                expansions += 1
            for key, nextnode in node.nodes.iteritems():
                stack.insert (0, nextnode)


def default_scoring_fn(node, maximizing_player_id):

    objects_mult = 1.0
    life_mult = 1.0 / 4
    pass_mult = 0.1

    hand_mult = 1.0 / 8

    alpha = 1 if node.player_id == maximizing_player_id else -1

    if node.game.end:
        if maximizing_player_id in node.game.winners:
            return float("inf")

    if isinstance(node.action, PassAction) and node.action.text.startswith("Cancel"):
        return float('-inf') if node.player_id == maximizing_player_id else float('inf')

    player = node.game.obj(maximizing_player_id)
    opponent = node.game.get_next_player(node.game.obj(maximizing_player_id))

    score = 0.0
    for obj in node.game.get_in_play_zone().objects:
        if obj.get_state().controller_id == maximizing_player_id:
            score += objects_mult
        else:
            score -= objects_mult

    score += len(node.game.get_hand(player).objects) * hand_mult
    score -= len(node.game.get_hand(opponent).objects) * hand_mult

    score += player.life * life_mult
    score -= opponent.life * life_mult

    if isinstance(node.action, PassAction):
        score += pass_mult * alpha

    return score

def choose_action(game, actions, depth, max_expansions = -1):
    player_id = actions.player_id

    root = TreeNode(game, None, None, actions, 0)
    expand_to_depth(root, depth, max_expansions)

    root.score(default_scoring_fn, player_id)

    return root.best_action()

