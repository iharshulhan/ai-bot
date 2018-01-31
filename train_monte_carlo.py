import collections
import random
import pickle
import numpy as np
import time

from techniques.monte_carlo_uct_with_value import monte_carlo_tree_play
from techniques.monte_carlo_uct_with_value import monte_carlo_tree_search_uct_with_value
from games.tic_tac_toe_x import TicTacToeXGameSpec
from techniques.min_max import min_max_alpha_beta
from value_network import gen_model

state_results = collections.defaultdict(float)
state_samples = collections.defaultdict(float)
state_values = collections.defaultdict(float)

# with open('mont_state_values.p', mode='wb') as f:
#     pickle.dump(state_values, f)

# with open('mont_state_results.p', mode='rb') as f:
#     state_results = pickle.load(f)
# with open('mont_state_samples.p', mode='rb') as f:
#     state_samples = pickle.load(f)
# with open('mont_state_values.p', mode='rb') as f:
#     state_values = pickle.load(f)


# state_samples2 = dict(state_samples)
# for x in state_samples2:
#     if state_samples[x] == 0:
#         del state_samples[x]

with open('mont_state_samples.p', mode='wb') as f:
    pickle.dump(state_samples, f)

model = gen_model()
model.load_weights(filepath='value_network_keras')

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


def value_func(board_state):
    result = model.predict(np.array(board_state).reshape(1, 10, 10, 1))

    return result


def make_move_network_train(board_state, side):
    start_time = time.time()
    avg_result, move = monte_carlo_tree_search_uct_with_value(game_spec, board_state, side, 1, value_func, 0.1, 0.7,
                                                              state_results, state_values, state_samples,
                                                              make_move_min_max_train)
    end_time = time.time()
    # print(move, side, end_time - start_time, 'montecarlo', avg_result)
    return move


def make_move_network(board_state, side):
    start_time = time.time()
    move = monte_carlo_tree_play(game_spec, board_state, side, value_func, 0.1,
                                             state_results, state_values, state_samples, make_move_min_max_train)
    end_time = time.time()
    print(move, side, end_time - start_time, 'montecarlo')
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
        with open('mont_state_results.p', mode='wb') as f:
            pickle.dump(state_results, f)
        with open('mont_state_values.p', mode='wb') as f:
            pickle.dump(state_values, f)
        with open('mont_state_samples.p', mode='wb') as f:
            pickle.dump(state_samples, f)
