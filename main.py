"""
   A E T H E R   H A R V E S T   v3.0           ║
║  Crystal mining · Wave defense · Prestige · Modes 

 WASD/Arrows  Move          Q / E / F  Abilities    ║
║  Space        Dash          RMB        Shoot bolt   ║
║  LMB          Harvest/Buy   S          Save         ║
║  Esc          Quit/Back                       
"""
import pygame, sys, math, random, os
sys.path.insert(0, os.path.dirname(__file__))

from utils.constants import (WIDTH, HEIGHT, FPS, TITLE,
                              C_BG, C_WHITE, C_PRIMARY, C_SECONDARY,
                              C_ACCENT, C_DANGER, C_SUCCESS, C_GRAY)
from utils.math_utils import format_number, lerp, smooth_step

from engine.camera    import Camera
from engine.input     import InputHandler
from engine.particles import ParticleSystem, FloatingTextManager
from engine.renderer  import draw_panel, draw_glow_rect, get_vignette

from entities.player  import Player
from entities.enemy   import EnemyManager
from entities.boss    import BossManager

from systems.resource_system import ResourceSystem, WORLD_W, WORLD_H
from systems.upgrade_system  import UpgradeSystem
from systems.combo           import ComboSystem
from systems.projectiles     import ProjectileSystem
from systems.xp              import XPSystem
from systems.abilities       import AbilitySystem

from ui.hud           import HUD, UpgradePanel
from ui.menu          import (MainMenu, ModeSelectScreen, DifficultyScreen,
                               AchievementsScreen, GameOverScreen)
from ui.warning_arrows import draw_warning_arrows
from ui.wave_timer     import WaveTimer

from world.world       import World
from core.save         import save_game, load_game
from core.difficulty   import DifficultyScaler
from core.game_modes   import MODES, DIFFICULTIES
from core.achievements  import AchievementSystem
from core.prestige      import PrestigeSystem
from core.highscores    import HighScoreSystem

# ── Init ──────────────────────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption(TITLE)
clock  = pygame.time.Clock()

def load_font(size, bold=False):
    for name in ("Segoe UI","Ubuntu","DejaVu Sans","Verdana","Arial"):
        try: return pygame.font.SysFont(name, size, bold=bold)
        except: pass
    return pygame.font.Font(None, size)

font_lg = load_font(36, bold=True)
font_md = load_font(24)
font_sm = load_font(18)
font_xs = load_font(13)

# ── Persistent systems (survive game resets) ──────────────────────────────────
achievements = AchievementSystem()
prestige_sys = PrestigeSystem()
highscores   = HighScoreSystem()
world_obj    = World()
inp          = InputHandler()

# ── Helpers ───────────────────────────────────────────────────────────────────
def draw_minimap(surf, player, ores, enemy_list, boss_mgr, cam):
    MM_W, MM_H = 150, 95
    MM_X = WIDTH - MM_W - 12
    MM_Y = HEIGHT - MM_H - 35
    mm   = pygame.Rect(MM_X, MM_Y, MM_W, MM_H)
    draw_panel(surf, mm, alpha=210, radius=6)
    sx, sy = MM_W/WORLD_W, MM_H/WORLD_H
    for ore in ores:
        pygame.draw.circle(surf, ore.color,
                           (MM_X+int(ore.x*sx), MM_Y+int(ore.y*sy)), 2)
    for e in enemy_list:
        if e.alive:
            pygame.draw.circle(surf, C_DANGER,
                               (MM_X+int(e.x*sx), MM_Y+int(e.y*sy)), 2)
    if boss_mgr.boss and boss_mgr.boss.alive:
        b = boss_mgr.boss
        pygame.draw.circle(surf, (255,100,255),
                           (MM_X+int(b.x*sx), MM_Y+int(b.y*sy)), 5)
    px = MM_X+int(player.x*sx); py = MM_Y+int(player.y*sy)
    pygame.draw.circle(surf, C_SECONDARY, (px,py), 4)
    pygame.draw.circle(surf, C_WHITE,     (px,py), 4, 1)
    vx1 = MM_X+int(cam.x*sx); vy1 = MM_Y+int(cam.y*sy)
    vx2 = MM_X+int((cam.x+WIDTH)*sx); vy2 = MM_Y+int((cam.y+HEIGHT)*sy)
    pygame.draw.rect(surf, C_GRAY, (vx1,vy1,vx2-vx1,vy2-vy1), 1)
    lbl = font_xs.render("MINIMAP", True, C_GRAY)
    surf.blit(lbl, (MM_X+4, MM_Y+2))

