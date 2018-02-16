# -*- coding: utf-8 -*-
import collections
import uuid
import pickle
import telebot
from filelock import FileLock

from Seq2SeqTalk import chat, get_model, weights_file, weights_file_GAN
from games.tic_tac_toe import TicTacToeGameSpec
from games.tic_tac_toe_x import TicTacToeXGameSpec
import logging
from WolframApi import Wolfram
from VoiceRecognizerApi import *
import Config
import re
import GameState as games
import Translation
from Matches import Matches
from techniques.min_max import min_max_alpha_beta

from techniques.monte_carlo_uct_with_value import monte_carlo_tree_play

from TextToCommand import text_to_command

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(Config.token)


# MATH, MATCHES, TICTACTOE_SMALL, TICTACTOE_BIG = range(4)

def unknown(bot, update):
    bot.send_message(update.message.chat_id,
                     text='Sorry, I didn\'t understand you')


@bot.message_handler(commands=['solve'])
def solve(message):
    try:
        args = message.text.replace("/solve", "")
        print("Debug /solve", args)

        response_text, response_images = Wolfram.ask(args)

        if response_text is None and response_images is None:
            bot.send_message(message.chat.id, ":( Try to rephrase your query.")
            return

        if response_text:
            bot.send_message(message.chat.id, "Result: " + response_text)
        if response_images:
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
/smallXO - start a game
/smallXOclose - command to close your current game

2. TicTacToe (10x10)
input: [a..j][1..10] to pick cell for your next move
input: [x..z][1..3] to pick cell for your next move
/bigXO - start a game
/bigXOclose - command to close your current game

3. Matches
input: [1..4] to pick sticks amount
/matches - start a new game
/matchesclose - command to close your current game

4. Feature to get mathematical knowledge of machine brain
input /solve and any mathematical (or other interesting for machine) request and I'll provide you answer

5. Translate your text to english by using /translate command

By the way, you can use voice commands and natural phrases in different languages to do those things. 

Also you can try to talk wit me, simply by messaging me

