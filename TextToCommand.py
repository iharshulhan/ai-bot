import nltk
import re
from nltk.corpus import stopwords
from nltk.corpus import brown

nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('universal_tagset')

stopwords = set(stopwords.words('english'))

force_tags = {'play': 'VERB', 'start': 'VERB', 'run': 'VERB',
              'close': 'VERB', 'quit': 'VERB', 'stop': 'VERB', 'end': 'VERB',
              'evaluate': 'VERB', 'calculate': 'VERB', 'solve': 'VERB',
              'tic': 'NOUN', 'tictactoe': 'NOUN'}

TICTACTOE_3X3_REGEX = re.compile("tic\s?tac\s?toe\s?3\s?x\s?3\s*$", re.IGNORECASE)
TICTACTOE_10X10_REGEX = re.compile("tic\s?tac\s?toe\s?10\s?x\s?10\s*$", re.IGNORECASE)
TICTACTOE_REGEX = re.compile("tic\s?tac\s?toe\s*$", re.IGNORECASE)
MATCHES_REGEX = re.compile("matches\s*", re.IGNORECASE)

PLAY_COMMANDS = ['play', 'run', 'start']
STOP_COMMANDS = ['stop', 'close', 'exit', 'quit']
WOLFRAM_COMMANDS = ['evaluate', 'solve', 'find']


def _parse(sentence):
    print(sentence)
    tokens_dirt = nltk.word_tokenize(sentence)
    tokens = []
    for token in tokens_dirt:
        if token in stopwords:
            continue
        tokens.append(token.lower())

    tags = nltk.pos_tag(tokens, tagset='universal')
    print(tags)
    sub = ''
    act = ''
    obj = ''
    prop = ''

    new_tagged_words = [(word, force_tags.get(word, tag)) for word, tag in tags]

    for tag in new_tagged_words:
        if sub == '' and (tag[1] == 'NOUN' and tag[0] != 'Hey'):
            sub += tag[0] + ' '
        elif tag[1] == 'VERB' or tag[1] == 'DET':
            if sub == '':
                sub = 'Me'
            act += tag[0] + ' '
        elif sub != '' and (tag[1] == 'NOUN' or tag[1] == 'NUM' or tag[1] == 'CONJ'):
            obj += tag[0] + ' '
        elif sub != '' and obj == '' and (tag[1] == 'NN' or tag[1] == 'NNP'):
            prop += tag[0] + ' '

    print('Subject: ' + sub + '\nAction: ' + act + '\nObject: ' + obj + '\nProperty: ' + prop)
    with open('TextToCommand.log', 'a') as log_file:
        log_file.write('Subject: ' + sub + '\nAction: ' + act + '\nObject: ' + obj + '\nProperty: ' + prop + '\n\n')
    return (sub, act, obj, prop)


def text_to_command(sentence):
    sub, act, obj, prop = _parse(sentence)

    print(sub, any(cmd in sub for cmd in PLAY_COMMANDS))
    if any(cmd in act for cmd in PLAY_COMMANDS) or any(cmd in sub for cmd in PLAY_COMMANDS):
        if TICTACTOE_3X3_REGEX.match(obj):
            return 'play', 'tictactoe3x3'
        elif TICTACTOE_10X10_REGEX.match(obj):
            return 'play', 'tictactoe10x10'
        elif TICTACTOE_REGEX.match(obj):
            return 'play', 'tictactoe10x10'
        elif MATCHES_REGEX.match(obj):
            return 'play', 'matches'

    elif any(cmd in act for cmd in STOP_COMMANDS) or any(cmd in sub for cmd in STOP_COMMANDS):
        if TICTACTOE_3X3_REGEX.match(obj):
            return 'close', 'tictactoe3x3'
        elif TICTACTOE_10X10_REGEX.match(obj):
            return 'close', 'tictactoe10x10'
        elif MATCHES_REGEX.match(obj):
            return 'close', 'matches'
    elif any(cmd in act for cmd in WOLFRAM_COMMANDS) or any(cmd in sub for cmd in WOLFRAM_COMMANDS):
        if obj == None:
            obj = ''
        return 'evaluate', obj
    else:
        return None, None


def main():
    print(text_to_command("HEY! I want to close that incredible TicTacToe 3x3!"))


if __name__ == '__main__':
    main()
