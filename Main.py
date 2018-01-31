import telebot

import logging
from WolframApi import Wolfram
import Config
import re
import GameState as games
from Matches import Matches

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
    bot.send_message(message.chat.id, "Input first move or math expression to start action")

@bot.message_handler(commands=['start'])
def start(message):
    #TODO: рассказать как ходить
    pass

def do_matches(message, args):
    state = games.get_game_state_for_user(Config.sh_matches, message.chat.id)
    print("Debug output", args)
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
