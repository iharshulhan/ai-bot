# -*- coding: utf-8 -*-

import shelve
from Config import sh_name

def set_user_game(game, chat_id, state):
    """
    Записываем юзера в игроки и запоминаем состояние его игры
    :param chat_id: id юзера
    :param game: название игры (из Config.py)
    :param state: сериализованное представление игры (поле или число)
    """
    with shelve.open(sh_name) as storage:
        storage[game + str(chat_id)] = state

def finish_user_game(game, chat_id):
    """
    Заканчиваем игру текущего пользователя и удаляем состояние игры из хранилища
    :param chat_id: id юзера
    :param game: название игры (из Config.py)
    """
    with shelve.open(sh_name) as storage:
        if game + str(chat_id) in storage:
            del storage[game + str(chat_id)]


def get_game_state_for_user(game, chat_id):
    """
    Получаем состояние игры для текущего юзера.
    В случае, если человек просто ввёл какие-то символы, не начав игру, возвращаем None
    :param chat_id: id юзера
    :param game: название игры (из Config.py)
    :return: (str) Правильный ответ / None
    """
    with shelve.open(sh_name) as storage:
        try:
            answer = storage[game + str(chat_id)]
            return answer
        # Если человек не играет, ничего не возвращаем
        except KeyError:
            return None


def get_talk_history(chat_id):
    with shelve.open(sh_name) as storage:
        try:
            last_last_history, last_history, text, prob, = storage[str(chat_id)]
            return last_last_history, last_history, text, prob
        except KeyError:
            return None, None, None, None


def set_talk_history(last_last_history, last_history, text, prob, chat_id):
    with shelve.open(sh_name) as storage:
        storage[str(chat_id)] = last_last_history, last_history, text, prob