def draw_danger_badge(surf, difficulty):
    col = difficulty.danger_color
    txt = font_xs.render(f"◈ {difficulty.danger_label}  W{difficulty.wave}", True, col)
    rect = pygame.Rect(10, 108, txt.get_width()+16, 22)
    draw_panel(surf, rect, alpha=180, border=col, radius=6)
    surf.blit(txt, (rect.x+8, rect.y+4))

def draw_mode_badge(surf, mode_id, difficulty_id):
    m = MODES.get(mode_id, MODES["classic"])
    d = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normal"])
    txt = font_xs.render(f"{m['icon']} {m['name']}  ·  {d['icon']} {d['name']}", True, m["color"])
    rect = pygame.Rect(10, 134, txt.get_width()+16, 20)
    draw_panel(surf, rect, alpha=160, border=m["color"], radius=5)
    surf.blit(txt, (rect.x+8, rect.y+3))

def draw_timer(surf, time_left, mode_id):
    """Countdown timer for timed modes."""
    if time_left <= 0:
        return
    col = C_DANGER if time_left < 30 else (C_ACCENT if time_left < 60 else C_SUCCESS)
    mins = int(time_left//60); secs = int(time_left%60)
    txt  = font_md.render(f"⏱  {mins}:{secs:02d}", True, col)
    rect = pygame.Rect(WIDTH//2 - txt.get_width()//2 - 12, 6,
                       txt.get_width()+24, 36)
    draw_panel(surf, rect, alpha=200, border=col, radius=8)
    surf.blit(txt, (rect.x+12, rect.y+6))
    if time_left < 10:
        # Pulse overlay
        a = int(abs(math.sin(pygame.time.get_ticks()*0.006))*80)
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((*C_DANGER, a))
        surf.blit(ov, (0,0))

# ── Session factory ───────────────────────────────────────────────────────────
def build_session(mode_id="classic", difficulty_id="normal", load_save=False):
    mode  = MODES[mode_id]
    diff  = DIFFICULTIES[difficulty_id]

    upgrades   = UpgradeSystem()
    resources  = 0.0
    saved_wave = 0
    xp_data    = None
    s_mode     = mode_id
    s_diff     = difficulty_id

    if load_save:
        resources, saved_wave, s_mode, s_diff, xp_data = load_game(upgrades)
        mode_id, difficulty_id = s_mode, s_diff
        mode = MODES.get(mode_id, MODES["classic"])
        diff = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normal"])

    # Void Siege: no upgrades
    if "no_upgrades" in mode["modifiers"]:
        upgrades = UpgradeSystem()   # fresh, can't buy

    # Prestige mode: max upgrades
    if "all_maxed" in mode["modifiers"]:
        for u in upgrades.levels:
            from utils.constants import UPGRADES
            for ug in UPGRADES:
                if ug["id"] == u:
                    upgrades.levels[u] = ug["max_level"]

    player = Player(WORLD_W//2, WORLD_H//2)
    player.collect_range_bonus = upgrades.collect_range_bonus
    player.speed_mult    = upgrades.speed_mult
    player.vacuum_radius = upgrades.vacuum_radius

    # Apply difficulty to player
    player.max_hp = int(100 * (2.0 - diff["enemy_hp"]) + 20)
    player.hp     = player.max_hp

    enemies             = EnemyManager()
    enemies.wave        = saved_wave
    enemies.spawn_interval = mode["wave_interval"]

    boss_mgr    = BossManager()
    res_sys     = ResourceSystem()
    combo       = ComboSystem()
    difficulty  = DifficultyScaler()
    difficulty.wave = saved_wave

    xp_sys      = XPSystem()
    if xp_data:
        for k, v in xp_data.items():
            if hasattr(xp_sys, k):
                setattr(xp_sys, k, v)

    abilities   = AbilitySystem()
    projectiles = ProjectileSystem()
    particles   = ParticleSystem()
    floats      = FloatingTextManager()

    camera = Camera(WIDTH, HEIGHT, WORLD_W, WORLD_H)
    camera.x = player.x - WIDTH//2
    camera.y = player.y - HEIGHT//2

    hud       = HUD(font_lg, font_md, font_sm, font_xs)
    up_panel  = UpgradePanel(font_md, font_sm, font_xs)
    wave_timer= WaveTimer(font_md, font_sm, font_xs)

    # Apply prestige bonuses
    prestige_sys.apply_to_session(player, upgrades)

    # Time limit for timed modes
    time_left = float(mode["time_limit"]) if mode["time_limit"] > 0 else 0.0

    # Ore value multiplier
    ore_mult  = mode["ore_value_mult"] * diff.get("ore_mult", 1.0) * prestige_sys.ore_mult

    return dict(
        mode_id=mode_id, difficulty_id=difficulty_id,
        mode=mode, diff=diff,
        upgrades=upgrades, resources=resources,
        player=player, enemies=enemies, boss_mgr=boss_mgr,
        res_sys=res_sys, combo=combo, difficulty=difficulty,
        xp_sys=xp_sys, abilities=abilities, projectiles=projectiles,
        particles=particles, floats=floats,
        camera=camera, hud=hud, up_panel=up_panel, wave_timer=wave_timer,
        time_left=time_left, ore_mult=ore_mult,
        no_upgrades=("no_upgrades" in mode["modifiers"]),
        no_enemies=("no_enemies"  in mode["modifiers"]),
        nodmg_wave=True,   # track no-damage achievement
    )

# ── State machine ─────────────────────────────────────────────────────────────
STATE_MAIN      = "main"
STATE_MODE_SEL  = "mode_sel"
STATE_DIFF_SEL  = "diff_sel"
STATE_PLAYING   = "playing"
STATE_GAMEOVER  = "gameover"
STATE_ACH       = "achievements"

state          = STATE_MAIN
session        = None
go_screen      = None
pending_mode   = None
total_time     = 0.0
time_slow      = False
time_slow_timer= 0.0
TIME_SLOW_DUR  = 3.0
save_flash     = 0.0
ambient_timer  = 0.0

# Build screens
has_save = os.path.exists("data/save.json")
main_menu   = MainMenu(font_lg, font_md, font_sm, font_xs,
                        has_save=has_save,
                        achievements=achievements,
                        highscores=highscores,
                        prestige=prestige_sys)
mode_screen  = None
diff_screen  = None
ach_screen   = None

def on_time_slow():
    global time_slow, time_slow_timer
    if session and session["upgrades"].has_time_slow:
        time_slow = True; time_slow_timer = TIME_SLOW_DUR

def sync_player_upgrades(s):
    p, u = s["player"], s["upgrades"]
    p.collect_range_bonus = u.collect_range_bonus
    p.speed_mult          = u.speed_mult
    p.vacuum_radius       = u.vacuum_radius

def apply_mode_enemy_scale(enemy, diff_cfg):
    enemy.hp     = int(enemy.hp     * diff_cfg["enemy_hp"])
    enemy.max_hp = enemy.hp
    enemy.dmg    = int(enemy.dmg    * diff_cfg["enemy_dmg"])
    enemy.speed  = enemy.speed * diff_cfg["enemy_speed"]

# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
running = True
while running:
    raw_dt = min(clock.tick(FPS)/1000.0, 0.05)

    events = pygame.event.get()
    inp.process_events(events)

    # ── EVENT ROUTING ─────────────────────────────────────────────────────────
    for event in events:
        if event.type == pygame.QUIT:
            running = False

        # ── Main menu ─────────────────────────────────────────────────────────
        if state == STATE_MAIN:
            main_menu.handle_event(event)
            if main_menu.done:
                if main_menu.to_achievements:
                    ach_screen = AchievementsScreen(
                        font_lg,font_md,font_sm,font_xs, achievements)
                    state = STATE_ACH
                    main_menu.done = False
                elif main_menu.to_mode_select:
                    mode_screen = ModeSelectScreen(
                        font_lg,font_md,font_sm,font_xs,
                        prestige=prestige_sys, highscores=highscores)
                    state = STATE_MODE_SEL
                    main_menu.done = False

        # ── Mode select ───────────────────────────────────────────────────────
        elif state == STATE_MODE_SEL:
            mode_screen.handle_event(event)
            if mode_screen.done:
                if mode_screen.back:
                    state = STATE_MAIN
                    mode_screen = None
                elif mode_screen.selected_mode:
                    pending_mode = mode_screen.selected_mode
                    diff_screen  = DifficultyScreen(
                        font_lg,font_md,font_sm,font_xs, pending_mode)
                    state = STATE_DIFF_SEL
                    mode_screen = None

        # ── Difficulty select ─────────────────────────────────────────────────
        elif state == STATE_DIFF_SEL:
            diff_screen.handle_event(event)
            if diff_screen.done:
                if diff_screen.back:
                    mode_screen = ModeSelectScreen(
                        font_lg,font_md,font_sm,font_xs,
                        prestige=prestige_sys, highscores=highscores)
                    state = STATE_MODE_SEL
                    diff_screen = None
                elif diff_screen.selected:
                    session    = build_session(pending_mode, diff_screen.selected,
                                               load_save=False)
                    total_time = 0.0; time_slow = False
                    state      = STATE_PLAYING
                    diff_screen= None

        # ── Achievements ──────────────────────────────────────────────────────
        elif state == STATE_ACH:
            ach_screen.handle_event(event)
            if ach_screen.done:
                state = STATE_MAIN
                ach_screen = None
                main_menu  = MainMenu(font_lg,font_md,font_sm,font_xs,
                                      has_save=os.path.exists("data/save.json"),
                                      achievements=achievements,
                                      highscores=highscores,
                                      prestige=prestige_sys)

        # ── Game over ─────────────────────────────────────────────────────────
        elif state == STATE_GAMEOVER and go_screen:
            go_screen.handle_event(event)
            if go_screen.restart:
                session    = build_session(
                    go_screen.mode_id, go_screen.difficulty_id)
                total_time = 0.0; time_slow = False
                state      = STATE_PLAYING
                go_screen  = None
            elif go_screen.prestige:
                kept = prestige_sys.do_prestige(go_screen.resources)
                session = build_session(go_screen.mode_id, go_screen.difficulty_id)
                session["resources"] = kept
                total_time = 0.0; time_slow = False
                state      = STATE_PLAYING
                go_screen  = None
            elif go_screen.quit:
                main_menu = MainMenu(font_lg,font_md,font_sm,font_xs,
                                     has_save=os.path.exists("data/save.json"),
                                     achievements=achievements,
                                     highscores=highscores,
                                     prestige=prestige_sys)
                state = STATE_MAIN
                go_screen = None

        # ── Playing ───────────────────────────────────────────────────────────
        elif state == STATE_PLAYING and session:
            s = session

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    save_game(s["resources"], s["upgrades"], s["enemies"].wave,
                              s["xp_sys"], s["mode_id"], s["difficulty_id"])
                    running = False
                if event.key == pygame.K_s:
                    save_game(s["resources"], s["upgrades"], s["enemies"].wave,
                              s["xp_sys"], s["mode_id"], s["difficulty_id"])
                    save_flash = 2.0
                # Abilities Q / E / F
                for ai, key in enumerate([pygame.K_q, pygame.K_e, pygame.K_f]):
                    if event.key == key:
                        gained = s["abilities"].fire(
                            ai, s["player"], s["enemies"], s["boss_mgr"],
                            s["res_sys"], s["particles"], s["floats"],
                            font_sm, s["camera"])
                        if gained:
                            s["resources"] += int(gained * s["ore_mult"])
                            s["camera"].shake(12, 0.3)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mp = inp.mouse_pos
                if not s["no_upgrades"] and s["up_panel"].panel_rect.collidepoint(mp):
                    s["resources"] = s["up_panel"].handle_click(
                        mp, s["resources"], s["upgrades"])
                    sync_player_upgrades(s)
                    achievements.update_stat("upgrades_bought", 1)
                    # Check maxed
                    from utils.constants import UPGRADES as UG_LIST
                    maxed = sum(1 for u in UG_LIST if s["upgrades"].maxed(u["id"]))
                    achievements.update_stat("upgrades_maxed", maxed, "max")
                    unique = sum(1 for u in UG_LIST if s["upgrades"].level(u["id"]) > 0)
                    achievements.update_stat("unique_upgrades", unique, "max")
                else:
                    wx, wy = s["camera"].screen_to_world(*mp)
                    gained = s["res_sys"].try_collect(
                        wx, wy, s["player"], s["particles"], s["floats"],
                        font_sm,
                        click_power  = s["upgrades"].click_power,
                        rare_boost   = s["upgrades"].rare_boost,
                        chain_chance = s["upgrades"].chain_chance,
                        time_slow_cb = on_time_slow,
                        cam          = s["camera"])
                    if gained:
                        mult  = s["combo"].register_collect()
                        total = int(gained * mult * s["ore_mult"] *
                                    s["xp_sys"].income_mult)
                        s["resources"] += total
                        s["camera"].shake(3, 0.07)
                        achievements.update_stat("crystals_collected", 1)
                        achievements.update_stat("total_resources", total)
                        if mult >= 8.0:
                            achievements.update_stat("max_combo", 8, "max")

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                wx, wy = s["camera"].screen_to_world(*inp.mouse_pos)
                if s["projectiles"].shoot(s["player"].x, s["player"].y,
                                          wx, wy, s["upgrades"].bolt_level):
                    s["particles"].emit(s["player"].x, s["player"].y,
                        (wx-s["player"].x)*0.3, (wy-s["player"].y)*0.3,
                        life=0.2, color=(180,100,255), size=3, glow=True)

    # ── SCREEN RENDERS ────────────────────────────────────────────────────────
    if state == STATE_MAIN:
        main_menu.update(raw_dt)
        screen.fill(C_BG)
        main_menu.draw(screen)
        pygame.display.flip(); continue

    if state == STATE_MODE_SEL and mode_screen:
        mode_screen.update(raw_dt)
        screen.fill(C_BG)
        mode_screen.draw(screen)
        pygame.display.flip(); continue

    if state == STATE_DIFF_SEL and diff_screen:
        diff_screen.update(raw_dt)
        screen.fill(C_BG)
        diff_screen.draw(screen)
        pygame.display.flip(); continue

    if state == STATE_ACH and ach_screen:
        ach_screen.update(raw_dt)
        screen.fill(C_BG)
        ach_screen.draw(screen)
        pygame.display.flip(); continue

    if state == STATE_GAMEOVER and go_screen:
        go_screen.update(raw_dt)
        screen.fill(C_BG)
        go_screen.draw(screen)
        pygame.display.flip(); continue

    if state != STATE_PLAYING or session is None:
        pygame.display.flip(); continue

    # ── PLAYING UPDATE ────────────────────────────────────────────────────────
    s  = session
    dt = raw_dt * (0.3 if time_slow else 1.0)

    total_time      += raw_dt
    save_flash       = max(0, save_flash - raw_dt)
    time_slow_timer  = max(0, time_slow_timer - raw_dt)
    if time_slow_timer <= 0: time_slow = False
    ambient_timer   -= dt

    # Timed mode countdown
    if s["time_left"] > 0:
        s["time_left"] = max(0, s["time_left"] - raw_dt)
        if s["time_left"] <= 0:
            # Time's up — submit score and go to game over
            is_rec = highscores.is_new_record(s["mode_id"], s["resources"])
            rank   = highscores.submit(s["mode_id"], s["difficulty_id"],
                                       s["resources"], s["enemies"].wave, total_time)
            if s["mode_id"] == "blitz":
                achievements.update_stat("blitz_wins", 1)
            if s["mode_id"] == "crystal_rush":
                achievements.update_stat("rush_best", int(s["resources"]), "max")
            go_screen = GameOverScreen(
                font_lg,font_md,font_sm,font_xs,
                s["resources"], s["enemies"].wave, total_time,
                s["mode_id"], s["difficulty_id"], rank, is_rec,
                prestige_sys.can_prestige(s["enemies"].wave))
            state = STATE_GAMEOVER
            continue

    # Autofire RMB
    if inp.mouse_buttons[2]:
        wx, wy = s["camera"].screen_to_world(*inp.mouse_pos)
        if s["projectiles"].shoot(s["player"].x, s["player"].y,
                                   wx, wy, s["upgrades"].bolt_level):
            s["particles"].emit(s["player"].x, s["player"].y,
                (wx-s["player"].x)*0.3, (wy-s["player"].y)*0.3,
                life=0.15, color=(180,100,255), size=2, glow=True)

    # Player update
    s["player"].update(dt, inp, WORLD_W, WORLD_H)

    # Death check
    if s["player"].hp <= 0:
        save_game(s["resources"], s["upgrades"], s["enemies"].wave,
                  s["xp_sys"], s["mode_id"], s["difficulty_id"])
        s["particles"].burst(s["player"].x, s["player"].y,
                             C_SECONDARY, count=50, speed=200, life=1.5)
        s["camera"].shake(20, 0.8)
        is_rec = highscores.is_new_record(s["mode_id"], s["resources"])
        rank   = highscores.submit(s["mode_id"], s["difficulty_id"],
                                    s["resources"], s["enemies"].wave, total_time)
        achievements.update_stat("max_wave", s["enemies"].wave, "max")
        go_screen = GameOverScreen(
            font_lg,font_md,font_sm,font_xs,
            s["resources"], s["enemies"].wave, total_time,
            s["mode_id"], s["difficulty_id"], rank, is_rec,
            prestige_sys.can_prestige(s["enemies"].wave))
        state = STATE_GAMEOVER; continue

    # Camera
    s["camera"].follow(s["player"].x, s["player"].y, raw_dt, speed=5.0)
    s["camera"].update(raw_dt)

    # Ore tick
    s["res_sys"].rare_boost = s["upgrades"].rare_boost
    for ore in s["res_sys"].ores:
        ore.update(dt)

    # Income
    s["resources"] += s["res_sys"].auto_collect(
        dt, s["player"], s["upgrades"].auto_income * prestige_sys.auto_mult)

    # HP regen
    if s["upgrades"].hp_regen > 0:
        s["player"].heal(s["upgrades"].hp_regen * dt)

    # Vacuum (Aether Lens)
    vac = s["res_sys"].vacuum_collect(
        s["player"], s["particles"], s["floats"],
        font_sm, s["upgrades"].click_power)
    if vac:
        s["resources"] += int(vac * s["ore_mult"])
        achievements.update_stat("crystals_collected", 1)

    # Projectiles
    s["projectiles"].try_shoot(s["player"].x, s["player"].y, 0, 0,
                                dt, s["upgrades"].bolt_level)
    s["projectiles"].update(dt, s["enemies"].enemies, s["boss_mgr"], s["particles"])

    # Abilities
    s["abilities"].update(dt)

    # Enemies (skip if no_enemies mode)
    if not s["no_enemies"]:
        diff_cfg = s["diff"]
        prev_wave = s["enemies"].wave
        s["enemies"].spawn_timer  -= dt
        if s["enemies"].spawn_timer <= 0:
            s["enemies"]._spawn_wave(s["player"].x, s["player"].y)
            s["enemies"].spawn_timer   = s["enemies"].spawn_interval
            s["enemies"].spawn_interval= max(8.0, s["enemies"].spawn_interval - 0.4)

        killed = []
        for enemy in s["enemies"].enemies:
            if not enemy.alive:
                killed.append(enemy); continue
            enemy.update(dt, s["player"].x, s["player"].y)
            from utils.math_utils import dist
            if dist(enemy.x, enemy.y, s["player"].x, s["player"].y) \
                    < enemy.size + s["player"].RADIUS:
                if s["player"].take_damage(
                        int(enemy.dmg * diff_cfg["enemy_dmg"])):
                    s["particles"].burst(s["player"].x, s["player"].y,
                                         (255,80,80), count=10)
                    s["nodmg_wave"] = False
                enemy.alive = False; killed.append(enemy)
        for e in killed:
            if e in s["enemies"].enemies:
                s["enemies"].enemies.remove(e)
                if not e.alive and e.hp <= 0:
                    reward = e.reward
                    xp = s["xp_sys"].register_kill(reward)
                    s["resources"] += int(reward * s["xp_sys"].income_mult)
                    s["particles"].burst(e.x, e.y, e.color, count=15, speed=150)
                    s["floats"].add(e.x, e.y-20, f"+{reward}✦", font_sm, (255,220,80))
                    s["floats"].add(e.x, e.y-38, f"+{xp}xp", font_sm, C_ACCENT,
                                    speed=-55, life=0.9)
                    achievements.update_stat("kills", 1)

        if s["enemies"].wave != prev_wave:
            nw = s["enemies"].wave
            s["hud"].announce_wave(nw)
            s["camera"].shake(10, 0.3)
            s["difficulty"].wave = nw
            achievements.update_stat("max_wave", nw, "max")
            if s.get("nodmg_wave") and nw >= 3:
                achievements.update_stat("nodmg_wave3", 1)
            if s["boss_mgr"].check_spawn(nw, s["player"].x, s["player"].y):
                s["camera"].shake(15, 0.5)

        # Boss
        boss_reward = s["boss_mgr"].update(
            dt, s["player"], s["particles"], s["floats"], font_md)
        if boss_reward:
            bxp = s["xp_sys"].register_kill(boss_reward, is_boss=True)
            s["resources"] += int(boss_reward * s["xp_sys"].income_mult)
            s["camera"].shake(20, 0.6)
            s["floats"].add(s["player"].x, s["player"].y-60,
                            f"+{bxp} XP", font_sm, C_ACCENT, speed=-50, life=1.5)
            achievements.update_stat("bosses_killed", 1)

    # Combo / difficulty / XP / achievements
    s["combo"].update(dt)
    s["difficulty"].tick(dt, s["enemies"].wave)
    s["xp_sys"].update(dt)
    s["xp_sys"].apply_to_player(s["player"])
    achievements.update_stat("player_level", s["xp_sys"].level, "max")
    achievements.update_stat("total_resources", 0)   # trigger check

    # Particles
    s["particles"].update(dt)
    s["floats"].update(dt)
    achievements.update(dt)

    # Ambient ore sparkles
    if ambient_timer <= 0:
        ambient_timer = 0.07
        for ore in random.sample(s["res_sys"].ores,
                                 min(3, len(s["res_sys"].ores))):
            s["particles"].emit(
                ore.x + random.uniform(-ore.radius, ore.radius),
                ore.y + random.uniform(-ore.radius, ore.radius),
                random.uniform(-15,15), random.uniform(-45,-10),
                life=random.uniform(0.3,0.7),
                color=ore.glow, end_color=(20,10,40),
                size=random.uniform(1,3), glow=True)

    if s["player"].dashing:
        s["particles"].trail(s["player"].x, s["player"].y, C_SECONDARY,
                             vx=s["player"].vx, vy=s["player"].vy)

    s["hud"].update(raw_dt, s["resources"], time_slow)
    s["up_panel"].update(raw_dt, inp.mouse_pos, s["upgrades"])

    # ── DRAW ──────────────────────────────────────────────────────────────────
    cam = s["camera"]
    screen.fill(C_BG)

    world_obj.draw(screen, cam)
    s["res_sys"].draw(screen, cam)
    s["particles"].draw(screen, cam.dx, cam.dy)
    if not s["no_enemies"]:
        s["enemies"].draw(screen, cam)
        s["boss_mgr"].draw(screen, cam)
    s["player"].draw(screen, cam)
    s["projectiles"].draw(screen, cam)
    s["floats"].draw(screen, cam.dx, cam.dy)

    screen.blit(get_vignette(WIDTH, HEIGHT), (0,0))

    # Time-slow overlay
    if time_slow:
        alpha = int(50*(time_slow_timer/TIME_SLOW_DUR))
        ov = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
        ov.fill((60,20,120,alpha))
        screen.blit(ov, (0,0))
        ts = font_sm.render("◈  TEMPORAL SURGE  ◈", True, (200,150,255))
        screen.blit(ts, (WIDTH//2 - ts.get_width()//2, 18))

    s["hud"].draw(screen, s["player"], s["upgrades"], s["enemies"].wave, time_slow)
    if not s["no_upgrades"]:
        s["up_panel"].draw(screen, s["resources"], s["upgrades"])
    s["combo"].draw(screen, font_md, font_xs)
    s["xp_sys"].draw(screen, font_lg, font_md, font_xs)
    s["abilities"].draw_hud(screen, font_sm, font_xs)
    s["wave_timer"].draw(screen, s["enemies"], s["boss_mgr"])

    draw_minimap(screen, s["player"], s["res_sys"].ores,
                 s["enemies"].enemies, s["boss_mgr"], cam)
    draw_danger_badge(screen, s["difficulty"])
    draw_mode_badge(screen, s["mode_id"], s["difficulty_id"])

    if not s["no_enemies"]:
        draw_warning_arrows(screen, s["player"], s["enemies"].enemies,
                            s["boss_mgr"], cam, font_xs)
        s["boss_mgr"].draw_intro(screen, font_lg, font_md)

    if s["time_left"] > 0:
        draw_timer(screen, s["time_left"], s["mode_id"])

    achievements.draw(screen, font_md, font_sm, font_xs)

    if save_flash > 0:
        a   = int(255 * smooth_step(min(save_flash,1.0)))
        msg = font_sm.render("✓  Game Saved", True, C_SUCCESS)
        msg.set_alpha(a)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT-60))

    screen.blit(font_xs.render(f"{int(clock.get_fps())} fps", True, C_GRAY), (8,HEIGHT-18))
    pygame.display.flip()

# ── Cleanup ───────────────────────────────────────────────────────────────────
if session:
    save_game(session["resources"], session["upgrades"],
              session["enemies"].wave, session["xp_sys"],
              session["mode_id"], session["difficulty_id"])
achievements.save()
pygame.quit()
sys.exit()

