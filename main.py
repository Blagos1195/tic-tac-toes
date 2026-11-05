import multiprocessing as mp
import os
import random as r
import signal
import sys
import threading
import time
import ai as ai
# 8 and 9 may be impossible to beat
VERBOSE = True  # Set to True to print board each move during human play
VS = 3  # 1: Random opponent, 2: Human player, 3: AI Self-Play
TEMPERATURE = 0.01  # Exploration factor
MIN_TEMP = 0.01  # Floor for temperature decay
DECAY_RATE = 0.9999  # Decay factor applied per game
GAMES_PER_WORKER = 10000  # Number of games each core plays locally per batch
TOTAL_GAMES = 10000000  # Total games to run
REPORT_EVERY = 100000  # Games played between status updates/saves

RUNNING = True


def display_board(board):
    if VERBOSE or VS == 2:
        print("")
        print(board[0] + "|" + board[1] + "|" + board[2])
        print(board[3] + "|" + board[4] + "|" + board[5])
        print(board[6] + "|" + board[7] + "|" + board[8])


def listener():
    global TEMPERATURE, VERBOSE, VS, MIN_TEMP, DECAY_RATE, RUNNING
    while RUNNING:
        if VS == 2:
            time.sleep(0.5)
            continue
        try:
            cmd = input()
            if cmd:
                exec(cmd, globals())
        except Exception as e:
            print(f"Error: {e}")


def init_worker(memX, memO):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    sys.stdin = open(os.devnull)
    ai.ai_memory["X"] = memX.copy()
    ai.ai_memory["O"] = memO.copy()


def run_worker_batch(args):
    temp, vs_mode, games_to_play = args
    local_stats = {"Computer": 0, "Player": 0, "Tie": 0}

    for _ in range(games_to_play):
        board = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        turnsO = []
        turnsX = []
        current_turn = "Computer" if r.randint(0, 1) == 0 else "Player"

        while True:
            if current_turn == "Player":
                if vs_mode == 1:
                    while True:
                        choice = r.randint(1, 9)
                        idx = choice - 1
                        if board[idx] not in ["X", "O"]:
                            board[idx] = "X"
                            break
                elif vs_mode == 3:
                    state_before_move = "".join(board)
                    computerChoice = ai.get_ai_moveX(board, temp)
                    board[computerChoice] = "X"
                    turnsX.append(
                        state_before_move + "|" + str(computerChoice)
                    )

                if (
                    (board[0] == "X" and board[1] == "X" and board[2] == "X")
                    or (board[3] == "X" and board[4] == "X" and board[5] == "X")
                    or (board[6] == "X" and board[7] == "X" and board[8] == "X")
                    or (board[0] == "X" and board[3] == "X" and board[6] == "X")
                    or (board[1] == "X" and board[4] == "X" and board[7] == "X")
                    or (board[2] == "X" and board[5] == "X" and board[8] == "X")
                    or (board[0] == "X" and board[4] == "X" and board[8] == "X")
                    or (board[2] == "X" and board[4] == "X" and board[6] == "X")
                ):
                    winner = "Player"
                    ai.update_ai_memoryO(turnsO, -1.0)
                    ai.update_ai_memoryX(turnsX, 1.0)
                    local_stats[winner] += 1
                    break

                elif all(spot in ["X", "O"] for spot in board):
                    winner = "Tie"
                    ai.update_ai_memoryO(turnsO, 0.3)
                    ai.update_ai_memoryX(turnsX, 0.3)
                    local_stats[winner] += 1
                    break

                current_turn = "Computer"

            else:
                state_before_move = "".join(board)
                computerChoice = ai.get_ai_moveO(board, temp)
                board[computerChoice] = "O"
                turnsO.append(state_before_move + "|" + str(computerChoice))

                if (
                    (board[0] == "O" and board[1] == "O" and board[2] == "O")
                    or (board[3] == "O" and board[4] == "O" and board[5] == "O")
                    or (board[6] == "O" and board[7] == "O" and board[8] == "O")
                    or (board[0] == "O" and board[3] == "O" and board[6] == "O")
                    or (board[1] == "O" and board[4] == "O" and board[7] == "O")
                    or (board[2] == "O" and board[5] == "O" and board[8] == "O")
                    or (board[0] == "O" and board[4] == "O" and board[8] == "O")
                    or (board[2] == "O" and board[4] == "O" and board[6] == "O")
                ):
                    winner = "Computer"
                    ai.update_ai_memoryO(turnsO, 1.0)
                    ai.update_ai_memoryX(turnsX, -1.0)
                    local_stats[winner] += 1
                    break

                elif all(spot in ["X", "O"] for spot in board):
                    winner = "Tie"
                    ai.update_ai_memoryO(turnsO, 0.3)
                    ai.update_ai_memoryX(turnsX, 0.3)
                    local_stats[winner] += 1
                    break

                current_turn = "Player"

    return local_stats, ai.ai_memory


def merge_memory(main_mem, worker_mem):
    for player in ["X", "O"]:
        for state, moves in worker_mem[player].items():
            if state not in main_mem[player]:
                main_mem[player][state] = moves
            else:
                main_mem[player][state].update(moves)


