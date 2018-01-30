#In this Puzzle there are 21 Match Sticks.
#You and Computer will pick up the sticks one by one.
#Sticks can be picked from 1 to 4.
#The who, picked up the last stick, is the loser.

#http://atozmath.com/Games/21MatchStick.aspx

'''
    Накидал код для теста сохранения игр пользователей. Закодьте потом нормальный AI
    по имеющемуся интерфейсу
'''

max_turn = 4

class Matches:

    def turn(state:int, user_amount:int):
        #returns tuple (answer, new_state, bot_amount)
        #There are some cases of game state such as win/lose etc.
        #In this cases all information will be passed through answer value to user
        #and new_state and bot_amount will be None

        new_state = state
        #check user input
        if(user_amount <= 0):
            return ("Cheat <=> miserable live", None, None)
        if(state - user_amount < 0):
            return("you done wrong move", None, None)
        #accept user input
        new_state = state - user_amount
        #compute my AI ANN super move
        bot_amount = min(max_turn, new_state - 1)
        return ("My turn. I'll take: ", new_state, bot_amount)