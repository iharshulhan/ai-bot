# -*- coding: utf-8 -*-
import collections
import uuid
import pickle
from time import sleep

import io
import telebot
from filelock import FileLock
from PIL import Image
from face_recognition.face_recogntion import add_picture_to_collection, find_face_in_collection
from seq2seq_chat.Seq2SeqTalk import chat
from xo_game.games.tic_tac_toe import TicTacToeGameSpec
from xo_game.games.tic_tac_toe_x import TicTacToeXGameSpec
import logging
from WolframApi import Wolfram
from VoiceRecognizerApi import *
import Config
import re
import GameState as games
import Translation
from Matches import Matches
from xo_game.techniques.min_max import min_max_alpha_beta

from xo_game.techniques.monte_carlo_uct_with_value import monte_carlo_tree_play

from TextToCommand import text_to_command
import cv2
import numpy as np
from YoloPostprocess import post_process

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(Config.token)


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

6. Send a photo to recognize objects (80 different objects supported) or faces. First you need to send one of the commands described later and then a photo. /add_picture_for_identification {name} if you want the bot to remember a picture, /identify_by_photo to ask the bot to identify a person on the photo,  /recognize_objects to recognize objects on the picture

By the way, you can use voice commands and natural phrases in different languages to do those things. 
For example, type "I want to play that incredible Tic Tac Toe" and start playing.

Also you can try to talk with it, however it still needs to learn a lot.

P.S. /Stas_comeback to return Stas Protasov to IU. Use it carefully ;)"""
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


@bot.message_handler(commands=['Stas_comeback', 'stas_comeback'])
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
    sleep(3)
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
    with open('weights/mont_state_results.p', mode='rb') as f:
        state_results = pickle.load(f)
    with open('weights/mont_state_samples.p', mode='rb') as f:
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
    sleep(1.5)
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

    return mapping[letter], int(number) - 1


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
    text = Translation.google_translate(args)
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


what_to_do_with_an_image = 0
name_of_a_person = ''


@bot.message_handler(commands=['add_picture_for_identification'])
def add_image_to_collection_set_var(message):
    global what_to_do_with_an_image, name_of_a_person
    name_of_a_person = message.text.replace('/add_picture_for_identification', '')
    what_to_do_with_an_image = 1
    bot.send_message(message.chat.id, "Okay. Send me an image!")


@bot.message_handler(commands=['recognise_objects'])
def add_image_to_collection_set_var(message):
    global what_to_do_with_an_image
    what_to_do_with_an_image = 0
    bot.send_message(message.chat.id, "Okay. Send me an image!")


@bot.message_handler(commands=['identify_by_photo'])
def add_image_to_collection_set_var(message):
    global what_to_do_with_an_image
    what_to_do_with_an_image = 2
    bot.send_message(message.chat.id, "Okay. Send me an image!")


@bot.message_handler(content_types=["photo"])
def do_smth_with_a_photo(message):
    if what_to_do_with_an_image == 0:
        object_recognition(message)
    if what_to_do_with_an_image == 1:
        add_image_to_collection(message)
    if what_to_do_with_an_image == 2:
        identify_user_by_photo(message)


def object_recognition(message):
    try:
        bot.send_message(message.chat.id, "Got your image. Please, wait.")
        file = bot.get_file(message.photo[-1].file_id)
        image = bot.download_file(file.file_path)
        image = cv2.imdecode(np.fromstring(image, np.uint8), cv2.IMREAD_COLOR)
        resized = cv2.resize(image, (416, 416))
        blob = cv2.dnn.blobFromImage(resized, 1 / 255)
        net = cv2.dnn.readNetFromDarknet("yolo/yolov2.cfg", "yolo/yolov2.weights")
        net.setInput(blob, "data")
        result = net.forward("detection_out")
        post_process(net, 0.6, image, result)
        bot.send_photo(message.chat.id, cv2.imencode(".png", image)[1].tostring())
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "I can't stand when it happens but something went wrong :(")


def add_image_to_collection(message):
    try:
        bot.send_message(message.chat.id, "Got your image. Please, wait.")
        file = bot.get_file(message.photo[-1].file_id)
        image_str = bot.download_file(file.file_path)
        tempBuff = io.BytesIO()
        tempBuff.write(image_str)
        tempBuff.seek(0)
        img = Image.open(tempBuff)
        name = name_of_a_person if name_of_a_person else f'{message.from_user.first_name}_{message.from_user.last_name}'
        img.save(f'/tmp/{file.file_id}.jpg')
        add_picture_to_collection(f'/tmp/{file.file_id}.jpg', name)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "I can't stand when it happens but something went wrong :(")
        return
    bot.send_message(message.chat.id, "Great! I saved it.")


def identify_user_by_photo(message):
    try:
        bot.send_message(message.chat.id, "Got your image. Please, wait.")
        file = bot.get_file(message.photo[-1].file_id)
        image_str = bot.download_file(file.file_path)
        tempBuff = io.BytesIO()
        tempBuff.write(image_str)
        tempBuff.seek(0)
        img = Image.open(tempBuff)
        img.save(f'/tmp/{file.file_id}.jpg')
        user = find_face_in_collection(f'/tmp/{file.file_id}.jpg')
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "I can't stand when it happens but something went wrong :(")
        return

    if user:
        bot.send_message(message.chat.id, f'This is {user.replace("_", " ")} ;)')
    else:
        bot.send_message(message.chat.id, f"Sorry, don't know who you are...")


def has_cyrillic(text):
    return bool(re.search('[а-яА-Я]', text))


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


def main():
    """Start the bot."""
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()
