import telegram
import logging
from WolframApi import Wolfram
from telegram.ext import (Updater, CommandHandler, MessageHandler,Filters, ConversationHandler, CallbackQueryHandler)
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup) 
import Config


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


#MATH, MATCHES, TICTACTOE_SMALL, TICTACTOE_BIG = range(4)

def start(bot, update):
    button_list = [
                [InlineKeyboardButton("Math", callback_data='math'), InlineKeyboardButton("Matches", callback_data='matches')],
                [InlineKeyboardButton("TicTacToe 3x3", callback_data='3x3'),InlineKeyboardButton("TicTacToe 15x15", callback_data='15x15')]
    ]
    
    keyboard = InlineKeyboardMarkup(button_list)
    update.message.reply_text('Please choose what do you want to do: ', reply_markup=keyboard)

# 
def keyboard_callback(bot, update):
    query = update.callback_query
    
    logger.info('InlineKeyboard query: {}'.format(query.data))

    if query.data == 'math':
            bot.send_message(chat_id=query.message.chat.id, text='Write /solve command with your query.')
    elif query.data == 'matches':
            runMathces(bot, update)
    elif query.data == '3x3':
        runTicTacToeSmall(bot, update)
    elif query.data == '15x15':
        runTicTacToeBig(bot, update)
    else:
        raise NotImplementedError

def runMath(bot, update):
    pass

def runMathces(bot, update):
    pass

def runTicTacToeSmall(bot, update):
    pass

def runTicTacToeBig(bot, update):
    pass

def unknown(bot, update):
    bot.send_message(update.message.chat_id, 
    text='Sorry, I didn\'t understand you')

def solve(bot, update, args):
    try:
        response = Wolfram.ask(args)
        bot.send_message(chat_id=update.message.chat_id, text=response)
    except ValueError:
        logging.error(response)
        bot.send_message(chat_id=update.message.chat_id, text='Something went wrong with the Wolfram Alpha :c')

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)
    

def main():
    """Start the bot."""

    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token=Config.token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    #log all errors
    dispatcher.add_error_handler(error)

    start_handler = CommandHandler('start', start)
    solve_handler = CommandHandler('solve', solve, pass_args=True)    
    callback_handler = CallbackQueryHandler(keyboard_callback) 
    unknown_handler = MessageHandler(Filters.command, unknown)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(solve_handler)
    dispatcher.add_handler(callback_handler)

    dispatcher.add_handler(unknown_handler) # Must be added last! 

    # Start the bot
    updater.start_polling()

if __name__ == '__main__':
    main()