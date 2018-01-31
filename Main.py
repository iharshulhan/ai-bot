# -*- coding: utf-8 -*-

import telebot

import logging
from WolframApi import Wolfram
import Config
import re
import GameState as games
from Matches import Matches


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


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    if re.compile("^[-+]?[0-9]$").match(message.text):
        # TODO: integrate Matches game and rooms. May be limit will be not almost 9 due to game rules
        print("Matches: ", message.text)
        do_matches(message, message.text)

    elif re.compile("^[x-z|X-Z][1-3]$").match(message.text):
        # TODO: integrate TicTacToe 3x3. !!!!!!!!!!!!!!! КОЛЛИЗИИ С ПОЛЕМ 15х15
        # upd: коллизии решены за счёт того что буквы будут с конца алфавита (смекалочка)
        print("XO 3x3: ", message.text)
        bot.send_message(message.chat.id, "There XO (3x3) game. Not implemented yet.")

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