if __name__ == "__main__":
    t = threading.Thread(target=listener, daemon=True)
    t.start()

    stats = {"Computer": 0, "Player": 0, "Tie": 0}
    games_played = 0

    num_cores = mp.cpu_count()

    pool = mp.Pool(
        processes=num_cores,
        initializer=init_worker,
        initargs=(ai.ai_memory["X"], ai.ai_memory["O"]),
    )

    start_time = time.time()
    last_report_time = start_time

    try:
        while games_played < TOTAL_GAMES:
            if VS == 2:
                board = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
                turnsO = []
                turnsX = []
                display_board(board)
                current_turn = "Computer" if r.randint(0, 1) == 0 else "Player"
                while True:
                    if current_turn == "Player":
                        choice = input("Enter position (1-9): ")
                        if choice.isdigit():
                            idx = int(choice) - 1
                            if 0 <= idx <= 8 and board[idx] not in ["X", "O"]:
                                board[idx] = "X"
                                display_board(board)
                                if (
                                    (
                                        board[0] == "X"
                                        and board[1] == "X"
                                        and board[2] == "X"
                                    )
                                    or (
                                        board[3] == "X"
                                        and board[4] == "X"
                                        and board[5] == "X"
                                    )
                                    or (
                                        board[6] == "X"
                                        and board[7] == "X"
                                        and board[8] == "X"
                                    )
                                    or (
                                        board[0] == "X"
                                        and board[3] == "X"
                                        and board[6] == "X"
                                    )
                                    or (
                                        board[1] == "X"
                                        and board[4] == "X"
                                        and board[7] == "X"
                                    )
                                    or (
                                        board[2] == "X"
                                        and board[5] == "X"
                                        and board[8] == "X"
                                    )
                                    or (
                                        board[0] == "X"
                                        and board[4] == "X"
                                        and board[8] == "X"
                                    )
                                    or (
                                        board[2] == "X"
                                        and board[4] == "X"
                                        and board[6] == "X"
                                    )
                                ):
                                    print("You win!")
                                    ai.update_ai_memoryO(turnsO, -1.0)
                                    ai.update_ai_memoryX(turnsX, 1.0)
                                    stats["Player"] += 1
                                    break
                                elif all(spot in ["X", "O"] for spot in board):
                                    print("It's a tie!")
                                    ai.update_ai_memoryO(turnsO, 0.3)
                                    ai.update_ai_memoryX(turnsX, 0.3)
                                    stats["Tie"] += 1
                                    break
                                current_turn = "Computer"
                    else:
                        state_before_move = "".join(board)
                        computerChoice = ai.get_ai_moveO(board, TEMPERATURE)
                        board[computerChoice] = "O"
                        display_board(board)
                        turnsO.append(
                            state_before_move + "|" + str(computerChoice)
                        )
                        if (
                            (
                                board[0] == "O"
                                and board[1] == "O"
                                and board[2] == "O"
                            )
                            or (
                                board[3] == "O"
                                and board[4] == "O"
                                and board[5] == "O"
                            )
                            or (
                                board[6] == "O"
                                and board[7] == "O"
                                and board[8] == "O"
                            )
                            or (
                                board[0] == "O"
                                and board[3] == "O"
                                and board[6] == "O"
                            )
                            or (
                                board[1] == "O"
                                and board[4] == "O"
                                and board[7] == "O"
                            )
                            or (
                                board[2] == "O"
                                and board[5] == "O"
                                and board[8] == "O"
                            )
                            or (
                                board[0] == "O"
                                and board[4] == "O"
                                and board[8] == "O"
                            )
                            or (
                                board[2] == "O"
                                and board[4] == "O"
                                and board[6] == "O"
                            )
                        ):
                            print("Computer wins!")
                            ai.update_ai_memoryO(turnsO, 1.0)
                            ai.update_ai_memoryX(turnsX, -1.0)
                            stats["Computer"] += 1
                            break
                        elif all(spot in ["X", "O"] for spot in board):
                            print("It's a tie!")
                            ai.update_ai_memoryO(turnsO, 0.3)
                            ai.update_ai_memoryX(turnsX, 0.3)
                            stats["Tie"] += 1
                            break
                        current_turn = "Player"
                games_played += 1
            else:
                batch_args = [
                    (TEMPERATURE, VS, GAMES_PER_WORKER) for _ in range(num_cores)
                ]
                results = pool.map(run_worker_batch, batch_args)

                batch_games = GAMES_PER_WORKER * num_cores

                for local_stats, worker_memory in results:
                    for key in stats:
                        stats[key] += local_stats[key]
                    merge_memory(ai.ai_memory, worker_memory)

                games_played += batch_games
                TEMPERATURE = max(
                    MIN_TEMP, TEMPERATURE * (DECAY_RATE**batch_games)
                )

                pool.starmap(
                    init_worker,
                    [(ai.ai_memory["X"], ai.ai_memory["O"])] * num_cores,
                )

            if games_played >= REPORT_EVERY and (
                games_played // REPORT_EVERY
                > (games_played - batch_games) // REPORT_EVERY
            ):
                now = time.time()
                interval_time = now - last_report_time
                gps = (
                    REPORT_EVERY / interval_time if interval_time > 0 else 0
                )
                avg_gps = (
                    games_played / (now - start_time)
                    if (now - start_time) > 0
                    else 0
                )
                last_report_time = now

                ai.save_memoryO()
                ai.save_memoryX()

                tie_rate = (stats["Tie"] / games_played) * 100
                win_rate = (stats["Computer"] / games_played) * 100
                print(
                    f"Game {games_played}/{TOTAL_GAMES} | "
                    f"GPS: {gps:.0f} (Avg: {avg_gps:.0f}) | "
                    f"Win Rate: {win_rate:.1f}% | Tie Rate: {tie_rate:.1f}% | "
                    f"Temp: {TEMPERATURE:.4f} [Saved]"
                )

    except KeyboardInterrupt:
        print("\nTraining stopped manually by user.")

    finally:
        RUNNING = False
        pool.terminate()
        pool.join()
        ai.save_memoryO()
        ai.save_memoryX()
        print("AI memory successfully saved to JSON files.")