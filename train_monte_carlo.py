import collections
import random
import pickle
import numpy as np
import time
from copy import copy

from filelock import Timeout, FileLock



from techniques.monte_carlo_uct_with_value import monte_carlo_tree_play
from techniques.monte_carlo_uct_with_value import monte_carlo_tree_search_uct_with_value
from games.tic_tac_toe_x import TicTacToeXGameSpec
from techniques.min_max import min_max_alpha_beta
from value_network import gen_model

state_results = collections.defaultdict(float)
state_samples = collections.defaultdict(float)
state_values = collections.defaultdict(float)

state_results_old = collections.defaultdict(float)
state_samples_old = collections.defaultdict(float)
state_values_old = collections.defaultdict(float)

lock = FileLock("mont_state_results.lock")

with lock:
    with open('mont_state_results.p', mode='rb') as f:
        state_results = pickle.load(f)
    with open('mont_state_samples.p', mode='rb') as f:
        state_samples = pickle.load(f)
    with open('mont_state_values.p', mode='rb') as f:
        state_values = pickle.load(f)

state_results_old = copy(state_results)
state_samples_old = copy(state_samples)
state_values_old = copy(state_values)

# state_samples2 = dict(state_samples)
# for x in state_samples2:
#     if state_samples[x] == 0:
#         del state_samples[x]


# model = gen_model()
# model.load_weights(filepath='value_network_keras')

game_spec = TicTacToeXGameSpec(winning_length=5, board_size=10)


def make_move_min_max(board_state, side):
    start_time = time.time()
    move = min_max_alpha_beta(game_spec, board_state, side, 2)[1]
    end_time = time.time()
    # print(move, side, end_time - start_time, 'minimax')
    return move


def make_move_min_max_train(board_state, side):
    move = min_max_alpha_beta(game_spec, board_state, side, 1)[1]
    return move


# def value_func(board_state):
#     result = model.predict(np.array(board_state).reshape(1, 10, 10, 1))
#
#     return result


def make_move_network_train(board_state, side):
    start_time = time.time()
    avg_result, move = monte_carlo_tree_search_uct_with_value(game_spec, board_state, side, 1, 0.7,
                                                              state_results, state_values, state_samples,
                                                              make_move_min_max_train)
    end_time = time.time()
    # print(move, side, end_time - start_time, 'montecarlo', avg_result)
    return move


def make_move_network(board_state, side):
    start_time = time.time()
    move = monte_carlo_tree_play(game_spec, board_state, side,
                                 state_results, state_values, state_samples, make_move_min_max_train)
    end_time = time.time()
    # print(move, side, end_time - start_time, 'montecarlo')
    return move


results = []
num = 0
while True:
    # randomize if going first or second
    if bool(random.random() > 0.5):
        reward = -game_spec.play_game(make_move_min_max, make_move_network_train)
    else:
        reward = game_spec.play_game(make_move_network_train, make_move_min_max)

    results.append(1 if reward > 0 else 0)
    print(reward)
    num += 1
    if num % 10 == 0:
        print(np.sum(np.array(results)) / num, num)
        with lock:
            with open('mont_state_results.p', mode='rb') as f:
                state_results_copy = pickle.load(f)
            with open('mont_state_samples.p', mode='rb') as f:
                state_samples_copy = pickle.load(f)
            with open('mont_state_values.p', mode='rb') as f:
                state_values_copy = pickle.load(f)


        def dsum(dict1, dict2, dict3):
            ret = collections.defaultdict(float)

            for k, v in dict2.items():
                ret[k] += dict1[k] + dict2[k] - dict3[k]
                if dict2[k] != 0 and ret[k] == 0:
                    ret[k] = dict2[k]
            return ret


        state_results = dsum(state_results_copy, state_results, state_results_old)
        state_samples = dsum(state_samples_copy, state_samples, state_samples_old)
        state_values = {**state_values, **state_values_copy}

        with lock:
            with open('mont_state_results.p', mode='wb') as f:
                pickle.dump(state_results, f)
            with open('mont_state_values.p', mode='wb') as f:
                pickle.dump(state_values, f)
            with open('mont_state_samples.p', mode='wb') as f:
                pickle.dump(state_samples, f)

            with open('mont_state_results_copy.p', mode='wb') as f:
                pickle.dump(state_results, f)
            with open('mont_state_values_copy.p', mode='wb') as f:
                pickle.dump(state_values, f)
            with open('mont_state_samples_copy.p', mode='wb') as f:
                pickle.dump(state_samples, f)

        state_results_old = copy(state_results)
        state_samples_old = copy(state_samples)
        state_values_old = copy(state_values)
