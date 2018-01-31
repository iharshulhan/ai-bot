# -*- coding: utf-8 -*-


import telebot

from games.tic_tac_toe import TicTacToeGameSpec
import logging
from WolframApi import Wolfram
import Config
import re
import GameState as games
from Matches import Matches
from techniques.min_max import min_max_alpha_beta


#TODO: add commands in @FatherBot
#/start
#/info
#/matchesclose
#/smallXOclose
#/bigXOclose
#/Stas_comeback

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(Config.token)


# MATH, MATCHES, TICTACTOE_SMALL, TICTACTOE_BIG = range(4)

def unknown(bot, update):
    bot.send_message(update.message.chat_id,
                     text='Sorry, I didn\'t understand you')


def solve(message, args):
    try:
        response_text, response_images = Wolfram.ask(args)

        if response_text is None and response_images is None:
            bot.send_message(message.chat.id, ":( Try to rephrase your query.")
            return

        if response_text:
            bot.send_message(message.chat.id, "Result: " + response_text)

        for title, image in response_images:
            bot.send_message(message.chat.id, title + ":")
            bot.send_photo(message.chat.id, image)

    except ValueError:
        logging.error("Solve error.")
        bot.send_message(message.chat.id, 'Something went wrong with the Wolfram Alpha :c')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

@bot.message_handler(commands=['help', 'info', 'h'])
def help(message):
    msg = """This bot provides you ability to play several games in parallel.

1. TicTacToe (3x3)
input: [x..z][1..3] to pick cell for your next move
/smallXOclose - command to close your current game

2. TicTacToe (10x10)
input: [a..j][1..10] to pick cell for your next move
/bigXOclose - command to close your current game

3. Matches
input: [1..4] to pick sticks amount
/matchesclose - command to close your current game

4. Feature to get mathematical knowledge of machine brain
input any mathematical (or other interesting for machine) request and I'll provide you answer.

P.S. /Stas_comeback to return Stas Protasov at IU. Use it carefully ;)"""
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['smallXOclose'])
def close_xo3(message):
    try:
        games.finish_user_game(Config.sh_xo_3, message.chat.id)
        bot.send_message(message.chat.id, "Game successfully closed.")
    except:
        logger.log(msg="close None game XO 3x3")


@bot.message_handler(commands=['bigXOclose'])
def close_xo15(message):
    try:
        games.finish_user_game(Config.sh_xo_15, message.chat.id)
        bot.send_message(message.chat.id, "Game successfully closed.")
    except:
        logger.log(msg="close None game XO 15x15")


@bot.message_handler(commands=['matchesclose'])
def close_matches(message):
    try:
        games.finish_user_game(Config.sh_matches, message.chat.id)
        bot.send_message(message.chat.id, "Game successfully closed.")
    except:
        logger.log(msg="close None game Matches")


@bot.message_handler(commands=['Stas_comeback'])
def send_Stas(message):
    bot.send_photo(message.chat.id, photo=open('res/stas.jpeg', 'rb'))

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hello, user!")
    help(message)

def do_matches(message, args):
    state = games.get_game_state_for_user(Config.sh_matches, message.chat.id)
    msg, state, bmv = Matches.turn(state, int(args))
    bot.send_message(message.chat.id, msg)
    if not bmv is None:
        bot.send_message(message.chat.id, "Bot's move: " + str(bmv))
    if not state is None:
        games.set_user_game(Config.sh_matches, message.chat.id, state)
        bot.send_message(message.chat.id, "Sticks lost: " + str(state))

