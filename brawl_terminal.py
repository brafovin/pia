#!/usr/bin/env python3
import random
import os
import time

# ─── BRAWL TERMINAL ───────────────────────────────────────────────────────────
# Gem Grab Modus: 7x11 Arena, sammle 10 Gems, töte Gegner
# Bewegung + Schießen + SUPER Fähigkeit
# 2 Teams: Blau (Spieler) vs Rot (KI)

COLS, ROWS = 11, 7
GEM_WIN = 10
MAX_AMMO = 3
AMMO_REGEN = 3   # Züge bis 1 Ammo regeneriert

BRAWLERS = [
    {
        "name": "Shelly",   "emoji": "🔫", "hp": 5200, "dmg": 900,
        "super_name": "Schrotflinte",
        "super_dmg": 2800, "super_range": 3, "super_splash": True,
        "range": 5, "desc": "Breiter Nahkampf-Schuss, Super trifft alle in der Linie"
    },
    {
        "name": "Colt",     "emoji": "🤠", "hp": 3600, "dmg": 700,
        "super_name": "Kugelhagel",
        "super_dmg": 4200, "super_range": 8, "super_splash": False,
        "range": 7, "desc": "Langer Schuss, Super schießt 6 Kugeln weit"
    },
    {
        "name": "Bull",     "emoji": "🐂", "hp": 6000, "dmg": 1400,
        "super_name": "Stampede",
        "super_dmg": 0, "super_range": 5, "super_splash": False,
        "range": 3, "desc": "Nahkampf-Tank, Super lädt durch und betäubt"
    },
    {
        "name": "Poco",     "emoji": "🎸", "hp": 4200, "dmg": 600,
        "super_name": "Heilsong",
        "super_dmg": -2000, "super_range": 0, "super_splash": False,
        "range": 6, "desc": "Heilt Team mit Super, guter Support"
    },
    {
        "name": "Brock",    "emoji": "🚀", "hp": 3200, "dmg": 1000,
        "super_name": "Raketenhagel",
        "super_dmg": 1600, "super_range": 9, "super_splash": True,
        "range": 8, "desc": "Sniper mit Raketen, Super zerstört Gebiet"
    },
]

ENEMY_BRAWLERS = [
    {"name": "Rosa",  "emoji": "🌸", "hp": 5800, "dmg": 800,  "range": 3, "ai": "aggressive"},
    {"name": "Nita",  "emoji": "🐻", "hp": 4000, "dmg": 900,  "range": 6, "ai": "balanced"},
    {"name": "Spike", "emoji": "🌵", "hp": 3400, "dmg": 1100, "range": 7, "ai": "sniper"},
]

