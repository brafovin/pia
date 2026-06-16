#!/usr/bin/env python3
import random
import os

# Chaos Tic Tac Toe
# 5x5 Board, 4 in a row gewinnt
# Jeder Spieler hat 3 Sonderzüge:
#   BOMBE  — löscht ein gegnerisches Feld
#   TAUSCH — tauscht zwei eigene Felder
#   BLOCK  — sperrt ein leeres Feld für 1 Runde (niemand darf rein)

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

SIZE = 5
WIN = 4

def empty_board():
    return [["." for _ in range(SIZE)] for _ in range(SIZE)]

def print_board(board, blocked=None):
    blocked = blocked or set()
    print("\n     " + "   ".join(str(i+1) for i in range(SIZE)))
    print("   +" + "───+" * SIZE)
    for r in range(SIZE):
        row_str = f" {r+1} |"
        for c in range(SIZE):
            cell = board[r][c]
            if (r, c) in blocked:
                cell = "▓"
            if cell == "X":
                cell = "\033[91mX\033[0m"
            elif cell == "O":
                cell = "\033[94mO\033[0m"
            elif cell == "▓":
                cell = "\033[90m▓\033[0m"
            row_str += f" {cell} |"
        print(row_str)
        print("   +" + "───+" * SIZE)
    print()

def parse_pos(s):
    parts = s.strip().replace(",", " ").split()
    if len(parts) != 2:
        return None
    try:
        r, c = int(parts[0]) - 1, int(parts[1]) - 1
        if 0 <= r < SIZE and 0 <= c < SIZE:
            return (r, c)
    except ValueError:
        pass
    return None

def check_winner(board, symbol):
    dirs = [(0,1),(1,0),(1,1),(1,-1)]
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != symbol:
                continue
            for dr, dc in dirs:
                count = 0
                for i in range(WIN):
                    nr, nc = r + dr*i, c + dc*i
                    if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == symbol:
                        count += 1
                    else:
                        break
                if count == WIN:
                    return True
    return False

def is_full(board, blocked):
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == "." and (r,c) not in blocked:
                return False
    return True

def print_powers(powers, name):
    p = powers
    print(f"  Sonderzüge [{name}]:  💣 Bombe x{p['bombe']}  🔄 Tausch x{p['tausch']}  🚫 Block x{p['block']}")

def do_bombe(board, opponent):
    print(f"\n  💣 BOMBE — Wähle ein Feld des Gegners ({opponent}) zum Löschen:")
    print("  Format: Reihe Spalte  (z.B. 2 3)")
    while True:
        pos = parse_pos(input("  > "))
        if pos and board[pos[0]][pos[1]] == opponent:
            board[pos[0]][pos[1]] = "."
            print(f"  Feld {pos[0]+1},{pos[1]+1} wurde gelöscht!")
            return
        print("  Ungültig — wähle ein Feld mit dem Gegner-Symbol!")

def do_tausch(board, symbol):
    print(f"\n  🔄 TAUSCH — Wähle zwei eigene Felder ({symbol}) zum Tauschen:")
    positions = []
    for i in range(2):
        while True:
            pos = parse_pos(input(f"  Feld {i+1}: "))
            if pos and board[pos[0]][pos[1]] == symbol and pos not in positions:
                positions.append(pos)
                break
            print("  Ungültig!")
    (r1,c1),(r2,c2) = positions
    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
    print(f"  Felder {r1+1},{c1+1} und {r2+1},{c2+1} getauscht!")

def do_block(board, blocked):
    print(f"\n  🚫 BLOCK — Wähle ein leeres Feld zum Sperren (1 Runde):")
    while True:
        pos = parse_pos(input("  > "))
        if pos and board[pos[0]][pos[1]] == "." and pos not in blocked:
            blocked.add(pos)
            print(f"  Feld {pos[0]+1},{pos[1]+1} gesperrt für 1 Runde!")
            return
        print("  Ungültig — nur leere, ungesperrte Felder!")

def player_turn(board, symbol, opponent, powers, blocked, name):
    print_board(board, blocked)
    print_powers(powers, name)
    print(f"\n  [{name}] {symbol} ist dran")
    print("  [1-5 1-5] Normal setzen  |  [b] Bombe  |  [t] Tausch  |  [k] Block")

    while True:
        raw = input("  > ").strip().lower()

        if raw == "b":
            if powers['bombe'] <= 0:
                print("  Keine Bomben mehr!")
                continue
            has_enemy = any(board[r][c] == opponent for r in range(SIZE) for c in range(SIZE))
            if not has_enemy:
                print("  Kein gegnerisches Feld vorhanden!")
                continue
            do_bombe(board, opponent)
            powers['bombe'] -= 1
            return

        elif raw == "t":
            if powers['tausch'] <= 0:
                print("  Keine Tausch-Züge mehr!")
                continue
            own = [(r,c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == symbol]
            if len(own) < 2:
                print("  Zu wenige eigene Felder zum Tauschen!")
                continue
            do_tausch(board, symbol)
            powers['tausch'] -= 1
            return

        elif raw == "k":
            if powers['block'] <= 0:
                print("  Keine Block-Züge mehr!")
                continue
            do_block(board, blocked)
            powers['block'] -= 1
            return

        else:
            pos = parse_pos(raw)
            if pos is None:
                print("  Ungültige Eingabe! Format: Reihe Spalte (z.B. 2 3)")
                continue
            r, c = pos
            if pos in blocked:
                print("  Dieses Feld ist gesperrt!")
                continue
            if board[r][c] != ".":
                print("  Feld bereits belegt!")
                continue
            board[r][c] = symbol
            return

def main():
    clear()
    print("=" * 52)
    print("       ⚡ CHAOS TIC TAC TOE ⚡")
    print("  5×5 Board  |  4 in einer Reihe gewinnt")
    print("  Jeder hat: 💣 Bombe  🔄 Tausch  🚫 Block")
    print("=" * 52)

    print("\n  Spieler 1 Name (X):")
    p1 = input("  > ").strip() or "Spieler 1"
    print("  Spieler 2 Name (O):")
    p2 = input("  > ").strip() or "Spieler 2"

    while True:
        board = empty_board()
        blocked = set()
        powers = {
            p1: {"bombe": 3, "tausch": 2, "block": 2},
            p2: {"bombe": 3, "tausch": 2, "block": 2},
        }
        players = [(p1, "X", p2), (p2, "O", p1)]
        turn = 0
        winner = None

        while True:
            # Gesperrte Felder nach 1 Runde freigeben
            if turn > 0 and turn % 2 == 0:
                blocked.clear()

            name, symbol, opponent_name = players[turn % 2]
            opp_sym = "O" if symbol == "X" else "X"

            clear()
            player_turn(board, symbol, opp_sym, powers[name], blocked, name)

            if check_winner(board, symbol):
                clear()
                print_board(board, blocked)
                print(f"  🎉 {name} ({symbol}) gewinnt mit 4 in einer Reihe!\n")
                winner = name
                break

            if is_full(board, blocked):
                clear()
                print_board(board, blocked)
                print("  🤝 Unentschieden!\n")
                break

            turn += 1

        again = input("  Nochmal spielen? [j/n]: ").strip().lower()
        if again != "j":
            print("\n  Tschüss!\n")
            break

if __name__ == "__main__":
    main()
