import telebot

import logging
from WolframApi import Wolfram
import Config
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(Config.token)


# MATH, MATCHES, TICTACTOE_SMALL, TICTACTOE_BIG = range(4)

def unknown(bot, update):
    bot.send_message(update.message.chat_id,
                     text='Sorry, I didn\'t understand you')


def solve(args):
    try:
        response = Wolfram.ask(args)
        return response
    except ValueError:
        logging.error(response)
        return 'Something went wrong with the Wolfram Alpha :c'


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

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):  # Название функции не играет никакой роли, в принципе
    if re.compile("^[-+]?[0-9]$").match(message.text):
        # TODO: integrate Matches game and rooms. May be limit will be not almost 9 due to game rules
        print("Matches: ", message.text)
        bot.send_message(message.chat.id, "There Matches game. Not implemented yet.")

    elif re.compile("^[a-c|A-C][1-3]$").match(message.text):
        # TODO: integrate TicTacToe 3x3. !!!!!!!!!!!!!!! КОЛЛИЗИИ С ПОЛЕМ 15х15
        print("XO 3x3: ", message.text)
        bot.send_message(message.chat.id, "There XO (3x3) game. Not implemented yet.")

    elif re.compile("^[a-o|A-O][0-9]+$").match(message.text):
        # TODO: integrate TicTacToe 15x15
        print("XO 15x15: ", message.text)
        bot.send_message(message.chat.id, "There XO (15x15) game. Not implemented yet.")

    else:
        print("Wolfram: ", message.text)
        bot.send_message(message.chat.id, solve(args=message.text))


def main():
    """Start the bot."""
    bot.polling(none_stop=True)



if __name__ == '__main__':
    main()