WALLS = {(2,1),(2,2),(4,1),(2,4),(2,5),(4,5),(6,1),(6,2),(8,1),(6,4),(6,5),(8,5)}

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def dist(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS

def is_wall(r, c):
    return (r, c) in WALLS

def make_entity(brawler, pos, team):
    e = dict(brawler)
    e['max_hp'] = e['hp']
    e['pos'] = list(pos)
    e['team'] = team
    e['ammo'] = MAX_AMMO
    e['ammo_timer'] = 0
    e['super_charge'] = 0   # 0-100
    e['stunned'] = 0
    e['gems'] = 0
    e['alive'] = True
    return e

def draw_arena(entities, gems, dropped_gems):
    grid = [["  " for _ in range(COLS)] for _ in range(ROWS)]

    # Wände
    for (wr, wc) in WALLS:
        grid[wr][wc] = "██"

    # Gems
    for (gr, gc) in gems:
        grid[gr][gc] = "💎"
    for (gr, gc) in dropped_gems:
        grid[gr][gc] = "✨"

    # Entities
    for e in entities:
        if e['alive']:
            r, c = e['pos']
            color = "\033[94m" if e['team'] == 'blue' else "\033[91m"
            grid[r][c] = color + e['emoji'] + "\033[0m"

    # Gem-Mine (Mitte)
    mr, mc = ROWS//2, COLS//2
    if grid[mr][mc] == "  ":
        grid[mr][mc] = "⛏ "

    print("  ┌" + "──" * COLS + "┐")
    for row in grid:
        print("  │" + "".join(row) + "│")
    print("  └" + "──" * COLS + "┘")

def draw_hud(player, enemies, blue_gems, red_gems):
    def hp_bar(hp, max_hp, length=10):
        f = int(length * hp / max_hp)
        return "█"*f + "░"*(length-f)

    print(f"\n  \033[94m[BLAU] {player['name']} {player['emoji']}\033[0m")
    print(f"  HP:    [{hp_bar(player['hp'], player['max_hp'])}] {player['hp']}/{player['max_hp']}")
    print(f"  Ammo:  {'🔵'*player['ammo']}{'⚫'*(MAX_AMMO-player['ammo'])}  |  "
          f"Super: [{'█'*int(player['super_charge']//10)}{'░'*(10-int(player['super_charge']//10))}] {player['super_charge']}%")
    print(f"  Gems:  {'💎'*blue_gems}  ({blue_gems}/{GEM_WIN})")

    print()
    for e in enemies:
        status = "💀" if not e['alive'] else ""
        print(f"  \033[91m[ROT] {e['name']} {e['emoji']}\033[0m {status}")
        if e['alive']:
            print(f"  HP:    [{hp_bar(e['hp'], e['max_hp'])}] {e['hp']}/{e['max_hp']}")
    print(f"  Gems:  {'💎'*red_gems}  ({red_gems}/{GEM_WIN})")
    print()

def shoot(shooter, target_pos, all_entities, splash=False, dmg_override=None, range_override=None):
    sr, sc = shooter['pos']
    tr, tc = target_pos
    dmg = dmg_override if dmg_override is not None else shooter['dmg']
    rng = range_override if range_override is not None else shooter['range']
    d = dist(shooter['pos'], target_pos)

    if d > rng:
        return False, "Ziel zu weit entfernt!"
    if is_wall(tr, tc):
        return False, "Eine Mauer blockiert den Schuss!"

    hit = False
    log = []
    for e in all_entities:
        if not e['alive'] or e['team'] == shooter['team']:
            continue
        er, ec = e['pos']
        if splash:
            if dist([tr,tc], [er,ec]) <= 1:
                e['hp'] -= dmg
                hit = True
                log.append(f"{e['name']} trifft für {dmg}!")
                if e['hp'] <= 0:
                    e['alive'] = False
                    log.append(f"💀 {e['name']} ausgeschaltet!")
        else:
            if [er,ec] == [tr,tc]:
                e['hp'] -= dmg
                hit = True
                log.append(f"{e['name']} trifft für {dmg}!")
                if e['hp'] <= 0:
                    e['alive'] = False
                    log.append(f"💀 {e['name']} ausgeschaltet!")

    if hit:
        shooter['super_charge'] = min(100, shooter['super_charge'] + 25)
    return hit, " | ".join(log) if log else "Verfehlt!"

def use_super(player, all_entities, enemies, gems):
    sname = player['super_name']
    log = []

    if player['name'] == "Poco":
        heal = abs(player['super_dmg'])
        player['hp'] = min(player['max_hp'], player['hp'] + heal)
        log.append(f"🎸 {sname}! Heilt {heal} HP!")
        player['super_charge'] = 0
        return log

    if player['name'] == "Bull":
        # Stampede: bewegt sich 3 Felder vorwärts und betäubt
        dr = 0
        dc = 1 if player['pos'][1] < COLS//2 else -1
        for _ in range(5):
            nr, nc = player['pos'][0]+dr, player['pos'][1]+dc
            if not in_bounds(nr, nc) or is_wall(nr, nc):
                break
            player['pos'] = [nr, nc]
            for e in enemies:
                if e['alive'] and e['pos'] == [nr, nc]:
                    e['hp'] -= 2000
                    e['stunned'] = 2
                    log.append(f"🐂 Rammte {e['name']} für 2000! Betäubt!")
                    if e['hp'] <= 0:
                        e['alive'] = False
                        log.append(f"💀 {e['name']} ausgeschaltet!")
        player['super_charge'] = 0
        return log

    # Andere Supers: Wähle Zielrichtung
    print(f"\n  ⚡ SUPER: {sname}! Zielfeld eingeben (Reihe Spalte):")
    while True:
        raw = input("  > ").strip().split()
        try:
            tr, tc = int(raw[0])-1, int(raw[1])-1
            break
        except:
            print("  Ungültig!")

    _, msg = shoot(player, [tr, tc], all_entities,
                   splash=player['super_splash'],
                   dmg_override=player['super_dmg'],
                   range_override=player['super_range'])
    log.append(f"⚡ {sname}! {msg}")
    player['super_charge'] = 0
    return log

def spawn_gems(gems, count=1):
    mr, mc = ROWS//2, COLS//2
    candidates = [(mr+dr, mc+dc) for dr in range(-2,3) for dc in range(-2,3)
                  if in_bounds(mr+dr, mc+dc) and not is_wall(mr+dr, mc+dc)
                  and (mr+dr, mc+dc) not in gems]
    for pos in random.sample(candidates, min(count, len(candidates))):
        gems.add(tuple(pos))

def ai_move(enemy, player, gems, all_entities, dropped_gems, log):
    if not enemy['alive'] or enemy['stunned'] > 0:
        enemy['stunned'] = max(0, enemy['stunned']-1)
        return

    er, ec = enemy['pos']
    ai = enemy.get('ai', 'balanced')

    # Ammo regen
    enemy['ammo_timer'] += 1
    if enemy['ammo_timer'] >= AMMO_REGEN and enemy['ammo'] < MAX_AMMO:
        enemy['ammo'] += 1
        enemy['ammo_timer'] = 0

    # Gems aufsammeln
    for g in list(dropped_gems):
        if list(g) == [er, ec]:
            enemy['gems'] += 1
            dropped_gems.discard(g)

    pd = dist(enemy['pos'], player['pos'])

    # Angreifen wenn in Range und Ammo
    if enemy['ammo'] > 0 and pd <= enemy['range'] and not is_wall(*player['pos']):
        _, msg = shoot(enemy, player['pos'], all_entities)
        enemy['ammo'] -= 1
        log.append(f"  \033[91m{enemy['name']}\033[0m schießt: {msg}")
        return

    # Bewegen
    moves = []
    if ai == 'sniper' and pd > enemy['range']:
        # Auf Spieler zugehen
        moves = [(er + dr, ec + dc) for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]]
    elif ai == 'aggressive':
        moves = [(er + dr, ec + dc) for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]]
    else:
        # Gems holen
        all_gems = list(gems) + list(dropped_gems)
        if all_gems:
            nearest = min(all_gems, key=lambda g: dist([er,ec], list(g)))
            gr, gc = nearest
            moves = [(er + (1 if gr>er else -1 if gr<er else 0), ec),
                     (er, ec + (1 if gc>ec else -1 if gc<ec else 0))]
        else:
            moves = [(er + dr, ec + dc) for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]]

    random.shuffle(moves)
    for nr, nc in moves:
        if in_bounds(nr, nc) and not is_wall(nr, nc):
            occupied = any(e['alive'] and e['pos']==[nr,nc] for e in all_entities)
            if not occupied:
                enemy['pos'] = [nr, nc]
                break

