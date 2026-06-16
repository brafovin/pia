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
        "name": "Shelly",   "emoji": "🔫", "hp": 5200, "dmg": 800,
        "super_name": "Schild-Wand",
        "range": 5,
        "desc": "Normaler Schuss. Super: Baut eine temporäre Mauer auf einem Feld (3 Runden)",
        "super_type": "wall",
    },
    {
        "name": "Colt",     "emoji": "🤠", "hp": 3600, "dmg": 650,
        "super_name": "Teleport-Schuss",
        "range": 7,
        "desc": "Präziser Schuss. Super: Teleportiert zu einem Zielfeld und schießt sofort",
        "super_type": "teleport",
    },
    {
        "name": "Bull",     "emoji": "🐂", "hp": 6500, "dmg": 1600,
        "super_name": "Berserker",
        "range": 2,
        "desc": "Nahkampf-Tank. Super: Verdoppelt Schaden für 3 Runden, kann nicht betäubt werden",
        "super_type": "berserk",
    },
    {
        "name": "Poco",     "emoji": "🎸", "hp": 4000, "dmg": 500,
        "super_name": "Gem-Diebstahl",
        "range": 5,
        "desc": "Schwacher Schuss. Super: Stiehlt 3 Gems vom nächsten Gegner",
        "super_type": "steal",
    },
    {
        "name": "Brock",    "emoji": "🚀", "hp": 3000, "dmg": 950,
        "super_name": "Zeitbombe",
        "range": 9,
        "desc": "Sniper. Super: Legt Bombe auf Feld — explodiert nächste Runde für 4000 Schaden (Radius 1)",
        "super_type": "bomb",
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

_temp_walls_ref = {}

def is_wall(r, c):
    return (r, c) in WALLS or (r, c) in _temp_walls_ref

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
    e['berserk_turns'] = 0   # Bull Super
    return e

def draw_arena(entities, gems, dropped_gems, temp_walls=None, bombs=None):
    temp_walls = temp_walls or {}
    bombs = bombs or []
    grid = [["  " for _ in range(COLS)] for _ in range(ROWS)]

    for (wr, wc) in WALLS:
        grid[wr][wc] = "██"
    for (wr, wc) in temp_walls:
        grid[wr][wc] = "🧱"
    for b in bombs:
        br, bc = b['pos']
        if in_bounds(br, bc):
            grid[br][bc] = "💣"

    for (gr, gc) in gems:
        grid[gr][gc] = "💎"
    for (gr, gc) in dropped_gems:
        grid[gr][gc] = "✨"

    for e in entities:
        if e['alive']:
            r, c = e['pos']
            color = "\033[94m" if e['team'] == 'blue' else "\033[91m"
            icon = e['emoji']
            if e.get('berserk_turns', 0) > 0:
                icon = "🔥"
            grid[r][c] = color + icon + "\033[0m"

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
    if shooter.get('berserk_turns', 0) > 0:
        dmg *= 2
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

def ask_target(prompt="  Zielfeld (Reihe Spalte): "):
    while True:
        raw = input(prompt).strip().split()
        try:
            return int(raw[0])-1, int(raw[1])-1
        except:
            print("  Ungültig! Format: Reihe Spalte (z.B. 3 5)")

def use_super(player, all_entities, enemies, gems, temp_walls, bombs):
    sname = player['super_name']
    stype = player.get('super_type', '')
    log = []

    # ── Shelly: Schild-Wand ──────────────────────────────────────────
    if stype == "wall":
        print(f"\n  🧱 SUPER: {sname}! Wo soll die Mauer erscheinen? (leeres Feld)")
        while True:
            tr, tc = ask_target()
            if not in_bounds(tr, tc):
                print("  Außerhalb der Arena!")
                continue
            if is_wall(tr, tc) or (tr, tc) in temp_walls:
                print("  Dort ist schon eine Mauer!")
                continue
            occupied = any(e['alive'] and e['pos']==[tr,tc] for e in all_entities)
            if occupied:
                print("  Ein Brawler steht dort!")
                continue
            break
        temp_walls[(tr, tc)] = 3
        log.append(f"🧱 Mauer bei {tr+1},{tc+1} errichtet! (3 Runden)")

    # ── Colt: Teleport-Schuss ────────────────────────────────────────
    elif stype == "teleport":
        print(f"\n  ⚡ SUPER: {sname}! Wohin teleportieren? (leeres Feld)")
        while True:
            tr, tc = ask_target()
            if not in_bounds(tr, tc):
                print("  Außerhalb!")
                continue
            if is_wall(tr, tc) or (tr, tc) in temp_walls:
                print("  Blockiert!")
                continue
            occupied = any(e['alive'] and e['pos']==[tr,tc] for e in all_entities)
            if occupied:
                print("  Besetzt!")
                continue
            break
        player['pos'] = [tr, tc]
        log.append(f"⚡ Teleportiert nach {tr+1},{tc+1}!")
        print(f"  Jetzt schießen! Zielfeld:")
        sr, sc = ask_target()
        hit, msg = shoot(player, [sr, sc], all_entities, range_override=COLS)
        log.append(f"🔫 Sofortschuss → {msg}")

    # ── Bull: Berserker ──────────────────────────────────────────────
    elif stype == "berserk":
        player['berserk_turns'] = 3
        log.append(f"🐂 BERSERKER! Doppelschaden für 3 Runden! Unaufhaltbar!")

    # ── Poco: Gem-Diebstahl ──────────────────────────────────────────
    elif stype == "steal":
        alive_enemies = [e for e in enemies if e['alive'] and e['gems'] > 0]
        if not alive_enemies:
            log.append(f"🎸 Kein Gegner hat Gems zum Stehlen!")
        else:
            target = min(alive_enemies, key=lambda e: dist(player['pos'], e['pos']))
            stolen = min(3, target['gems'])
            target['gems'] -= stolen
            player['gems'] += stolen
            log.append(f"🎸 {stolen} Gems von {target['name']} gestohlen! 💎×{stolen}")

    # ── Brock: Zeitbombe ─────────────────────────────────────────────
    elif stype == "bomb":
        print(f"\n  💣 SUPER: {sname}! Wo soll die Bombe landen?")
        tr, tc = ask_target()
        if in_bounds(tr, tc):
            bombs.append({'pos': [tr, tc], 'timer': 1, 'dmg': 4000, 'radius': 1})
            log.append(f"💣 Bombe bei {tr+1},{tc+1} platziert! Explodiert nächste Runde!")
        else:
            log.append("Ziel außerhalb!")

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

def player_turn(player, enemies, gems, dropped_gems, all_entities, temp_walls, bombs):
    log_lines = []
    berserk_str = f"  🔥 BERSERKER noch {player['berserk_turns']} Runden!" if player.get('berserk_turns',0)>0 else ""
    print("\n  STEUERUNG:")
    print("  [w/a/s/d] Bewegen  [f Reihe Spalte] Schießen  [q] Super  [skip] Aussetzen")
    print(f"  Ammo: {'🔵'*player['ammo']}{'⚫'*(MAX_AMMO-player['ammo'])}  |  Pos: {player['pos'][0]+1},{player['pos'][1]+1}{berserk_str}")

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
            msgs = use_super(player, all_entities, enemies, gems, temp_walls, bombs)
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
    temp_walls = {}   # (r,c) -> turns_remaining
    bombs = []        # [{'pos':[], 'timer':int, 'dmg':int, 'radius':int}]
    spawn_gems(gems, 3)

    # Globale temp_walls Referenz für is_wall()
    global _temp_walls_ref
    _temp_walls_ref = temp_walls

    round_num = 0

    while True:
        round_num += 1

        if round_num % 3 == 0:
            spawn_gems(gems, 1)

        # Temp-Wände herunter zählen
        expired = [k for k, v in temp_walls.items() if v <= 0]
        for k in expired:
            del temp_walls[k]
        for k in temp_walls:
            temp_walls[k] -= 1

        # Bomben zünden
        bomb_logs = []
        for b in list(bombs):
            b['timer'] -= 1
            if b['timer'] <= 0:
                br, bc = b['pos']
                bomb_logs.append(f"💥 EXPLOSION bei {br+1},{bc+1}!")
                for e in all_entities:
                    if not e['alive']:
                        continue
                    if dist(e['pos'], b['pos']) <= b['radius']:
                        e['hp'] -= b['dmg']
                        bomb_logs.append(f"   {e['name']} trifft für {b['dmg']}!")
                        if e['hp'] <= 0:
                            e['alive'] = False
                            bomb_logs.append(f"   💀 {e['name']} ausgeschaltet!")
                bombs.remove(b)

        # Berserk runterzählen
        if player.get('berserk_turns', 0) > 0:
            player['berserk_turns'] -= 1

        blue_gems = player['gems']
        red_gems = sum(e['gems'] for e in enemies)

        clear()
        print(f"  ⚡ BRAWL TERMINAL  |  Runde {round_num}  |  Gem Grab: Erst zu {GEM_WIN} 💎 gewinnt!")
        draw_arena(all_entities, gems, dropped_gems, temp_walls, bombs)
        draw_hud(player, enemies, blue_gems, red_gems)

        if bomb_logs:
            for l in bomb_logs:
                print(f"  {l}")
            input("  [Enter]...")

        if blue_gems >= GEM_WIN:
            print(f"  🏆 \033[94mDU GEWINNST!\033[0m {player['name']} hat {blue_gems} Gems gesammelt!\n")
            break
        if red_gems >= GEM_WIN:
            print(f"  💀 \033[91mROT GEWINNT!\033[0m Die Gegner haben {red_gems} Gems gesammelt!\n")
            break
        if not player['alive']:
            print(f"  💀 \033[91mDU WURDEST AUSGESCHALTET!\033[0m\n")
            break
        if not any(e['alive'] for e in enemies):
            print(f"  🏆 \033[94mALLE GEGNER BESIEGT!\033[0m Du gewinnst!\n")
            break

        logs = player_turn(player, enemies, gems, dropped_gems, all_entities, temp_walls, bombs)

        if not player['alive']:
            for _ in range(player['gems']):
                pr, pc = player['pos']
                dropped_gems.add((max(0,min(ROWS-1,pr+random.randint(-1,1))),
                                  max(0,min(COLS-1,pc+random.randint(-1,1)))))
            player['gems'] = 0

        ai_logs = []
        for e in enemies:
            ai_move(e, player, gems, all_entities, dropped_gems, ai_logs)
            if not e['alive'] and e['gems'] > 0:
                for _ in range(e['gems']):
                    er, ec = e['pos']
                    dropped_gems.add((max(0,min(ROWS-1,er+random.randint(-1,1))),
                                      max(0,min(COLS-1,ec+random.randint(-1,1)))))
                e['gems'] = 0

        clear()
        print(f"  ⚡ BRAWL TERMINAL  |  Runde {round_num}")
        draw_arena(all_entities, gems, dropped_gems, temp_walls, bombs)
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
