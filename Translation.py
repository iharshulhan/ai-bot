from googletrans import Translator
translator = Translator()


def google_translate(source):
    """
    Use google translate
    :param source: string to translate
    :return: English sentence
    """
    res = translator.translate(source, dest='en')
    return res.text