def player_turn(player, enemies, gems, dropped_gems, all_entities):
    log_lines = []
    print("\n  STEUERUNG:")
    print("  [w/a/s/d] Bewegen  [f Reihe Spalte] Schießen  [q] Super  [skip] Aussetzen")
    print(f"  Ammo: {'🔵'*player['ammo']}{'⚫'*(MAX_AMMO-player['ammo'])}  |  Pos: {player['pos'][0]+1},{player['pos'][1]+1}")

    while True:
        raw = input("  > ").strip().lower()

        if raw == "skip":
            log_lines.append("Ausgesetzt.")
            break

        elif raw in ("w","a","s","d"):
            dr, dc = {"w":(-1,0),"s":(1,0),"a":(0,-1),"d":(0,1)}[raw]
            nr, nc = player['pos'][0]+dr, player['pos'][1]+dc
            if not in_bounds(nr, nc):
                print("  Außerhalb der Arena!")
                continue
            if is_wall(nr, nc):
                print("  Mauer!")
                continue
            if any(e['alive'] and e['pos']==[nr,nc] for e in all_entities if e['team']!='blue'):
                print("  Gegner blockiert den Weg!")
                continue
            player['pos'] = [nr, nc]
            log_lines.append(f"Bewegt nach {nr+1},{nc+1}")

            # Gems aufsammeln
            for g in list(dropped_gems):
                if list(g) == [nr, nc]:
                    player['gems'] += 1
                    dropped_gems.discard(g)
                    log_lines.append("💎 Gem aufgesammelt!")
            for g in list(gems):
                if list(g) == [nr, nc]:
                    player['gems'] += 1
                    gems.discard(g)
                    log_lines.append("💎 Gem aufgesammelt!")
            break

        elif raw.startswith("f ") or raw == "f":
            if player['ammo'] <= 0:
                print("  Keine Munition! Bewege dich um aufzuladen.")
                continue
            parts = raw.split()
            if len(parts) != 3:
                print("  Format: f Reihe Spalte (z.B. f 3 5)")
                continue
            try:
                tr, tc = int(parts[1])-1, int(parts[2])-1
            except:
                print("  Ungültig!")
                continue
            if not in_bounds(tr, tc):
                print("  Außerhalb!")
                continue
            hit, msg = shoot(player, [tr, tc], all_entities)
            player['ammo'] -= 1
            log_lines.append(f"Schuss → {msg}")
            break

        elif raw == "q":
            if player['super_charge'] < 100:
                print(f"  Super noch nicht bereit! ({player['super_charge']}%)")
                continue
            msgs = use_super(player, all_entities, enemies, gems)
            log_lines.extend(msgs)
            break

        else:
            print("  Unbekannte Eingabe!")

    # Ammo regen bei Bewegung/Skip
    player['ammo_timer'] += 1
    if player['ammo_timer'] >= AMMO_REGEN and player['ammo'] < MAX_AMMO:
        player['ammo'] += 1
        player['ammo_timer'] = 0

    return log_lines

