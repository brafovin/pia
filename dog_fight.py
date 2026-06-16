#!/usr/bin/env python3
import random
import time
import os

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

DOGS = [
    {"name": "Chihuahua",   "hp": 15,  "atk": 3,  "xp": 10, "emoji": "🐕"},
    {"name": "Pudel",       "hp": 25,  "atk": 6,  "xp": 20, "emoji": "🐩"},
    {"name": "Schäferhund", "hp": 40,  "atk": 10, "xp": 35, "emoji": "🐺"},
    {"name": "Rottweiler",  "hp": 60,  "atk": 15, "xp": 55, "emoji": "🦮"},
    {"name": "Höllenhund",  "hp": 100, "atk": 22, "xp": 100,"emoji": "👹"},
]

MOVES = {
    "1": {"name": "Faustschlag",    "dmg": (8, 15),  "cost": 0,  "desc": "Ein schneller Schlag"},
    "2": {"name": "Tritt",          "dmg": (12, 20), "cost": 10, "desc": "Tritt mit voller Kraft"},
    "3": {"name": "Spezialangriff", "dmg": (20, 35), "cost": 25, "desc": "Mächtiger Angriff"},
    "4": {"name": "Heilen",         "dmg": (0, 0),   "cost": 20, "desc": "Heilt 20 HP"},
}

def bar(val, max_val, length=20, char="█"):
    filled = int(length * val / max_val)
    return char * filled + "░" * (length - filled)

def print_status(player, dog):
    print("─" * 50)
    print(f"  👤 {player['name']:<15} HP: [{bar(player['hp'], player['max_hp'])}] {player['hp']}/{player['max_hp']}")
    print(f"     Stamina: [{bar(player['stamina'], 100)}] {player['stamina']}/100  |  Level {player['level']}  XP: {player['xp']}/{player['xp_next']}")
    print("─" * 50)
    print(f"  {dog['emoji']} {dog['name']:<15} HP: [{bar(dog['hp'], dog['max_hp'])}] {dog['hp']}/{dog['max_hp']}")
    print("─" * 50)

def print_moves(player):
    print("\n  Was tust du?")
    for key, move in MOVES.items():
        cost = f"  [{move['cost']} Stamina]" if move['cost'] > 0 else ""
        print(f"  [{key}] {move['name']:<18} {move['desc']}{cost}")
    print(f"  [5] Fliehen")

def level_up(player):
    player['level'] += 1
    player['xp_next'] = int(player['xp_next'] * 1.5)
    player['max_hp'] += 15
    player['hp'] = player['max_hp']
    player['stamina'] = 100
    print(f"\n  ⭐ LEVEL UP! Du bist jetzt Level {player['level']}!")
    print(f"  Max HP erhöht auf {player['max_hp']}!")
    time.sleep(1.5)

def spawn_dog(player):
    tier = min(player['level'] - 1, len(DOGS) - 1)
    base = random.choice(DOGS[:tier + 1])
    scale = 1 + (player['level'] - 1) * 0.1
    dog = {
        "name": base["name"],
        "emoji": base["emoji"],
        "hp": int(base["hp"] * scale),
        "atk": int(base["atk"] * scale),
        "xp": int(base["xp"] * scale),
    }
    dog["max_hp"] = dog["hp"]
    return dog

def fight(player, dog):
    log = []
    fled = False

    while player['hp'] > 0 and dog['hp'] > 0:
        clear()
        print_status(player, dog)
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
                log.append(f"Nicht genug Stamina! (Brauchst {move['cost']})")
            else:
                player['stamina'] = max(0, player['stamina'] - move['cost'])
                if choice == "4":
                    heal = 20
                    player['hp'] = min(player['max_hp'], player['hp'] + heal)
                    log.append(f"Du heilst dich um {heal} HP!")
                else:
                    dmg = random.randint(*move['dmg'])
                    if random.random() < 0.15:
                        dmg = int(dmg * 1.5)
                        log.append(f"💥 KRITISCHER TREFFER!")
                    dog['hp'] = max(0, dog['hp'] - dmg)
                    log.append(f"Du setzt {move['name']} ein und triffst für {dmg} Schaden!")
        else:
            log.append("Ungültige Eingabe!")
            continue

        if dog['hp'] <= 0:
            break

        dog_dmg = random.randint(int(dog['atk'] * 0.7), int(dog['atk'] * 1.3))
        player['hp'] = max(0, player['hp'] - dog_dmg)
        player['stamina'] = min(100, player['stamina'] + 15)
        log.append(f"Der {dog['name']} greift an und trifft für {dog_dmg} Schaden!")

    return fled

def main():
    clear()
    print("=" * 50)
    print("       🐾 HUNDEKAMPF ARENA 🐾")
    print("=" * 50)
    name = input("\n  Dein Name, Kämpfer: ").strip() or "Held"

    player = {
        "name": name,
        "hp": 100,
        "max_hp": 100,
        "stamina": 100,
        "level": 1,
        "xp": 0,
        "xp_next": 50,
        "kills": 0,
    }

    print(f"\n  Willkommen, {name}! Besiege alle Hunde!\n")
    time.sleep(1.5)

    while player['hp'] > 0:
        dog = spawn_dog(player)
        clear()
        print(f"\n  Ein {dog['emoji']} {dog['name']} erscheint!\n")
        time.sleep(1)

        fled = fight(player, dog)

        if player['hp'] <= 0:
            clear()
            print("=" * 50)
            print(f"  💀 Du wurdest besiegt!")
            print(f"  Besiegte Hunde: {player['kills']}")
            print(f"  Erreichtes Level: {player['level']}")
            print("=" * 50)
            break

        if fled:
            clear()
            print(f"\n  Du bist geflohen! Erhole dich...\n")
            player['hp'] = min(player['max_hp'], player['hp'] + 10)
            time.sleep(1.5)
            continue

        if dog['hp'] <= 0:
            player['kills'] += 1
            player['xp'] += dog['xp']
            clear()
            print(f"\n  ✅ {dog['name']} besiegt! +{dog['xp']} XP\n")
            time.sleep(1)

            if player['xp'] >= player['xp_next']:
                player['xp'] -= player['xp_next']
                level_up(player)

            if player['kills'] % 3 == 0:
                bonus = 20
                player['hp'] = min(player['max_hp'], player['hp'] + bonus)
                print(f"  🏆 Bonus! +{bonus} HP für je 3 Siege!")
                time.sleep(1)

    print("\n  Spiel beendet. Auf Wiedersehen!\n")

if __name__ == "__main__":
    main()
