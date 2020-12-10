import requests
from copy import deepcopy
from random import choice

TEAM_NAME = 'host1'


def wait(color):
    now = {}
    while now.get('whose_turn') != color and not now.get('is_finished'):
        now = requests.get("http://localhost:8081/game").json()['data']


def get_positions(color):
    board = requests.get("http://localhost:8081/game").json()['data']['board']
    # print(board)
    my, enemy = [], []
    for checker in board:
        if checker['color'] == color:
            my.append(checker)
        else:
            enemy.append(checker)

    return my, enemy


def make_move(move, header):
    resp = requests.post("http://localhost:8081/move", headers=header, json={"move": move})
    print(resp.text)


def abs_move(my, enemy, old_position, new_position, beated_position, row, column):
    my, enemy = deepcopy(my), deepcopy(enemy)
    the_checker = None

    for checker in my:
        if checker['position'] == old_position:
            checker['position'] += new_position
            checker['row'] += row
            checker['column'] += column
            the_checker = checker
            break

    for checker in enemy:
        if checker['position'] == old_position + beated_position:
            enemy.remove(checker)
            break

    return my, enemy, the_checker


def find_to_beat(my, enemy, checker, rec=''):
    checker = deepcopy(checker)
    positions = [checker['position'] for checker in my + enemy]
    enemy_positions = [checker['position'] for checker in enemy]
    alpha_beats = []
    # Top
    if checker['column'] != 0 and 't' not in rec:
        # Top left
        if checker['row'] > 1 and checker['position'] - 9 not in positions and 'l' not in rec \
                and (checker['color'] == 'BLACK' or checker['king']):
            beat_position = -4 - (checker['row'] % 2)
            if checker['position'] + beat_position in enemy_positions:
                temp_beat = [checker['position'] - 9]
                temp_my, temp_enemy, temp_checker = abs_move(my, enemy, checker['position'],
                                                             -9, beat_position, -2, -1)
                temp_route = find_to_beat(temp_my, temp_enemy, temp_checker, rec='tl')
                for route in temp_route:
                    alpha_beats.append(temp_beat + route)
                if not temp_route:
                    alpha_beats.append(temp_beat)
        # Top right
        if checker['row'] < 6 and checker['position'] + 7 not in positions and 'r' not in rec \
                and (checker['color'] == 'RED' or checker['king']):
            beat_position = 4 - (checker['row'] % 2)
            if checker['position'] + beat_position in enemy_positions:
                temp_beat = [checker['position'] + 7]
                temp_my, temp_enemy, temp_checker = abs_move(my, enemy, checker['position'],
                                                             7, beat_position, 2, -1)
                temp_route = find_to_beat(temp_my, temp_enemy, temp_checker, rec='tr')
                for route in temp_route:
                    alpha_beats.append(temp_beat + route)
                if not temp_route:
                    alpha_beats.append(temp_beat)

    # Bottom
    if checker['column'] != 3 and 'd' not in rec:
        # Bottom left
        if checker['row'] > 1 and checker['position'] - 7 not in positions and 'l' not in rec \
                and (checker['color'] == 'BLACK' or checker['king']):
            beat_position = -3 - (checker['row'] % 2)
            if checker['position'] + beat_position in enemy_positions:
                temp_beat = [checker['position'] - 7]
                temp_my, temp_enemy, temp_checker = abs_move(my, enemy, checker['position'],
                                                             -7, beat_position, -2, 1)
                temp_route = find_to_beat(temp_my, temp_enemy, temp_checker, rec='dl')
                for route in temp_route:
                    alpha_beats.append(temp_beat + route)
                if not temp_route:
                    alpha_beats.append(temp_beat)
        # Bottom right
        if checker['row'] < 6 and checker['position'] + 9 not in positions and 'r' not in rec \
                and (checker['color'] == 'RED' or checker['king']):
            beat_position = 5 - (checker['row'] % 2)
            if checker['position'] + beat_position in enemy_positions:
                temp_beat = [checker['position'] + 9]
                temp_my, temp_enemy, temp_checker = abs_move(my, enemy, checker['position'],
                                                             9, beat_position, 2, 1)
                temp_route = find_to_beat(temp_my, temp_enemy, temp_checker, rec='dr')
                for route in temp_route:
                    alpha_beats.append(temp_beat + route)
                if not temp_route:
                    alpha_beats.append(temp_beat)

    return alpha_beats


def get_next_step(my, enemy, color):
    positions = [checker['position'] for checker in my + enemy]
    route, beats = [], []

    coif = [4, 3, 5, 4] if color == "RED" else [-4, -5, -3, -4]

    for checker in my:
        temp_beats = find_to_beat(my, enemy, checker)
        for temp_beat in temp_beats:
            if temp_beat:
                beats.append((checker['position'], temp_beat))

    if beats:
        beats.sort(key=lambda b: -len(b[1]))
        return beats[0][0], beats[0][1][0]


    for checker in my:
        # Top
        if checker['column'] != 0 or checker['row'] % 2 == 0:
            if checker['row'] % 2 == 0 and checker['position'] + coif[0] not in positions and 0 < checker['position'] + coif[0] < 33:
                route.append((checker['position'], checker['position'] + coif[0]))
            elif checker['row'] % 2 == 1 and checker['position'] + coif[1] not in positions and 0 < checker['position'] + coif[1] < 33:
                route.append((checker['position'], checker['position'] + coif[1]))
        # Bottom
        if checker['column'] != 3 or checker['row'] % 2 == 1:
            if checker['row'] % 2 == 0 and checker['position'] + coif[2] not in positions and 0 < checker['position'] + coif[2] < 33:
                route.append((checker['position'], checker['position'] + coif[2]))
            elif checker['row'] % 2 == 1 and checker['position'] + coif[3] not in positions and 0 < checker['position'] + coif[3] < 33:
                route.append((checker['position'], checker['position'] + coif[3]))

    return choice(route) if route else None


def run():
    # Init the game
    resp = requests.post(f"http://localhost:8081/game?team_name={TEAM_NAME}")
    j = resp.json()
    color = j['data']['color']
    header = {'Authorization': f'Token {j["data"]["token"]}'}

    # Start game loop:
    while True:
        wait(color)
        my, enemy = get_positions(color)
        step = get_next_step(my, enemy, color)
        if not step or requests.get("http://localhost:8081/game").json()['data']['is_finished']:
            break
        print(step)
        make_move(step, header)

    if color == requests.get("http://localhost:8081/game").json()['data']['winner']:
        print('I won!')
    else:
        print('I lost:(')


if __name__ == '__main__':
    run()