def choose_brawler():
    clear()
    print("=" * 56)
    print("       ⚡ BRAWL TERMINAL — BRAWLER WÄHLEN ⚡")
    print("=" * 56)
    for i, b in enumerate(BRAWLERS, 1):
        print(f"\n  [{i}] {b['emoji']} {b['name']}")
        print(f"      HP: {b['hp']}  DMG: {b['dmg']}  Range: {b['range']}")
        print(f"      Super: {b['super_name']}")
        print(f"      {b['desc']}")
    print()
    while True:
        c = input("  Wähle (1-5): ").strip()
        if c in [str(i) for i in range(1, len(BRAWLERS)+1)]:
            return dict(BRAWLERS[int(c)-1])
        print("  Ungültig!")

def main():
    brawler_data = choose_brawler()
    player = make_entity(brawler_data, [ROWS//2, 1], 'blue')

    # 2 Gegner spawnen
    e1 = make_entity(dict(random.choice(ENEMY_BRAWLERS)), [ROWS//2 - 1, COLS-2], 'red')
    e2 = make_entity(dict(random.choice(ENEMY_BRAWLERS)), [ROWS//2 + 1, COLS-2], 'red')
    enemies = [e1, e2]
    all_entities = [player] + enemies

    gems = set()
    dropped_gems = set()
    spawn_gems(gems, 3)

    round_num = 0
    respawn_timer = {}

    while True:
        round_num += 1

        # Neue Gems spawnen
        if round_num % 3 == 0:
            spawn_gems(gems, 1)

        # Gems fallen lassen wenn Spieler stirbt (wird unten behandelt)
        blue_gems = player['gems']
        red_gems = sum(e['gems'] for e in enemies)

        clear()
        print(f"  ⚡ BRAWL TERMINAL  |  Runde {round_num}  |  Gem Grab: Erst zu {GEM_WIN} 💎 gewinnt!")
        draw_arena(all_entities, gems, dropped_gems)
        draw_hud(player, enemies, blue_gems, red_gems)

        # Sieg prüfen
        if blue_gems >= GEM_WIN:
            print(f"  🏆 \033[94mDU GEWINNST!\033[0m {player['name']} hat {blue_gems} Gems gesammelt!\n")
            break
        if red_gems >= GEM_WIN:
            print(f"  💀 \033[91mROT GEWINNT!\033[0m Die Gegner haben {red_gems} Gems gesammelt!\n")
            break
        if not player['alive']:
            print(f"  💀 \033[91mDU WURDEST AUSGESCHALTET!\033[0m\n")
            break
        all_alive = [e for e in enemies if e['alive']]
        if not all_alive:
            print(f"  🏆 \033[94mALLE GEGNER BESIEGT!\033[0m Du gewinnst!\n")
            break

        # Spieler-Zug
        logs = player_turn(player, enemies, gems, dropped_gems, all_entities)

        # Gems fallen lassen wenn Spieler stirbt
        if not player['alive']:
            for _ in range(player['gems']):
                pr, pc = player['pos']
                dropped_gems.add((pr + random.randint(-1,1), pc + random.randint(-1,1)))
            player['gems'] = 0

        # KI-Züge
        ai_logs = []
        for e in enemies:
            ai_move(e, player, gems, all_entities, dropped_gems, ai_logs)
            # Gegner-Gems fallen lassen wenn besiegt
            if not e['alive'] and e['gems'] > 0:
                for _ in range(e['gems']):
                    er, ec = e['pos']
                    pos = (max(0,min(ROWS-1, er+random.randint(-1,1))),
                           max(0,min(COLS-1, ec+random.randint(-1,1))))
                    dropped_gems.add(pos)
                e['gems'] = 0

        clear()
        print(f"  ⚡ BRAWL TERMINAL  |  Runde {round_num}")
        draw_arena(all_entities, gems, dropped_gems)
        draw_hud(player, enemies, player['gems'], sum(e['gems'] for e in enemies))

        if logs:
            print("  📋 Deine Aktionen:")
            for l in logs:
                print(f"     → {l}")
        if ai_logs:
            print("  🤖 KI-Aktionen:")
            for l in ai_logs:
                print(f"     {l}")

        input("\n  [Enter] Nächste Runde...")

if __name__ == "__main__":
    main()