P.S. /Stas_comeback to return Stas Protasov at IU. Use it carefully ;)"""
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['smallXOclose', 'smallxoclose'])
def close_xo3(message):
    try:
        games.finish_user_game(Config.sh_xo_3, message.chat.id)
        bot.send_message(message.chat.id, "Game successfully closed.")
    except:
        logger.log(msg="close None game XO 3x3")


@bot.message_handler(commands=['bigXOclose', 'bigxoclose'])
def close_xo10(message):
    try:
        games.finish_user_game(Config.sh_xo_10, message.chat.id)
        bot.send_message(message.chat.id, "Game successfully closed.")
    except:
        logger.log(msg="close None game XO 10x10")


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


@bot.message_handler(commands=['matches'])
def print_matches(message):
    state = games.get_game_state_for_user(Config.sh_matches, message.chat.id)
    bot.send_message(message.chat.id, "Let's play! We have " + str(state) + " sticks left. Your turn")


def do_matches(message, args):
    state = games.get_game_state_for_user(Config.sh_matches, message.chat.id)
    msg, state, bmv = Matches.turn(state, int(args))
    bot.send_message(message.chat.id, msg)
    if bmv == 'new':
        games.set_user_game(Config.sh_matches, message.chat.id, state)
        print_matches(message)
        return

    if not bmv is None:
        bot.send_message(message.chat.id, "I'll take: " + str(bmv))
    if not state is None:
        games.set_user_game(Config.sh_matches, message.chat.id, state)
        bot.send_message(message.chat.id, "Sticks left: " + str(state))


@bot.message_handler(commands=['smallXO', 'smallxo', 'smallXo', 'smallxO'])
def print_small_xo(message):
    chat_id = message.chat.id
    board_state = games.get_game_state_for_user(Config.sh_xo_3, message.chat.id)
    game_spec = TicTacToeGameSpec()
    if board_state is None:
        board_state = game_spec.new_board()

    bot.send_message(chat_id, "Make a move: \n" + serialize_3x3_board(board_state))
    games.set_user_game(Config.sh_xo_3, message.chat.id, board_state)


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
    bot.send_message(chat_id, "Your turn: \n" + serialize_3x3_board(board_state))

    def check_winner():
        winner = game_spec.has_winner(board_state)
        if winner == 1:
            bot.send_message(chat_id, "You won!!!")
            games.finish_user_game(Config.sh_xo_3, chat_id)
            return True
        elif winner == -1:
            bot.send_message(chat_id, "Bot won!!! Bot is really smart ^ ^")
            games.finish_user_game(Config.sh_xo_3, chat_id)
            return True
        return False

    if check_winner():
        bot.send_message(chat_id, "Let's try again!")
        print_small_xo(message)
        return

    # Check if it is a Draw
    def check_draw():
        sum = 0
        num = 0
        for x in board_state:
            for y in x:
                sum += y
                if y != 0:
                    num += 1
        if num == 9:
            bot.send_message(chat_id, "Draw! We both are awesome :)")
            games.finish_user_game(Config.sh_xo_3, chat_id)
            return True
        return False

    if check_draw():
        bot.send_message(chat_id, "Let's try again!")
        print_small_xo(message)
        return

    # Bot's move
    bot_move = min_max_alpha_beta(game_spec, board_state, -1, 1000)[1]
    board_state = game_spec.apply_move(board_state, bot_move, -1)
    bot.send_message(chat_id, "Bot's turn: \n" + serialize_3x3_board(board_state))

    if check_winner():
        bot.send_message(chat_id, "Let's try again!")
        print_small_xo(message)
        return

    # Check if it is a Draw
    if check_draw():
        bot.send_message(chat_id, "Let's try again!")
        print_small_xo(message)
        return

    games.set_user_game(Config.sh_xo_3, message.chat.id, board_state)


state_results = collections.defaultdict(float)
state_samples = collections.defaultdict(float)
state_values = collections.defaultdict(float)

lock = FileLock("mont_state_results.lock")


def make_move_min_max_train(board_state, side):
    move = min_max_alpha_beta(game_spec, board_state, side, 3)[1]
    return move


game_spec = TicTacToeXGameSpec(winning_length=5, board_size=10)

with lock:
    with open('mont_state_results.p', mode='rb') as f:
        state_results = pickle.load(f)
    with open('mont_state_samples.p', mode='rb') as f:
        state_samples = pickle.load(f)


@bot.message_handler(commands=['bigXO', 'bigxo', 'bigXo', 'bigxO'])
def print_big_xo(message):
    chat_id = message.chat.id
    board_state = games.get_game_state_for_user(Config.sh_xo_10, message.chat.id)
    game_spec = TicTacToeXGameSpec(winning_length=5, board_size=10)
    if board_state is None:
        board_state = game_spec.new_board()

    bot.send_message(chat_id, "Make a move: \n" + serialize_10x10_board(board_state))
    games.set_user_game(Config.sh_xo_10, message.chat.id, board_state)


def do_xo_big(message, args):
    chat_id = message.chat.id
    board_state = games.get_game_state_for_user(Config.sh_xo_10, message.chat.id)
    game_spec = TicTacToeXGameSpec(winning_length=5, board_size=10)
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
    bot.send_message(chat_id, "Your turn: \n" + serialize_10x10_board(board_state))

    def check_winner():
        winner = game_spec.has_winner(board_state)
        if winner == 1:
            bot.send_message(chat_id, "You won!!!")
            games.finish_user_game(Config.sh_xo_10, chat_id)
            return True
        elif winner == -1:
            bot.send_message(chat_id, "Bot won!!! Bot is really smart ^ ^")
            games.finish_user_game(Config.sh_xo_10, chat_id)
            return True
        return False

    if check_winner():
        bot.send_message(chat_id, "Let's try again!")
        print_big_xo(message)
        return

    # Check if it is a Draw
    def check_draw():
        sum = 0
        num = 0
        for x in board_state:
            for y in x:
                sum += y
                if y != 0:
                    num += 1
        if num == 100:
            bot.send_message(chat_id, "Draw! We both are awesome :)")
            games.finish_user_game(Config.sh_xo_10, chat_id)
            return True
        return False

    if check_draw():
        bot.send_message(chat_id, "Let's try again!")
        print_big_xo(message)
        return

    # Bot's move
    # bot_move = min_max_alpha_beta(game_spec, board_state, -1, 3)[1]
    bot_move = monte_carlo_tree_play(game_spec, board_state, -1,
                                     state_results, state_samples, make_move_min_max_train)
    board_state = game_spec.apply_move(board_state, bot_move, -1)
    bot.send_message(chat_id, "Bot's turn: \n" + serialize_10x10_board(board_state))

    if check_winner():
        bot.send_message(chat_id, "Let's try again!")
        print_big_xo(message)
        return

    # Check if it is a Draw
    if check_draw():
        bot.send_message(chat_id, "Let's try again!")
        print_big_xo(message)
        return

    games.set_user_game(Config.sh_xo_10, message.chat.id, board_state)


def symbols_to_tuple(s):
    mapping = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7, 'i': 8, 'j': 9,
               'x': 0, 'y': 1, 'z': 2, 'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9,
               'X': 0, 'Y': 1, 'Z': 2}
    letter = s[0]
    # print(letter)
    if len(s) > 2:
        number = s[1] + s[2]
    else:
        number = s[1]

    return (mapping[letter], int(number) - 1)


def serialize_3x3_board(board_state):
    mapping = {1: 'X', 2: 'Y', 3: 'Z'}
    serialized = "    1  2  3 \n"
    serialized += "------------ \n"
    for i in range(3):
        serialized += str(mapping[i + 1]) + "| "
        for j in range(3):
            cell = board_state[i][j]
            if cell == 1:
                serialized += ' x '
            elif cell == -1:
                serialized += ' o '
            elif cell == 0:
                serialized += ' . '

        serialized += '\n'
    return serialized


def serialize_10x10_board(board_state):
    mapping = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I  ', 9: 'J '}
    serialized = "     1   2   3   4  5  6  7  8  9  10\n"
    serialized += "     ----------------------------------------- \n"
    for i in range(10):
        serialized += str(mapping[i]) + "| "
        for j in range(10):
            cell = board_state[i][j]
            if cell == 1:
                serialized += 'x   '
            elif cell == -1:
                serialized += 'o   '
            elif cell == 0:
                serialized += '.    '

        serialized += '\n'
    return serialized


@bot.message_handler(commands=['translate'])
def translate(message):
    args = message.text.replace("/translate", "")
    text = Translation.googleTranslate(args)
    bot.send_message(message.chat.id, 'Translation: ' + text)
    return text


def talk_with_bot(message):
    last_last_history, last_history, text, prob = games.get_talk_history(message.chat.id)
    if last_last_history is None:
        last_history = ''
        last_last_history = ''
        text = ''
        prob = 0
    last_last_history, last_history, prob, response = chat(message.from_user.first_name, message.text,
                                                           last_last_history, last_history, text, prob)
    games.set_talk_history(last_last_history, last_history, text, prob, message.chat.id)
    bot.send_message(message.chat.id, response)


def sentence_command(message):
    text = message.text
    if has_cyrillic(text):
        message.text = translate(message)
    # print(message.text)
    cmd, arg = text_to_command(message.text)
    if cmd == 'play':
        if arg == 'tictactoe3x3':
            print_small_xo(message)
        elif arg == 'tictactoe10x10':
            print_big_xo(message)
        elif arg == 'matches':
            print_matches(message)
    elif cmd == 'close':
        if arg == 'tictactoe3x3':
            close_xo3(message)
        elif arg == 'tictactoe10x10':
            close_xo10(message)
        elif arg == 'matches':
            close_matches(message)
    elif cmd == 'evaluate':
        solve(message)
    else:
        talk_with_bot(message)


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    if re.compile("^[-+]?[0-9]$").match(message.text):
        do_matches(message, message.text)

    elif re.compile("^[x-z|X-Z][1-3]$").match(message.text):
        bot.send_message(message.chat.id, "There XO (3x3) game.")
        do_xo_small(message, message.text)

    elif re.compile("^[a-o|A-O][0-9]+$").match(message.text):
        bot.send_message(message.chat.id, "There XO (10x10) game.")
        do_xo_big(message, message.text)

    else:
        sentence_command(message)


@bot.message_handler(content_types=["voice"])
def voice_processing(message):
    try:
        metadata = bot.get_file(message.voice.file_id)
        audio = requests.get("https://api.telegram.org/file/bot{0}/{1}".format(Config.token, metadata.file_path))
        audio = VoiceRecognizer.ogg2pcm(audio.content)
        text = VoiceRecognizer.ask(audio, message.voice.file_size, str(uuid.uuid4()).replace("-", ""))
        # print(text)
        bot.send_message(message.chat.id, 'Got your message: ' + text)
        message.text = text
        sentence_command(message)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "I cannot recognize it. Try again.")


def has_cyrillic(text):
    return bool(re.search('[а-яА-Я]', text))


def main():
    """Start the bot."""
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()
