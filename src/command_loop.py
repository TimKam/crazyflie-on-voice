from num2words import num2words
import speech_recognition as sr
from word2number import w2n

"""
This module implements the voice control functionality.
"""


def move(crazyflie, direction, distance):
    """
    Moves the crazyflie from its current position in the provided direction
    :param crazyflie: The crazyflie to be controlled
    :param direction: The direction, into which the crazyflie should move
    :param distance: The distance the crazyflie should move
    """
    print(f'Moving crazyflie: {direction} {distance}')

    if direction == 'go up':
        print()
    elif direction == 'lower':
        print()
    elif direction == 'back':
        print()
    elif direction == 'ahead':
        print()
    elif direction == 'left':
        print()
    elif direction == 'right':
        print()
    elif direction == 'start landing':
        print()
        crazyflie.commander.send_stop_setpoint()




def listen(recognizer, mic, keywords):
    """
    Listens for a set of (keyword, priority) tuples and returns the response
    :param recognizer: speech_recognition Recognizer object
    :param mic: speech_recognition Microphone object
    :param keywords: Iterable of (keyword, priority) tuples
    :return: response string
    """
    response = None
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        response = recognizer.recognize_sphinx(audio, keyword_entries=keywords)
    except sr.RequestError:
        print('CMU Sphinx installation missing or not working.')
    except sr.UnknownValueError:
        print('Could not recognize speech')
    return response


def start_command_loop(crazyflie):
    """
    :param crazyflie: The crazyflie to be controlled
    Starts the voice control command loop
    """
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    directions = [
        'go up',
        'lower',
        'back',
        'ahead',
        'left',
        'right',
        'start landing'
    ]

    distances = [f'{num2words(i)}' for i in range(0, 1000, 10)]

    keyword_entries = {
        'code_word': [
            ('crazy', 1)
        ],
        'direction': [
            (direction, 1) for direction in directions
        ],
        'distance': [
            (distance, 1) for distance in distances
        ]
    }

    responses = {
        'direction': '',
        'distance': ''
    }

    while True:
        print('Waiting for code word...')
        while True:
            word = listen(recognizer, mic, keyword_entries['code_word'])
            if word and 'crazy' in word:
                print(f'Code word received.')
                break
        print('Waiting for direction...')
        while True:
            term = listen(recognizer, mic, keyword_entries['direction'])
            if term and term in directions:
                responses['direction'] = term
                break
        print(f'Direction received: {responses["direction"]}')
        if 'start landing' not in responses['direction']:
            print('Waiting for distance...')
            print(distances)
            while True:
                term = listen(recognizer, mic, keyword_entries['distance'])
                print(term)
                if term and any(distance in term for distance in distances):
                    responses['distance'] = w2n.word_to_num(term)
                    break

            print(f'Distance received: {responses["distance"]}')
        move(crazyflie, responses['direction'], responses["distance"])


start_command_loop(None)
