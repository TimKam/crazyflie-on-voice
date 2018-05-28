import json
import Levenshtein
from num2words import num2words
import operator
import requests
import speech_recognition as sr
from word2number import w2n

"""
This module implements the voice control functionality.
"""

start_word = 'start'
code_word = 'crazy'
stop_word = 'stop'
land_word = 'land'

directions = [
    'up',
    'down',
    'back',
    'forward',
    'left',
    'right',
    stop_word,
    start_word,
    land_word
]


def generate_protocol_data(direction, distance):
    """
    Generates the command JSON object the Crazyflie control server expects
    :param direction:
    :param distance:
    :return: command to be send to the control server
    """
    if direction == stop_word\
            or direction == start_word\
            or direction == land_word:
        return {'command': direction}
    else:
        distance = distance / 100
        if direction == 'up':
            return {'distance': [0, 0, distance]}
        if direction == 'down':
            return {'distance': [0, 0, -distance]}
        if direction == 'back':
            return {'distance': [0, -distance, 0]}
        if direction == 'forward':
            return {'distance': [0, distance, 0]}
        if direction == 'left':
            return {'distance': [-distance, 0, 0]}
        if direction == 'right':
            return {'distance': [distance, 0, 0]}


def get_best_direction_match(direction_input):
    """
    Returns best direction matched, based on input direction
    :param direction_input: direction as provided by the voice-to-text parser
    :return: best match if score < 4; else None
    """
    levenshtein_scores = {}

    for direction in directions:
        if direction == direction_input:
            return direction
        levenshtein_scores[direction] =\
            Levenshtein.distance(direction, direction_input)

    best_match = min(levenshtein_scores.items(), key=operator.itemgetter(1))
    if best_match[1] < 4:
        return best_match[0]
    return None


def listen(recognizer, mic, keywords, uses_google_api):
    """
    Listens for a set of (keyword, priority) tuples and returns the response
    :param recognizer: speech_recognition Recognizer object
    :param mic: speech_recognition Microphone object
    :param keywords: Iterable of (keyword, priority) tuples
    :param uses_google_api: True if Google API should be used
    :return: response string
    """
    response = None
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        if uses_google_api:
            response = recognizer.recognize_google(audio)
        else:
            response = recognizer.recognize_sphinx(audio,
                                                    keyword_entries=keywords)
    except sr.RequestError:
        print('Voice control setup missing or not working.')
    except sr.UnknownValueError:
        print('Could not recognize speech')
    return response


def start_command_loop(server_url, voice_api):
    """
    Starts the voice control command loop
    :param server_url: URL (incl. port) of the control server to connect to
    :param voice_api: Voice API to use: "google" or "pocketsphinx"
    """

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    if voice_api == 'google' or voice_api is None:
        uses_google_api = True
    else:
        uses_google_api = False

    if uses_google_api:
        distances = [i for i in range(0, 1000, 10)]
    else:
        distances = [f'{num2words(i)}' for i in range(0, 1000, 10)]

    keyword_entries = {
        'code_word': [
            (code_word, 1)
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
        term = listen(recognizer, mic, keyword_entries['code_word'],
                      uses_google_api)
        print(term)
        if term:
            first_word = term.split()[0]
            if len(term.split()) > 1 and code_word in first_word.lower():
                print(f'Code word received.')
                print('Getting direction...')
                direction_term = term.split()[1]
                if direction_term == '*':
                    direction_term = start_word
                best_direction_match =\
                    get_best_direction_match(direction_term)
                if best_direction_match:
                    responses['direction'] = best_direction_match
                    print(f'Direction received: {responses["direction"]}')
                    if len(term.split()) > 2:
                        print('Getting distance...')
                        direction_term = term.split()[2]
                        distance = None
                        if uses_google_api:
                            try:
                                distance = int(direction_term)
                            except (ValueError, TypeError):
                                print(f'{direction_term} is not a number')
                            if distance and distance in distances:
                                responses['distance'] = distance
                        else:
                            if direction_term and any(distance in direction_term for distance in distances):
                                distance = w2n.word_to_num(direction_term)
                                responses['distance'] = distance
                        if distance:
                            print(f'Distance received: {responses["distance"]}')
                            data = generate_protocol_data(
                                responses['direction'],
                                responses['distance']
                            )
                            try:
                                command_request = requests.post(
                                    server_url, data=json.dumps(data))
                                res_content = command_request.content
                                print(f'Send data to server with result: {res_content}')
                            except Exception as e:
                                print(f'Failed to send request: {e}')
                            # break
                    else:
                        try:
                            data = generate_protocol_data(
                                responses['direction'],
                                responses['distance']
                            )
                            command_request = requests.post(
                                server_url, data=json.dumps(data))
                            res_content = command_request.content
                            print(
                                f'Send data to server with result: {res_content}')
                        except Exception as e:
                            print(f'Failed to send request: {e}')
