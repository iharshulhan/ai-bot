"""
After using reinforcement learning to train a network, e.g. policy_gradient.py, to play a game well. We then want to
learn to estimate weather that network would win, lose or draw from a given position.

Alpha Go used a database of real positions to get it's predictions from, we don't have that for tic-tac-toe so instead
we generate some random game positions and train off of the results we get playing from those.
"""
import random
import pickle
import numpy as np
import tensorflow as tf
from keras.callbacks import ModelCheckpoint
from keras.layers import Conv2D, Dense, Dropout, Input, Flatten
from keras.layers.normalization import BatchNormalization
from keras.models import Model
from keras.optimizers import Adam

from xo_game.games.tic_tac_toe_x import TicTacToeXGameSpec
from xo_game.techniques import min_max_alpha_beta

BATCH_SIZE = 100  # every how many games to do a parameter update?

REINFORCEMENT_NETWORK_PATH = 'train_vs_historical_a_lot_of_training_not_good.p'
VALUE_NETWORK_PATH = 'value_network.p'
TEST_SAMPLES = 5000

# to play a different game change this to another spec, e.g TicTacToeXGameSpec or ConnectXGameSpec
game_spec = TicTacToeXGameSpec(winning_length=5, board_size=10)

NUMBER_RANDOM_RANGE = (1, game_spec.board_squares() * 0.8)


def gen_model(relu_type='relu'):
    input_1 = Input(shape=(10, 10, 1))

    fcnn = Conv2D(64, kernel_size=(3, 3), activation=relu_type, padding='same')(
        BatchNormalization()(input_1))
    fcnn = Dropout(0.3)(fcnn)
    fcnn = Conv2D(128, kernel_size=(3, 3), activation=relu_type, padding='same')(fcnn)
    fcnn = Dropout(0.3)(fcnn)
    fcnn = Conv2D(128, kernel_size=(3, 3), activation=relu_type, padding='same')(fcnn)

    fcnn = Dropout(0.3)(fcnn)
    fcnn = BatchNormalization()(fcnn)
    fcnn = Flatten()(fcnn)

    dense = Dropout(0.2)(fcnn)
    dense = Dense(512, activation=relu_type)(dense)
    dense = Dropout(0.2)(dense)
    dense = Dense(256, activation=relu_type)(dense)
    dense = Dropout(0.2)(dense)
    dense = Dense(512, activation=relu_type)(dense)
    dense = Dropout(0.2)(dense)
    # dense = Dense(256, activation=relu_type)(dense)
    # dense = Dropout(0.2)(dense)
    # dense = Dense(512, activation=relu_type)(dense)
    # dense = Dropout(0.2)(dense)
    # For some reason i've decided not to normalize angle data
    output = Dense(1, activation="sigmoid")(dense)
    model = Model(input_1, output)
    optimizer = Adam()
    model.compile(loss="binary_crossentropy", optimizer=optimizer, metrics=["accuracy"])
    return model


def min_max_move_func(board_state, side):
    return min_max_alpha_beta(game_spec, board_state, side, 2)[1]


if __name__ == '__main__':
    with tf.Session() as session:
        session.run(tf.global_variables_initializer())
        #
        # load_network(session, reinforcement_variables, REINFORCEMENT_NETWORK_PATH)
        #
        # if os.path.isfile(VALUE_NETWORK_PATH):
        #     print("loading previous version of value network")
        #     load_network(session, value_variables, VALUE_NETWORK_PATH)

        # def make_move(board_state, side):
        #     move = get_deterministic_network_move(session, reinforcement_input_layer, reinforcement_output_layer,
        #                                           board_state, side, game_spec=game_spec)
        #
        #     return game_spec.flat_move_to_tuple(np.argmax(move))

        board_states_training = {}
        board_states_test = []
        episode_number = 0
        with open('board_states_training.p', mode='rb') as f:
            board_states_training = pickle.load(f)
        print(len(board_states_training))
        # take a random selection from training into a test set
        for _ in range(TEST_SAMPLES):
            sample = random.choice(list(board_states_training.keys()))
            board_states_test.append((sample, board_states_training[sample]))
            del board_states_training[sample]

        board_states_training = list(board_states_training.items())

        model = gen_model()
        # test_error = model.predict([x[0] for x in board_states_test], [[x[1]] for x in board_states_test], verbose=1, batch_size=10)
        model.summary()
        while True:
            print('started')
            np.random.shuffle(board_states_training)
            train_error = 0
            callbacks = [ModelCheckpoint('value_network_keras', save_best_only=True, monitor='acc')]
            x = np.array([x[0] for x in board_states_training]).reshape(-1, 10, 10, 1)
            y = np.array([1 if x[1] > 0 else 0 for x in board_states_training])
            x_val = np.array([x[0] for x in board_states_test]).reshape(-1, 10, 10, 1)
            y_val = np.array([1 if x[1] > 0 else 0 for x in board_states_test])

            model.fit(x, y, verbose=1, batch_size=10,
                      callbacks=callbacks, epochs=50, validation_data=(x_val, y_val))
            # for start_index in range(0, len(board_states_training) - BATCH_SIZE + 1, BATCH_SIZE):
            #     mini_batch = board_states_training[start_index:start_index + BATCH_SIZE]
            #
            #     batch_error, _ = session.run([error, train_step],
            #                                  feed_dict={value_input_layer: [x[0] for x in mini_batch],
            #                                             target_placeholder: [[x[1]] for x in mini_batch]})
            #     train_error += batch_error
            #
            # new_test_error = session.run(error, feed_dict={value_input_layer: [x[0] for x in board_states_test],
            #                                                target_placeholder: [[x[1]] for x in board_states_test]})

            # print("episode: %s train_error: %s test_error: %s" % (episode_number, train_error, test_error))
            #
            # # if new_test_error > test_error:
            # #     print("train error went up, stopping training")
            # #     break
            #
            # test_error = new_test_error
            episode_number += 1
