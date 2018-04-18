import collections
import random
import pickle
import numpy as np
import time

from filelock import FileLock

from xo_game.techniques import monte_carlo_tree_play
from xo_game.games.tic_tac_toe_x import TicTacToeXGameSpec
from xo_game.techniques import min_max_alpha_beta

state_results = collections.defaultdict(float)
state_samples = collections.defaultdict(float)
state_values = collections.defaultdict(float)

lock = FileLock("mont_state_results.lock")

with lock:
    with open('mont_state_results.p', mode='rb') as f:
        state_results = pickle.load(f)
    with open('mont_state_samples.p', mode='rb') as f:
        state_samples = pickle.load(f)
    with open('mont_state_values.p', mode='rb') as f:
        state_values = pickle.load(f)

game_spec = TicTacToeXGameSpec(winning_length=5, board_size=10)


def make_move_min_max(board_state, side):
    start_time = time.time()
    move = min_max_alpha_beta(game_spec, board_state, side, 3)[1]
    end_time = time.time()
    print(move, side, end_time - start_time, 'minimax')
    return move


def make_move_min_max_train(board_state, side):
    move = min_max_alpha_beta(game_spec, board_state, side, 3)[1]
    return move


def make_move_network(board_state, side):
    start_time = time.time()
    move = monte_carlo_tree_play(game_spec, board_state, side,
                                 state_results, state_values, state_samples, make_move_min_max_train)
    end_time = time.time()
    print(move, side, end_time - start_time, 'montecarlo')
    return move


results = []
num = 0
while True:
    # randomize if going first or second
    if bool(random.random() > 0.5):
        reward = -game_spec.play_game(make_move_min_max, make_move_network)
    else:
        reward = game_spec.play_game(make_move_network, make_move_min_max)

    results.append(1 if reward > 0 else 0)
    print(reward)
    num += 1
    if num % 10 == 0:
        print(np.sum(np.array(results)) / num, num)
