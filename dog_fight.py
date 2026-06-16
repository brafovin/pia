#!/usr/bin/env python3
import random
import time
import os
import subprocess

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def play_sound_67():
    # "67" sound effect on win
    try:
        subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-f", "lavfi",
             "-i", "sine=frequency=67:duration=0.6"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        print("\a", end="", flush=True)

PLAYER_DOGS = [
    {"name": "Chihuahua",   "hp": 60,  "atk": 8,  "emoji": "🐕", "special": "Zittern",    "special_dmg": (18, 28)},
    {"name": "Pudel",       "hp": 80,  "atk": 10, "emoji": "🐩", "special": "Fell-Wirbel", "special_dmg": (22, 32)},
    {"name": "Schäferhund", "hp": 100, "atk": 13, "emoji": "🐺", "special": "Rudel-Biss",  "special_dmg": (28, 40)},
    {"name": "Rottweiler",  "hp": 120, "atk": 16, "emoji": "🦮", "special": "Ramme",        "special_dmg": (35, 50)},
]

ENEMY_DOGS = [
    {"name": "Dackel",      "hp": 20,  "atk": 4,  "xp": 10, "emoji": "🌭"},
    {"name": "Mops",        "hp": 35,  "atk": 7,  "xp": 20, "emoji": "🐶"},
    {"name": "Husky",       "hp": 55,  "atk": 11, "xp": 35, "emoji": "🐕‍🦺"},
    {"name": "Dobermann",   "hp": 75,  "atk": 16, "xp": 55, "emoji": "🦴"},
    {"name": "Höllenhund",  "hp": 120, "atk": 24, "xp": 100,"emoji": "👹"},
]

MOVES = {
    "1": {"name": "Bellen",        "dmg": (6, 12),  "cost": 0,  "desc": "Schneller Angriff"},
    "2": {"name": "Beißen",        "dmg": (12, 20), "cost": 10, "desc": "Fester Biss"},
    "3": {"name": "Spezial",       "dmg": None,     "cost": 25, "desc": "Spezialangriff deiner Rasse"},
    "4": {"name": "Lecken",        "dmg": (0, 0),   "cost": 20, "desc": "Heilt 20 HP"},
}

def bar(val, max_val, length=20, char="█"):
    filled = int(length * val / max_val)
    return char * filled + "░" * (length - filled)

def print_status(player, enemy):
    print("─" * 52)
    print(f"  {player['emoji']} {player['name']:<14} HP: [{bar(player['hp'], player['max_hp'])}] {player['hp']}/{player['max_hp']}")
    print(f"     Juwelen: [{bar(player['stamina'], 100, 14)}] {player['stamina']}/100  |  Lvl {player['level']}  XP: {player['xp']}/{player['xp_next']}")
    print("─" * 52)
    print(f"  {enemy['emoji']} {enemy['name']:<14} HP: [{bar(enemy['hp'], enemy['max_hp'])}] {enemy['hp']}/{enemy['max_hp']}")
    print("─" * 52)

def print_moves(player):
    print("\n  Was tut dein Hund?")
    for key, move in MOVES.items():
        cost = f"  [{move['cost']} Juwelen]" if move['cost'] > 0 else ""
        desc = move['desc']
        if key == "3":
            desc = player['special']
        print(f"  [{key}] {move['name']:<16} {desc}{cost}")
    print(f"  [5] Fliehen")

def level_up(player):
    player['level'] += 1
    player['xp_next'] = int(player['xp_next'] * 1.5)
    player['max_hp'] += 20
    player['hp'] = player['max_hp']
    player['stamina'] = 100
    player['atk'] += 2
    print(f"\n  ⭐ LEVEL UP! {player['name']} ist jetzt Level {player['level']}!")
    print(f"  Max HP: {player['max_hp']}  |  Angriff: {player['atk']}")
    time.sleep(1.5)

def spawn_enemy(player):
    tier = min(player['level'] - 1, len(ENEMY_DOGS) - 1)
    base = random.choice(ENEMY_DOGS[:tier + 1])
    scale = 1 + (player['level'] - 1) * 0.12
    enemy = {
        "name": base["name"],
        "emoji": base["emoji"],
        "hp": int(base["hp"] * scale),
        "atk": int(base["atk"] * scale),
        "xp": int(base["xp"] * scale),
    }
    enemy["max_hp"] = enemy["hp"]
    return enemy

