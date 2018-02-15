import collections
import random
import pickle
import math

import numpy as np

from techniques.monte_carlo import _upper_confidence_bounds


def monte_carlo_tree_search_uct_with_value(game_spec, board_state, side, value_random, state_results, state_samples,
                                           move_func):
    """Evaluate the best from the current board_state for the given side using monte carlo sampling with upper
    confidence bounds for trees.

    Args:
        game_spec (BaseGameSpec): The specification for the game we are evaluating
        board_state (3x3 tuple of int): state of the board
        side (int): side currently to play. +1 for the plus player, -1 for the minus player
        value_random: probability of selecting a random move
        state_samples: precalculated values
        state_results: precalculated values
        move_func: move func when tree is not expanded

    Returns:
        (result(int), move(int,int)): The average result for the best move from this position and what that move was.
    """
    # state_results = collections.defaultdict(float)
    # state_samples = collections.defaultdict(float)
    # state_values = collections.defaultdict(float)

    current_side = side
    current_board_state = board_state
    rollout_path = []
    result = 0

    while result == 0:
        move_states = {move: game_spec.apply_move(current_board_state, move, current_side)
                       for move in game_spec.available_moves(current_board_state)}

        fl = 0
        fl2 = 0
        move_states_available = collections.defaultdict(float)
        move_states_unvisited = collections.defaultdict(float)
        for x in move_states:
            # if move_states[x] not in state_values:
            #     state_values[move_states[x]] = current_side * value_func(current_board_state)
            if move_states[x] in state_samples:
                fl = 1
                move_states_available[x] = move_states[x]
            else:
                fl2 = 1
                move_states_unvisited[x] = move_states[x]
        if not move_states:
            result = 0
            break

        if (fl == 1 and random.random() < value_random) or fl2 == 0:
            sum = 0
            for x in move_states:
                if move_states[x] in state_samples:
                    sum = sum + state_samples[move_states[x]]
            log_total_samples = math.log(sum)
            move = max(move_states_available, key=lambda s:     _upper_confidence_bounds(
                                                                state_results[move_states_available[s]],
                                                                state_samples[move_states_available[s]],
                                                                log_total_samples))
            current_board_state = move_states_available[move]
        else:
            # move = max(move_states_unvisited, key=lambda s: state_values[move_states_unvisited[s]])
            if fl == 0:
                move = move_func(current_board_state, current_side)
            else:
                move = random.choice(list(move_states_unvisited.keys()))
            current_board_state = move_states[move]
            # if current_board_state not in state_values:
            #     state_values[current_board_state] = current_side * value_func(current_board_state)

        rollout_path.append((current_board_state, current_side, move))

        current_side = -current_side

        result = game_spec.has_winner(current_board_state)

    for path_board_state, path_side, move in rollout_path:
        # print(state_samples[board_state])
        state_samples[path_board_state] += 1.
        result *= path_side
        # normalize results to be between 0 and 1 before this it between -1 and 1

        state_results[path_board_state] += result / 2 + 0.5

    board, _, move = rollout_path[0]

    return state_results[board] / state_samples[board], move


def monte_carlo_tree_play(game_spec, board_state, side, state_results, state_samples, move_func):
    """Evaluate the best from the current board_state for the given side using monte carlo sampling with upper
    confidence bounds for trees.

    Args:
        game_spec (BaseGameSpec): The specification for the game we are evaluating
        board_state (3x3 tuple of int): state of the board
        side (int): side currently to play. +1 for the plus player, -1 for the minus player
        state_samples: precalculated values
        state_results: precalculated values
        move_func: move func when tree is not expanded

    Returns:
        move(int,int): The average result for the best move from this position and what that move was.

    """
    # state_results = collections.defaultdict(float)
    # state_samples = collections.defaultdict(float)
    # state_values = collections.defaultdict(float)

    current_side = side
    current_board_state = board_state
    rollout_path = []
    result = 0

    move_states = {move: game_spec.apply_move(current_board_state, move, current_side)
                   for move in game_spec.available_moves(current_board_state)}

    fl = 0
    fl2 = 0
    move_states_available = collections.defaultdict(float)
    move_states_unvisited = collections.defaultdict(float)
    for x in move_states:
        # if move_states[x] not in state_values:
        #     state_values[move_states[x]] = current_side * value_func(current_board_state)
        if move_states[x] in state_samples:
            fl = 1
            move_states_available[x] = move_states[x]
        else:
            fl2 = 1
            move_states_unvisited[x] = move_states[x]

    if fl == 1 or fl2 == 0:
        sum = 0
        for x in move_states:
            if move_states[x] in state_samples:
                sum = sum + state_samples[move_states[x]]

        move = max(move_states_available, key=lambda s: state_results[move_states_available[s]] / state_samples[move_states_available[s]])
    else:
        # move = max(move_states_unvisited, key=lambda s: state_values[move_states_unvisited[s]])
        move = move_func(current_board_state, current_side)

    return move
