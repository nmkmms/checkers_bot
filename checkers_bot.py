import requests
from copy import deepcopy
from random import choice

TEAM_NAME = 'host1'
SIDE_CELLS = {1, 2, 3, 4, 5, 12, 13, 20, 21, 28, 29, 30, 31, 32}
RED_CORNER = {1, 2, 3, 4}
BLACK_CORNER = {29, 30, 31, 32}


def wait(color):
    """Wait until my turn."""
    now = {}
    while now.get('whose_turn') != color and not now.get('is_finished'):
        now = requests.get("http://localhost:8081/game").json()['data']


def get_positions(color):
    """Get all allies and enemies checkers."""
    board = requests.get("http://localhost:8081/game").json()['data']['board']
    allies, enemies = [], []
    for checker in board:
        if checker['color'] == color:
            allies.append(checker)
        else:
            enemies.append(checker)

    return allies, enemies


def make_move(move, header):
    resp = requests.post("http://localhost:8081/move", headers=header, json={"move": move})
    print(resp.text)


def abs_move(my, enemy, old_position, new_position, beated_position, row, column):
    """Make abstract move to get beats chain."""
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
    """Find beats chains."""
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


def one_way_step(coif, checker, positions, check):
    """Make one step (top or down)."""
    if checker['column'] != check or checker['row'] % 2 == check // 3:
        if checker['row'] % 2 == 0 and checker['position'] + coif[0] not in positions and \
                0 < checker['position'] + coif[0] < 33:
            return checker['position'], checker['position'] + coif[0]
        elif checker['row'] % 2 == 1 and checker['position'] + coif[1] not in positions and \
                0 < checker['position'] + coif[1] < 33:
            return checker['position'], checker['position'] + coif[1]


def moves_sort(move, color):
    total = 0
    if move[1] in SIDE_CELLS:
        total -= 1
    if (color == 'RED' and move[0] in RED_CORNER) or (color == 'BLACK' and move[0] in BLACK_CORNER):
        total += 1
    return total


def get_next_step(allies, enemies, color):
    """Get all possible steps and beats."""
    positions = [checker['position'] for checker in allies + enemies]
    route, beats = [], []

    coif = [4, 3, 5, 4] if color == "RED" else [-4, -5, -3, -4]
    enemy_coif = [-4, -5, -3, -4] if color == 'RED' else [4, 3, 5, 4]

    # Beats
    for checker in allies:
        temp_beats = find_to_beat(allies, enemies, checker)
        for temp_beat in temp_beats:
            if temp_beat:
                beats.append((checker['position'], temp_beat))

    if beats:
        beats.sort(key=lambda b: -len(b[1]))
        return beats[0][0], beats[0][1][0]

    # Basic moves
    for checker in allies:
        # Top
        step = one_way_step(coif[:2], checker, positions, 0)
        if step:
            route.append(step)
        if checker['king']:
            step = one_way_step(enemy_coif[:2], checker, positions, 0)
            if step:
                route.append(step)

        # Bottom
        step = one_way_step(coif[2:], checker, positions, 3)
        if step:
            route.append(step)
        if checker['king']:
            step = one_way_step(enemy_coif[2:], checker, positions, 3)
            if step:
                route.append(step)

    if route:
        route.sort(key=lambda r: moves_sort(r, color))
    return route[0] if route else None


def run():
    # Init the game
    resp = requests.post(f"http://localhost:8081/game?team_name={TEAM_NAME}")
    j = resp.json()
    color = j['data']['color']
    header = {'Authorization': f'Token {j["data"]["token"]}'}

    # Start game loop:
    while True:
        wait(color)
        allies, enemies = get_positions(color)
        step = get_next_step(allies, enemies, color)
        if not step or requests.get("http://localhost:8081/game").json()['data']['is_finished']:
            break
        print(step, end='  \t')
        make_move(step, header)

    # Define a winner
    if color == requests.get("http://localhost:8081/game").json()['data']['winner']:
        print('I won!')
    else:
        print('I lost:(')


if __name__ == '__main__':
    run()
