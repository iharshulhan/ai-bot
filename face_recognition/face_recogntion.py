"""
Identify a user from a database of pictures
"""
import cv2
import numpy as np
import os
from shutil import copy2
from face_recognition.align import AlignDlib
from face_recognition.model import create_model

THRESHOLD = 0.8  # this threshold was found to be the best

nn_pretrained = create_model()
nn_pretrained._make_predict_function()
nn_pretrained.load_weights('weights/nn4.small2.v1.h5')


def load_image(path):
    img = cv2.imread(path, 1)
    # OpenCV loads images with color channels
    # in BGR order. So we need to reverse them
    return img[..., ::-1]


# Initialize the OpenFace face alignment utility
alignment = AlignDlib('weights/landmarks.dat')


def distance_between_embedding(emb1, emb2):
    return np.sum(np.square(emb1 - emb2))


def align_image(img):
    return alignment.align(96, img, alignment.getLargestFaceBoundingBox(img),
                           landmarkIndices=AlignDlib.OUTER_EYES_AND_NOSE)


def embedding_from_image(image_path):
    if os.path.exists(f'{image_path}.npy'):
        return np.load(f'{image_path}.npy')

    img = load_image(image_path)
    img = align_image(img)
    # scale RGB values to interval [0,1]
    img = (img / 255.).astype(np.float32)

    # obtain embedding vector for image
    emb = nn_pretrained.predict(np.expand_dims(img, axis=0))[0]
    np.save(f'{image_path}.npy', emb)

    return emb


def find_face_in_collection(face_file_name: str, dir_name: str = 'face_recognition/images') -> [str, None]:
    """
    Compares face with all others in a directory and then return the one with the best match or none, if is not clear
    :param dir_name: a file_path for collection of images
    :param face_file_name: a file_path to an image we want to identify
    :return:
    """
    try:
        face = embedding_from_image(face_file_name)
    except Exception as e:
        print(f'Could not load an image from {face_file_name}. Error {e}')
        return None

    best_score = 1
    best_image = None

    for i in os.listdir(dir_name):
        num_of_pictures = 0
        avg_score = 0
        fl = 0
        for f in os.listdir(os.path.join(dir_name, i)):
            if '.npy' in f:
                continue
            try:
                face_to_compare = embedding_from_image(os.path.join(dir_name, i, f))
            except Exception as e:
                print(f'Could not load an image from {os.path.join(dir_name, i, f)}. Error {e}')
                os.remove(os.path.join(dir_name, i, f))
                continue

            dist = distance_between_embedding(face, face_to_compare)
            if 'Arn' in i:
                print('Arny', dist)
            if 'Ilgiz' in i:
                print('Ilgiz', dist)
            avg_score += dist
            if dist <= THRESHOLD:
                fl = 1
            num_of_pictures += 1

        if fl != 0 and (avg_score / num_of_pictures) < best_score:
            best_score = avg_score / num_of_pictures
            best_image = i  # name of a person

    return best_image


def add_picture_to_collection(file_name: str, user_name: str, dir_name: str = 'face_recognition/images'):
    """
    Adds an image to the collection of images which the bot can recognise
    :param user_name: a name of user to identify him later
    :param dir_name: a file_path for collection of images
    :param file_name: a file_path to an image
    :return:
    """

    try:
        if not os.path.exists(os.path.join(dir_name, f"{user_name}/")):
            os.makedirs(os.path.join(dir_name, f"{user_name}/"))
        copy2(file_name, os.path.join(dir_name, f'{user_name}/'))
    except Exception as e:
        print(f'Could not copy an image from {file_name} to {os.path.join(dir_name, f"{user_name}/")}. Error {e}')
