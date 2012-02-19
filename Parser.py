# Copyright 2011 Marek Schmidt
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

class NonTerminal:
    def __init__ (self, label):
        self.label = label

    def __repr__ (self):
        return "N("+ self.label +")"

def nt(label):
    return NonTerminal(label)

class Rule:
    def __init__ (self, lhs, rhs, action):
        self.lhs = lhs
        self.rhs = rhs
        self.action = action

    def __repr__ (self):
        return (repr((self.lhs, self.rhs)))

def parse(rules, label, string, debug=False):
    stack = []

    stack.append ( (string, [(Rule("S", [nt(label)], lambda t,x:x), 0, [], "")]) )

    while len(stack) > 0:
        c = stack.pop()

        if debug:
            print(repr(c))

        currentRule = c[1][-1][0]
        currentRulePos = c[1][-1][1]
        currentRuleArgs = c[1][-1][2]
        currentRuleText = c[1][-1][3]
        
        if len(currentRule.rhs) == currentRulePos:
            # parsed the rule, call action and pop
            result = currentRule.action(* ([currentRuleText] + currentRuleArgs))

            if len(c[1]) == 1:
                # touched the bottom, have we parsed the whole input?
                if len(c[0]) == 0:
                    #yes
                    yield result
                else:
                    # no, ignore
                    pass
            else:
                # pass the result to the rule below and advance
                nextc = ( c[0], c[1][:-1] )
                nextc[1][-1] = (nextc[1][-1][0], nextc[1][-1][1] + 1, nextc[1][-1][2] + [result], nextc[1][-1][3] + currentRuleText)

                stack.append (nextc)

        else:
            # terminal or nonterminal?
            currentRuleElement = currentRule.rhs[currentRulePos]
            
            if isinstance(currentRuleElement, NonTerminal):
                for rule in rules:
                    if rule.lhs == currentRuleElement.label:
                        stack.append ( (c[0], c[1][:] + [(rule, 0, [], "")]) )

            else:
                if c[0].startswith(currentRuleElement):
                    nextc = (c[0][len(currentRuleElement):], c[1][:])
                    nextc[1][-1] = (nextc[1][-1][0], nextc[1][-1][1] + 1, nextc[1][-1][2], nextc[1][-1][3] + currentRuleElement)

                    stack.append (nextc)



