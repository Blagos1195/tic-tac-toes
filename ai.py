import json
import math
import os
import random

DATA_FILE_X = "aiData10.json"  # Path for storing Player X Q-table
DATA_FILE_O = "aiData9.json"  # Path for storing Player O Q-table
LEARNING_RATE = 0.1  # Alpha learning rate (0.0 to 1.0)
DISCOUNT_FACTOR = 0.9  # Gamma discount factor (0.0 to 1.0)

ai_memory = {"X": {}, "O": {}}


def load_memory():
    if os.path.exists(DATA_FILE_X):
        try:
            with open(DATA_FILE_X, "r") as f:
                ai_memory["X"] = json.load(f)
        except Exception:
            ai_memory["X"] = {}

    if os.path.exists(DATA_FILE_O):
        try:
            with open(DATA_FILE_O, "r") as f:
                ai_memory["O"] = json.load(f)
        except Exception:
            ai_memory["O"] = {}


def save_memoryX():
    with open(DATA_FILE_X, "w") as f:
        json.dump(ai_memory["X"], f)


def save_memoryO():
    with open(DATA_FILE_O, "w") as f:
        json.dump(ai_memory["O"], f)


def get_available_moves(board):
    return [i for i, val in enumerate(board) if val not in ["X", "O"]]


def get_ai_move(board, temperature, player):
    state = "".join(board)
    valid_moves = get_available_moves(board)

    if not valid_moves:
        return None

    if state not in ai_memory[player]:
        ai_memory[player][state] = {str(m): 0.0 for m in valid_moves}
    else:
        for m in valid_moves:
            if str(m) not in ai_memory[player][state]:
                ai_memory[player][state][str(m)] = 0.0

    q_values = [ai_memory[player][state][str(m)] for m in valid_moves]

    if temperature <= 0.01:
        max_q = max(q_values)
        best_moves = [m for m, q in zip(valid_moves, q_values) if q == max_q]
        return random.choice(best_moves)

    try:
        exp_values = [math.exp(q / temperature) for q in q_values]
        total_exp = sum(exp_values)
        probabilities = [e / total_exp for e in exp_values]
        return random.choices(valid_moves, weights=probabilities, k=1)[0]
    except OverflowError:
        max_q = max(q_values)
        best_moves = [m for m, q in zip(valid_moves, q_values) if q == max_q]
        return random.choice(best_moves)


def get_ai_moveX(board, temperature):
    return get_ai_move(board, temperature, "X")


def get_ai_moveO(board, temperature):
    return get_ai_move(board, temperature, "O")


def update_ai_memory(turns, final_reward, player):
    target = final_reward
    for turn_str in reversed(turns):
        state, move_str = turn_str.split("|")
        if state not in ai_memory[player]:
            ai_memory[player][state] = {move_str: 0.0}

        current_q = ai_memory[player][state].get(move_str, 0.0)
        ai_memory[player][state][move_str] = current_q + LEARNING_RATE * (
            target - current_q
        )
        target = ai_memory[player][state][move_str] * DISCOUNT_FACTOR


def update_ai_memoryX(turns, final_reward):
    update_ai_memory(turns, final_reward, "X")


def update_ai_memoryO(turns, final_reward):
    update_ai_memory(turns, final_reward, "O")


load_memory()