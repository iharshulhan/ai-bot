"""
This is the same as the policy_gradient.py network except that instead of playing against a random opponent. It plays
against previous versions of itself. It is first created with the weights from the "current_network.p" file, if no file
is found there random weights are used. It then creates a series of copies of itself and plays against them.
After "SAVE_HISTORICAL_NETWORK_EVERY" games, it saves it's current weights into the weights of one of the historical
networks. Over time the main network and the historical networks should improve.
"""
import collections
import functools
import os
import random

import numpy as np
import tensorflow as tf

from common.network_helpers import create_convolutional_network, load_network, get_stochastic_network_move, \
    save_network, create_network
from games.tic_tac_toe_x import TicTacToeXGameSpec
from techniques.min_max import min_max_alpha_beta
from techniques.train_policy_gradient import train_policy_gradients
from techniques.train_policy_gradient_historic import train_policy_gradients_vs_historic

SAVE_HISTORICAL_NETWORK_EVERY = 5000
game_spec = TicTacToeXGameSpec(winning_length=5, board_size=10)
HIDDEN_NODES_VALUE = (100, 100, 100)
create_network_func = functools.partial(create_convolutional_network, game_spec)


def min_max_move_func(board_state, side):
    return min_max_alpha_beta(game_spec, board_state, side, 0)[1]


while 1 > 0:
    train_policy_gradients(game_spec, create_network_func,
                           'train_vs_historical.p',
                           opponent_func=min_max_move_func,
                           number_of_games=20000,
                           print_results_every=1000,
                           batch_size=10)

    train_policy_gradients_vs_historic(game_spec, create_network_func,
                                       'train_vs_historical.p',
                                       save_historic_every=SAVE_HISTORICAL_NETWORK_EVERY,
                                       number_of_games=300000,
                                       print_results_every=1000,
                                       batch_size=10)




