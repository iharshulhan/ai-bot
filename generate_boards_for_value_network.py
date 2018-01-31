"""
After using reinforcement learning to train a network, e.g. policy_gradient.py, to play a game well. We then want to
learn to estimate weather that network would win, lose or draw from a given position.

Alpha Go used a database of real positions to get it's predictions from, we don't have that for tic-tac-toe so instead
we generate some random game positions and train off of the results we get playing from those.
"""
import os
import random
import pickle
import numpy as np
import tensorflow as tf

from common.network_helpers import create_network, load_network, save_network, \
    get_deterministic_network_move, create_convolutional_network
from games.tic_tac_toe import TicTacToeGameSpec
from games.tic_tac_toe_x import TicTacToeXGameSpec
from techniques.min_max import min_max_alpha_beta


TRAIN_SAMPLES = 100000
TEST_SAMPLES = 100000

# to play a different game change this to another spec, e.g TicTacToeXGameSpec or ConnectXGameSpec
game_spec = TicTacToeXGameSpec(winning_length=5, board_size=10)

NUMBER_RANDOM_RANGE = (1, game_spec.board_squares() * 0.8)


# it would be good to have real board positions, but failing that just generate random ones
def generate_random_board_position():
    while True:
        board_state = game_spec.new_board()
        number_moves = random.randint(*NUMBER_RANDOM_RANGE)
        side = 1
        for _ in range(number_moves):
            board_state = game_spec.apply_move(board_state, random.choice(list(game_spec.available_moves(board_state))),
                                               side)
            if game_spec.has_winner(board_state) != 0:
                # start again if we hit an already winning position
                continue

            side = -side
        return board_state



def min_max_move_func(board_state, side):
    return min_max_alpha_beta(game_spec, board_state, side, 2)[1]



board_states_training = {}
episode_number = 0
num = 0
avg = 0

while len(board_states_training) < TRAIN_SAMPLES + TEST_SAMPLES:
    board_state = generate_random_board_position()
    board_state_flat = tuple(np.ravel(board_state))

    # only accept the board_state if not already in the dict
    if board_state_flat not in board_states_training:
        import time
        start_time = time.time()
        result = game_spec.play_game(min_max_move_func, min_max_move_func, board_state=board_state)
        end_tim = time.time()
        avg = (avg + (end_tim - start_time))
        if num % 100 == 0:
            print(num)
            print(avg / (num + 1e-20))
        board_states_training[board_state_flat] = float(result)
        num += 1

    if num % 300 == 0:
        with open('board_states_training.p', mode='rb') as f:
            new_train = pickle.load(f)
        board_states_training =  {**board_states_training, **new_train}
        print('len', len(board_states_training))
        with open('board_states_training.p', mode='wb') as f:
            pickle.dump(board_states_training, f)