def fight(player, enemy):
    log = []
    fled = False

    while player['hp'] > 0 and enemy['hp'] > 0:
        clear()
        print_status(player, enemy)
        if log:
            print()
            for line in log[-3:]:
                print(f"  {line}")
        print_moves(player)

        choice = input("\n  > ").strip()
        log = []

        if choice == "5":
            if random.random() < 0.5:
                log.append("Du bist erfolgreich geflohen!")
                fled = True
                break
            else:
                log.append("Flucht fehlgeschlagen!")
        elif choice in MOVES:
            move = MOVES[choice]
            if player['stamina'] < move['cost']:
                log.append(f"Nicht genug Juwelen! (Brauchst {move['cost']})")
            else:
                player['stamina'] = max(0, player['stamina'] - move['cost'])
                if choice == "4":
                    heal = 20
                    player['hp'] = min(player['max_hp'], player['hp'] + heal)
                    log.append(f"{player['name']} leckt seine Wunden und heilt {heal} HP!")
                else:
                    if choice == "3":
                        dmg = random.randint(*player['special_dmg'])
                    else:
                        dmg = random.randint(*move['dmg'])
                        dmg += player['atk'] // 3
                    if random.random() < 0.15:
                        dmg = int(dmg * 1.5)
                        log.append(f"💥 KRITISCHER TREFFER!")
                    enemy['hp'] = max(0, enemy['hp'] - dmg)
                    move_name = player['special'] if choice == "3" else move['name']
                    log.append(f"{player['name']} setzt {move_name} ein — {dmg} Schaden!")
        else:
            log.append("Ungültige Eingabe!")
            continue

        if enemy['hp'] <= 0:
            break

        enemy_dmg = random.randint(int(enemy['atk'] * 0.7), int(enemy['atk'] * 1.3))
        player['hp'] = max(0, player['hp'] - enemy_dmg)
        player['stamina'] = min(100, player['stamina'] + 15)
        log.append(f"{enemy['emoji']} {enemy['name']} greift an — {enemy_dmg} Schaden!")

    return fled

def choose_dog():
    clear()
    print("=" * 52)
    print("        🐾 WÄHLE DEINEN HUND 🐾")
    print("=" * 52)
    for i, d in enumerate(PLAYER_DOGS, 1):
        print(f"  [{i}] {d['emoji']} {d['name']:<14} HP: {d['hp']}  ATK: {d['atk']}  Spezial: {d['special']}")
    print()
    while True:
        choice = input("  > ").strip()
        if choice in [str(i) for i in range(1, len(PLAYER_DOGS) + 1)]:
            return PLAYER_DOGS[int(choice) - 1]
        print("  Ungültige Wahl!")

def main():
    clear()
    print("=" * 52)
    print("       🐾 HUNDE KAMPF ARENA 🐾")
    print("=" * 52)

    base = choose_dog()

    player = {
        "name": base["name"],
        "emoji": base["emoji"],
        "hp": base["hp"],
        "max_hp": base["hp"],
        "atk": base["atk"],
        "stamina": 100,
        "special": base["special"],
        "special_dmg": base["special_dmg"],
        "level": 1,
        "xp": 0,
        "xp_next": 50,
        "kills": 0,
    }

    clear()
    print(f"\n  {player['emoji']} {player['name']} betritt die Arena! Besiege alle Hunde!\n")
    time.sleep(1.5)

    while player['hp'] > 0:
        enemy = spawn_enemy(player)
        clear()
        print(f"\n  {enemy['emoji']} Ein {enemy['name']} erscheint und bellt dich an!\n")
        time.sleep(1)

        fled = fight(player, enemy)

        if player['hp'] <= 0:
            clear()
            print("=" * 52)
            print(f"  💀 {player['name']} wurde besiegt!")
            print(f"  Besiegte Hunde: {player['kills']}")
            print(f"  Erreichtes Level: {player['level']}")
            print("=" * 52)
            break

        if fled:
            clear()
            print(f"\n  {player['emoji']} {player['name']} flieht! Erholung...\n")
            player['hp'] = min(player['max_hp'], player['hp'] + 10)
            time.sleep(1.5)
            continue

        if enemy['hp'] <= 0:
            player['kills'] += 1
            player['xp'] += enemy['xp']
            clear()
            play_sound_67()
            print(f"\n  🎉 {enemy['name']} besiegt! +{enemy['xp']} XP  🔊 *67*\n")
            time.sleep(1.2)

            if player['xp'] >= player['xp_next']:
                player['xp'] -= player['xp_next']
                level_up(player)

            if player['kills'] % 3 == 0:
                bonus = 20
                player['hp'] = min(player['max_hp'], player['hp'] + bonus)
                print(f"  🏆 3 Siege Bonus! +{bonus} HP!")
                time.sleep(1)

    print("\n  Spiel beendet. Wuff!\n")

if __name__ == "__main__":
    main()
