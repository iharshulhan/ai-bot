# -*- coding: utf-8 -*-

# In this Puzzle there are 21 Match Sticks.
# You and Computer will pick up the sticks one by one.
# Sticks can be picked from 1 to 4.
# The who, picked up the last stick, is the loser.

# http://atozmath.com/Games/21MatchStick.aspx

max_turn = 4
begin_amount = 21


class Matches:

    def __end_game__(message):
        return message, begin_amount, "new"

    def turn(state, user_amount):
        # returns tuple (answer, new_state, bot_amount)
        # There are some cases of game state such as win/lose etc.
        # In this cases all information will be passed through answer value to user
        # and new_state and bot_amount will be None

        new_state = 0
        if state is None:
            new_state = begin_amount
        else:
            new_state = state
        # check user input
        if user_amount <= 0:
            return ("Cheat <=> miserable live", None, None)
        if new_state - user_amount < 0:
            return ("You've done wrong move", None, None)
        if user_amount > max_turn:
            return ("Wrong move! Maximum value is " + str(max_turn), None, None)
        # accept user input
        new_state = new_state - user_amount
        if new_state == 0:
            return Matches.__end_game__("You lost")
        # compute my AI ANN super move
        bot_amount = min(max_turn, new_state - 1)
        if bot_amount <= 0:
            return Matches.__end_game__("You won")

        new_state -= bot_amount
        return "My turn.", new_state, bot_amount