def do_xo_small(message, args):
    chat_id = message.chat.id
    board_state = games.get_game_state_for_user(Config.sh_xo_3, message.chat.id)
    game_spec = TicTacToeGameSpec()
    print("DEBUG: ", args)
    if board_state is None:
        board_state = game_spec.new_board()

    # User's move
    user_move = symbols_to_tuple(args)
    print("User's move: ", user_move)

    
    try:
        board_state = game_spec.apply_move(board_state, user_move, 1)
    except  ValueError:
        bot.send_message(chat_id, "The cell is occupied. Try again please \n")
        return
    print("User board")
    bot.send_message(chat_id, "Your turn: \n" + serialize_board(board_state))

    winner = game_spec.has_winner(board_state)
    if winner == 1:
        bot.send_message(chat_id, "You won!!!")
        games.finish_user_game(Config.sh_xo_3, chat_id)
        return
    elif winner == -1:
        bot.send_message(chat_id, "Bot won!!! Bot is really smart ^ ^")
        games.finish_user_game(Config.sh_xo_3, chat_id)
        return
    
    # Check if it is a Draw
    sum = 0
    num = 0
    for x in board_state:
        for y in x:
            sum += y
            if y != 0:
                num += 1
    if num == 9 and sum == 0:
        bot.send_message(chat_id, "Draw! We both are awesome :)")
        games.finish_user_game(Config.sh_xo_3, chat_id)
        return

    # Bot's move
    bot_move = min_max_alpha_beta(game_spec, board_state, -1, 1000)[1] 
    board_state = game_spec.apply_move(board_state, bot_move, -1)
    bot.send_message(chat_id, "Bot's turn: \n" + serialize_board(board_state))

    winner = game_spec.has_winner(board_state)
    if winner == 1:
        bot.send_message(chat_id, "You won!!!")
        games.finish_user_game(Config.sh_xo_3, chat_id)
    if winner == -1:
        bot.send_message(chat_id, "Bot won!!! Bot is really smart ^ ^")
        games.finish_user_game(Config.sh_xo_3, chat_id)

    # Check if it is a Draw
    sum = 0
    num = 0
    for x in board_state:
        for y in x:
            sum += y
            if y != 0:
                num += 1
    if num == 9 and sum == 0:
        bot.send_message(chat_id, "Draw! We both are awesome :)")
        games.finish_user_game(Config.sh_xo_3, chat_id)
        return

    games.set_user_game(Config.sh_xo_3, message.chat.id, board_state)

def symbols_to_tuple(s):
    mapping = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'k': 8, 'l': 9,
               'x': 0, 'y': 1, 'z': 2}
    letter = s[0]
    print(letter)
    number = s[1]

    return (mapping[letter], int(number)-1)

def serialize_board(board_state):
    #print("Board_state: ", board_state[0], "\n", board_state[1], "\n", board_state[2])
    serialized = ""
    for row in board_state:
        print(row)
        for cell in row:
            if cell == 1:
                serialized += 'x'
            elif cell == -1:
                serialized += 'o'
            elif cell == 0:
                serialized += '.'

        serialized += '\n'
    return serialized
        

def do_xo_big(message, args):
    pass

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    if re.compile("^[-+]?[0-9]$").match(message.text):
        # TODO: integrate Matches game and rooms. May be limit will be not almost 9 due to game rules
        print("Matches: ", message.text)
        do_matches(message, message.text)

    elif re.compile("^[x-z|X-Z][1-3]$").match(message.text):
        # TODO: integrate TicTacToe 3x3. !!!!!!!!!!!!!!! КОЛЛИЗИИ С ПОЛЕМ 15х15
        # upd: коллизии решены за счёт того что буквы будут с конца алфавита (смекалочка)

        bot.send_message(message.chat.id, "There XO (3x3) game.")
        do_xo_small(message, message.text)

    elif re.compile("^[a-o|A-O][0-9]+$").match(message.text):
        # TODO: integrate TicTacToe 15x15
        print("XO 15x15: ", message.text)
        bot.send_message(message.chat.id, "There XO (15x15) game. Not implemented yet.")

    else:
        print("Wolfram: ", message.text)
        message.chat.id, solve(message=message, args=message.text)


def main():
    """Start the bot."""
    bot.polling(none_stop=True)



if __name__ == '__main__':
    main()
