
import pygame, sys, math, random, os
sys.path.insert(0, os.path.dirname(__file__))

from utils.constants import (WIDTH, HEIGHT, FPS, TITLE,
                              C_BG, C_WHITE, C_PRIMARY, C_SECONDARY,
                              C_ACCENT, C_DANGER, C_SUCCESS, C_GRAY)
from utils.math_utils import format_number, lerp, smooth_step, dist

from engine.camera    import Camera
from engine.input     import InputHandler
from engine.particles import ParticleSystem, FloatingTextManager
from engine.renderer  import draw_panel, draw_glow_rect, get_vignette

from entities.player  import Player
from entities.enemy   import EnemyManager, Enemy
from entities.boss    import BossManager

from systems.resource_system import ResourceSystem, WORLD_W, WORLD_H
from systems.upgrade_system  import UpgradeSystem
from systems.combo           import ComboSystem
from systems.xp              import XPSystem
from systems.abilities       import AbilitySystem
from systems.loot            import LootSystem
from systems.weapons         import WeaponSystem

from ui.hud           import HUD, UpgradePanel
from ui.menu          import (MainMenu, ModeSelectScreen, DifficultyScreen,
                               AchievementsScreen, GameOverScreen)
from ui.warning_arrows import draw_warning_arrows
from ui.howtoplay     import HowToPlayScreen
from ui.layout        import (MM_X, MM_Y, MM_W, MM_H, PANEL_X, BADGE_Y,
                               MODE_Y, LX, FPS_Y, LOOT_X, LOOT_Y)
from ui.wave_timer     import WaveTimer

from world.world       import World
from world.events      import EventSystem
from world.weather     import WeatherSystem

from core.save         import save_game, load_game
from core.difficulty   import DifficultyScaler
from core.game_modes   import MODES, DIFFICULTIES
from core.achievements  import AchievementSystem
from core.prestige      import PrestigeSystem
from core.highscores    import HighScoreSystem

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption(TITLE)
clock  = pygame.time.Clock()

def load_font(size, bold=False):
    for n in ("Segoe UI","Ubuntu","DejaVu Sans","Verdana","Arial"):
        try: return pygame.font.SysFont(n, size, bold=bold)
        except: pass
    return pygame.font.Font(None, size)

font_lg = load_font(36, bold=True)
font_md = load_font(24)
font_sm = load_font(18)
font_xs = load_font(13)

achievements = AchievementSystem()
prestige_sys = PrestigeSystem()
highscores   = HighScoreSystem()
world_obj    = World()
inp          = InputHandler()

def draw_minimap(surf, player, ores, enemy_list, boss_mgr, cam):
    from ui.layout import MM_X, MM_Y, MM_W, MM_H
    mm   = pygame.Rect(MM_X, MM_Y, MM_W, MM_H)
    draw_panel(surf, mm, color=(10,8,24), border=(40,30,80), alpha=220, radius=6)
    sx_s = MM_W / WORLD_W; sy_s = MM_H / WORLD_H
    for ore in ores:
        pygame.draw.circle(surf, ore.color,
                           (MM_X+int(ore.x*sx_s), MM_Y+int(ore.y*sy_s)), 2)
    for e in enemy_list:
        if e.alive:
            pygame.draw.circle(surf, C_DANGER,
                               (MM_X+int(e.x*sx_s), MM_Y+int(e.y*sy_s)), 2)
    if boss_mgr.boss and boss_mgr.boss.alive:
        b = boss_mgr.boss
        bx = MM_X+int(b.x*sx_s); by = MM_Y+int(b.y*sy_s)
        pygame.draw.circle(surf, (255,100,255), (bx,by), 5)
        pygame.draw.circle(surf, C_WHITE,       (bx,by), 5, 1)
    px = MM_X+int(player.x*sx_s); py = MM_Y+int(player.y*sy_s)
    pygame.draw.circle(surf, C_SECONDARY, (px,py), 4)
    pygame.draw.circle(surf, C_WHITE,     (px,py), 4, 1)
    vx1=MM_X+int(cam.x*sx_s); vy1=MM_Y+int(cam.y*sy_s)
    vx2=MM_X+int((cam.x+WIDTH)*sx_s); vy2=MM_Y+int((cam.y+HEIGHT)*sy_s)
    pygame.draw.rect(surf, C_GRAY, (vx1,vy1,vx2-vx1,vy2-vy1), 1)
    surf.blit(font_xs.render("MINIMAP",True,C_GRAY), (MM_X+4,MM_Y+2))

def draw_mode_badge(surf, mode_id, difficulty_id):
    from ui.layout import LX, MODE_Y
    m   = MODES.get(mode_id, MODES["classic"])
    d   = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normal"])
    col = m["color"]
    txt = font_xs.render(f"{m['icon']} {m['name']}  ·  {d['icon']} {d['name']}",True,col)
    rect= pygame.Rect(LX, MODE_Y, txt.get_width()+16, 20)
    draw_panel(surf, rect, alpha=160, border=col, radius=5)
    surf.blit(txt, (rect.x+8, rect.y+3))

def draw_danger_badge(surf, difficulty):
    from ui.layout import LX, BADGE_Y
    col = difficulty.danger_color
    txt = font_xs.render(f"◈ {difficulty.danger_label}  W{difficulty.wave}",True,col)
    rect= pygame.Rect(LX, BADGE_Y, txt.get_width()+16, 20)
    draw_panel(surf, rect, alpha=180, border=col, radius=6)
    surf.blit(txt, (rect.x+8, rect.y+3))

def draw_timed_countdown(surf, time_left):
    if time_left <= 0: return
    col  = C_DANGER if time_left < 30 else (C_ACCENT if time_left < 60 else C_SUCCESS)
    mins = int(time_left//60); secs = int(time_left%60)
    txt  = font_md.render(f"⏱  {mins}:{secs:02d}", True, col)
    rect = pygame.Rect(WIDTH//2-txt.get_width()//2-12, 6, txt.get_width()+24, 36)
    draw_panel(surf, rect, alpha=200, border=col, radius=8)
    surf.blit(txt, (rect.x+12, rect.y+6))
    if time_left < 10:
        a  = int(abs(math.sin(pygame.time.get_ticks()*0.006))*70)
        ov = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
        ov.fill((*C_DANGER, a)); surf.blit(ov,(0,0))

def build_session(mode_id="classic", difficulty_id="normal", load_save=False):
    mode = MODES.get(mode_id, MODES["classic"])
    diff = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normal"])

    upgrades   = UpgradeSystem()
    resources  = 0.0
    saved_wave = 0
    xp_data    = None

    if load_save:
        resources, saved_wave, mode_id, difficulty_id, xp_data = load_game(upgrades)
        mode = MODES.get(mode_id, MODES["classic"])
        diff = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normal"])

    if "no_upgrades" in mode["modifiers"]:
        upgrades = UpgradeSystem()
    if "all_maxed" in mode["modifiers"]:
        from utils.constants import UPGRADES as UG
        for ug in UG: upgrades.levels[ug["id"]] = ug["max_level"]

    player = Player(WORLD_W//2, WORLD_H//2)
    player.max_hp = max(60, int(100 * (2.0 - diff["enemy_hp"]) + 20))
    player.hp     = player.max_hp

    def sync_player(p, u):
        p.collect_range_bonus = u.collect_range_bonus
        p.speed_mult          = u.speed_mult
        p.vacuum_radius       = u.vacuum_radius
    sync_player(player, upgrades)

    enemies             = EnemyManager()
    enemies.wave        = saved_wave
    enemies.spawn_interval = mode["wave_interval"]
    enemies.spawn_timer = min(15.0, mode["wave_interval"])

    boss_mgr    = BossManager()
    res_sys     = ResourceSystem()
    combo       = ComboSystem()
    difficulty  = DifficultyScaler()
    difficulty.wave = saved_wave

    xp_sys = XPSystem()
    if xp_data:
        for k, v in xp_data.items():
            if hasattr(xp_sys, k): setattr(xp_sys, k, v)

    abilities   = AbilitySystem()
    weapons     = WeaponSystem()
    loot_sys    = LootSystem()
    event_sys   = EventSystem()
    weather     = WeatherSystem()

    particles   = ParticleSystem()
    floats      = FloatingTextManager()

    camera = Camera(WIDTH, HEIGHT, WORLD_W, WORLD_H)
    camera.x = player.x - WIDTH//2
    camera.y = player.y - HEIGHT//2

    hud        = HUD(font_lg, font_md, font_sm, font_xs)
    up_panel   = UpgradePanel(font_md, font_sm, font_xs)
    wave_timer = WaveTimer(font_md, font_sm, font_xs)

    prestige_sys.apply_to_session(player, upgrades)
    sync_player(player, upgrades)

    ore_mult  = (mode["ore_value_mult"]
                 * diff.get("ore_mult", 1.0)
                 * prestige_sys.ore_mult)
    time_left = float(mode["time_limit"]) if mode["time_limit"] > 0 else 0.0

    return dict(
        mode_id=mode_id, difficulty_id=difficulty_id,
        mode=mode, diff=diff,
        upgrades=upgrades, resources=resources,
        player=player, enemies=enemies, boss_mgr=boss_mgr,
        res_sys=res_sys, combo=combo, difficulty=difficulty,
        xp_sys=xp_sys, abilities=abilities, weapons=weapons,
        loot_sys=loot_sys, event_sys=event_sys, weather=weather,
        particles=particles, floats=floats,
        camera=camera, hud=hud, up_panel=up_panel, wave_timer=wave_timer,
        time_left=time_left, ore_mult=ore_mult,
        no_upgrades=("no_upgrades" in mode["modifiers"]),
        no_enemies=("no_enemies"  in mode["modifiers"]),
        nodmg_wave=True,
        sync_player=sync_player,
    )

STATE_MAIN     = "main"
STATE_MODE_SEL = "mode_sel"
STATE_DIFF_SEL = "diff_sel"
STATE_PLAYING  = "playing"
STATE_GAMEOVER = "gameover"
STATE_ACH      = "achievements"
STATE_HTP      = "howtoplay"

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

has_save = os.path.exists("data/save.json")

def make_main_menu():
    return MainMenu(font_lg, font_md, font_sm, font_xs,
                    has_save=os.path.exists("data/save.json"),
                    achievements=achievements,
                    highscores=highscores,
                    prestige=prestige_sys)

main_menu   = make_main_menu()
mode_screen = None
diff_screen = None
ach_screen  = None
htp_screen  = None

def on_time_slow():
    global time_slow, time_slow_timer
    if session and session["upgrades"].has_time_slow:
        time_slow=True; time_slow_timer=TIME_SLOW_DUR

def end_session_to_gameover(s, total_time):
    """Submit score, build GameOverScreen, return it."""
    is_rec = highscores.is_new_record(s["mode_id"], s["resources"])
    rank   = highscores.submit(s["mode_id"], s["difficulty_id"],
                                s["resources"], s["enemies"].wave, total_time)
    achievements.update_stat("max_wave", s["enemies"].wave, "max")
    return GameOverScreen(
        font_lg, font_md, font_sm, font_xs,
        s["resources"], s["enemies"].wave, total_time,
        s["mode_id"], s["difficulty_id"], rank, is_rec,
        prestige_sys.can_prestige(s["enemies"].wave))

running = True
while running:
    raw_dt = min(clock.tick(FPS)/1000.0, 0.05)

    events = pygame.event.get()
    inp.process_events(events)

    for event in events:
        if event.type == pygame.QUIT:
            running = False

        if state == STATE_MAIN:
            main_menu.handle_event(event)
            if main_menu.done:
                if getattr(main_menu, 'to_howtoplay', False):
                    htp_screen = HowToPlayScreen(font_lg,font_md,font_sm,font_xs)
                    state = STATE_HTP; main_menu.done=False
                elif main_menu.to_achievements:
                    ach_screen = AchievementsScreen(
                        font_lg,font_md,font_sm,font_xs, achievements)
                    state = STATE_ACH; main_menu.done=False
                elif main_menu.to_mode_select:
                    mode_screen = ModeSelectScreen(
                        font_lg,font_md,font_sm,font_xs,
                        prestige=prestige_sys, highscores=highscores)
                    state=STATE_MODE_SEL; main_menu.done=False

        elif state == STATE_MODE_SEL:
            mode_screen.handle_event(event)
            if mode_screen.done:
                if mode_screen.back:
                    state=STATE_MAIN; mode_screen=None
                elif mode_screen.selected_mode:
                    pending_mode=mode_screen.selected_mode
                    diff_screen=DifficultyScreen(
                        font_lg,font_md,font_sm,font_xs,pending_mode)
                    state=STATE_DIFF_SEL; mode_screen=None

        elif state == STATE_DIFF_SEL:
            diff_screen.handle_event(event)
            if diff_screen.done:
                if diff_screen.back:
                    mode_screen=ModeSelectScreen(
                        font_lg,font_md,font_sm,font_xs,
                        prestige=prestige_sys,highscores=highscores)
                    state=STATE_MODE_SEL; diff_screen=None
                elif diff_screen.selected:
                    session=build_session(pending_mode,diff_screen.selected)
                    total_time=0.0; time_slow=False
                    state=STATE_PLAYING; diff_screen=None

        elif state == STATE_ACH:
            ach_screen.handle_event(event)
            if ach_screen.done:
                state=STATE_MAIN; ach_screen=None
                main_menu=make_main_menu()

        elif state == STATE_HTP:
            htp_screen.handle_event(event)
            if htp_screen.done:
                state=STATE_MAIN; htp_screen=None
                main_menu=make_main_menu()

        elif state == STATE_GAMEOVER and go_screen:
            go_screen.handle_event(event)
            if go_screen.restart:
                session=build_session(go_screen.mode_id,go_screen.difficulty_id)
                total_time=0.0; time_slow=False
                state=STATE_PLAYING; go_screen=None
            elif go_screen.prestige:
                kept=prestige_sys.do_prestige(go_screen.resources)
                session=build_session(go_screen.mode_id,go_screen.difficulty_id)
                session["resources"]=kept
                total_time=0.0; time_slow=False
                state=STATE_PLAYING; go_screen=None
            elif go_screen.quit:
                main_menu=make_main_menu()
                state=STATE_MAIN; go_screen=None

        elif state == STATE_PLAYING and session:
            s = session
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    save_game(s["resources"],s["upgrades"],s["enemies"].wave,
                              s["xp_sys"],s["mode_id"],s["difficulty_id"])
                    running=False
                elif event.key == pygame.K_s:
                    save_game(s["resources"],s["upgrades"],s["enemies"].wave,
                              s["xp_sys"],s["mode_id"],s["difficulty_id"])
                    save_flash=2.0
                elif event.key == pygame.K_TAB:
                    s["weapons"].cycle_weapon()
                    s["particles"].burst(s["player"].x, s["player"].y,
                        s["weapons"].current["color"],count=8,speed=60,life=0.3)

                for ai, key in enumerate([pygame.K_q, pygame.K_e, pygame.K_f]):
                    if event.key == key:
                        gained = s["abilities"].fire(
                            ai, s["player"], s["enemies"], s["boss_mgr"],
                            s["res_sys"], s["particles"], s["floats"],
                            font_sm, s["camera"])
                        if gained:
                            s["resources"] += int(gained * s["ore_mult"]
                                                   * s["event_sys"].get_resource_mult())
                            s["camera"].shake(12, 0.3)
                            s["weather"].spawn_ring(
                                s["player"].x, s["player"].y,
                                s["abilities"].abilities[ai].color,
                                max_radius=250, speed=300)

            elif event.type == pygame.MOUSEWHEEL:
                if s["up_panel"].panel_rect.collidepoint(inp.mouse_pos):
                    s["up_panel"].handle_scroll(event.y)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mp = inp.mouse_pos
                if event.button == 1:
                    if (not s["no_upgrades"] and
                            s["up_panel"].panel_rect.collidepoint(mp)):
                        s["resources"] = s["up_panel"].handle_click(
                            mp, s["resources"], s["upgrades"])
                        s["sync_player"](s["player"], s["upgrades"])
                        from utils.constants import UPGRADES as UGL
                        achievements.update_stat("upgrades_bought",1)
                        achievements.update_stat("upgrades_maxed",
                            sum(1 for u in UGL if s["upgrades"].maxed(u["id"])),"max")
                        achievements.update_stat("unique_upgrades",
                            sum(1 for u in UGL if s["upgrades"].level(u["id"])>0),"max")
                    else:
                        wx,wy = s["camera"].screen_to_world(*mp)
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
                            evmul = s["event_sys"].get_resource_mult()
                            lmul  = s["loot_sys"].damage_mult
                            total = int(gained * mult * s["ore_mult"]
                                        * evmul * s["xp_sys"].income_mult)
                            s["resources"] += total
                            s["camera"].shake(3, 0.07)
                            achievements.update_stat("crystals_collected",1)
                            achievements.update_stat("total_resources",total)
                            if mult >= 8.0:
                                achievements.update_stat("max_combo",8,"max")

                elif event.button == 3:
                    wx,wy = s["camera"].screen_to_world(*inp.mouse_pos)
                    dmul  = s["loot_sys"].damage_mult
                    if s["weapons"].shoot(s["player"].x, s["player"].y,
                                          wx, wy, s["upgrades"].bolt_level, dmul):
                        s["particles"].emit(
                            s["player"].x, s["player"].y,
                            (wx-s["player"].x)*0.3,(wy-s["player"].y)*0.3,
                            life=0.2, color=s["weapons"].current["color"],
                            size=3, glow=True)

    if state == STATE_MAIN:
        main_menu.update(raw_dt); screen.fill(C_BG); main_menu.draw(screen)
        pygame.display.flip(); continue
    if state == STATE_MODE_SEL and mode_screen:
        mode_screen.update(raw_dt); screen.fill(C_BG); mode_screen.draw(screen)
        pygame.display.flip(); continue
    if state == STATE_DIFF_SEL and diff_screen:
        diff_screen.update(raw_dt); screen.fill(C_BG); diff_screen.draw(screen)
        pygame.display.flip(); continue
    if state == STATE_ACH and ach_screen:
        ach_screen.update(raw_dt); screen.fill(C_BG); ach_screen.draw(screen)
        pygame.display.flip(); continue
    if state == STATE_HTP and htp_screen:
        htp_screen.update(raw_dt); screen.fill(C_BG); htp_screen.draw(screen)
        pygame.display.flip(); continue
    if state == STATE_GAMEOVER and go_screen:
        go_screen.update(raw_dt); screen.fill(C_BG); go_screen.draw(screen)
        pygame.display.flip(); continue
    if state != STATE_PLAYING or session is None:
        pygame.display.flip(); continue

    s = session

    slow_factor = 0.3 if (time_slow or s["loot_sys"].time_warp_active) else 1.0
    dt          = raw_dt * slow_factor

    total_time      += raw_dt
    save_flash       = max(0, save_flash - raw_dt)
    time_slow_timer  = max(0, time_slow_timer - raw_dt)
    if time_slow_timer <= 0: time_slow=False
    ambient_timer   -= dt

    if s["time_left"] > 0:
        s["time_left"] = max(0, s["time_left"] - raw_dt)
        if s["time_left"] <= 0:
            if s["mode_id"] == "blitz":
                achievements.update_stat("blitz_wins",1)
            if s["mode_id"] == "crystal_rush":
                achievements.update_stat("rush_best",int(s["resources"]),"max")
            go_screen = end_session_to_gameover(s, total_time)
            state=STATE_GAMEOVER; continue

    if inp.mouse_buttons[2]:
        wx,wy = s["camera"].screen_to_world(*inp.mouse_pos)
        dmul  = s["loot_sys"].damage_mult
        if s["weapons"].shoot(s["player"].x, s["player"].y,
                               wx, wy, s["upgrades"].bolt_level, dmul):
            s["particles"].emit(s["player"].x, s["player"].y,
                (wx-s["player"].x)*0.3,(wy-s["player"].y)*0.3,
                life=0.15, color=s["weapons"].current["color"], size=2, glow=True)

    s["player"].speed_mult = (s["upgrades"].speed_mult
                               * s["loot_sys"].speed_mult)
    s["player"].update(dt, inp, WORLD_W, WORLD_H)

    if s["player"].hp <= 0:
        save_game(s["resources"],s["upgrades"],s["enemies"].wave,
                  s["xp_sys"],s["mode_id"],s["difficulty_id"])
        s["particles"].burst(s["player"].x,s["player"].y,
                             C_SECONDARY,count=50,speed=200,life=1.5)
        s["camera"].shake(20,0.8)
        s["weather"].spawn_ring(s["player"].x,s["player"].y,
                                C_DANGER,max_radius=400,speed=350,width=4)
        go_screen=end_session_to_gameover(s,total_time)
        state=STATE_GAMEOVER; continue

    s["camera"].follow(s["player"].x, s["player"].y, raw_dt, speed=5.0)
    s["camera"].update(raw_dt)

    s["event_sys"].update(dt)
    ev = s["event_sys"]
    s["weather"].set_storm(ev.triple_ore_spawn)
    s["weather"].set_blood_moon(ev.blood_moon)
    s["weather"].update(dt, s["camera"])

    if ev.get_instant_nova():
        from systems.resource_system import WORLD_W as WW, WORLD_H as WH
        for ore in s["res_sys"].ores:
            ore.alive = False
            s["resources"] += ore.value * s["upgrades"].click_power * 5
            s["particles"].burst(ore.x,ore.y,ore.color,count=12,speed=160,life=0.7)
        s["res_sys"].ores = []
        s["camera"].shake(15, 0.4)
        s["weather"].spawn_ring(s["player"].x,s["player"].y,
                                (255,200,80),max_radius=600,speed=400,width=5)

    if ev.ore_gravity:
        for ore in s["res_sys"].ores:
            dx = s["player"].x - ore.x
            dy = s["player"].y - ore.y
            d  = math.hypot(dx,dy)+0.01
            ore.x += (dx/d) * 120 * dt
            ore.y += (dy/d) * 120 * dt

    if ev.triple_ore_spawn and len(s["res_sys"].ores) < 40:
        s["res_sys"]._spawn_ore(s["player"].x, s["player"].y)

    s["res_sys"].rare_boost = s["upgrades"].rare_boost
    for ore in s["res_sys"].ores:
        ore.update(dt)

    s["resources"] += s["res_sys"].auto_collect(
        dt, s["player"], s["upgrades"].auto_income * prestige_sys.auto_mult)

    if s["upgrades"].hp_regen > 0:
        s["player"].heal(s["upgrades"].hp_regen * dt)

    vac = s["res_sys"].vacuum_collect(
        s["player"],s["particles"],s["floats"],
        font_sm, s["upgrades"].click_power)
    if vac:
        evmul = ev.get_resource_mult()
        s["resources"] += int(vac * s["ore_mult"] * evmul)
        achievements.update_stat("crystals_collected",1)

    s["weapons"].update(dt)
    s["weapons"].check_hits(s["enemies"].enemies, s["boss_mgr"], s["particles"])

    s["abilities"].update(dt)

    collected_loot = s["loot_sys"].update(dt, s["player"], s["particles"])
    if "magnet" in collected_loot or s["loot_sys"].magnet_active:
        for ore in s["res_sys"].ores:
            dx=s["player"].x-ore.x; dy=s["player"].y-ore.y
            d=math.hypot(dx,dy)+0.01
            if d < 350:
                ore.x+=(dx/d)*200*dt; ore.y+=(dy/d)*200*dt

    if not s["no_enemies"]:
        diff_cfg = s["diff"]
        hp_mult  = diff_cfg["enemy_hp"] * s["difficulty"].enemy_hp_mult
        spd_mult = diff_cfg["enemy_speed"] * s["difficulty"].enemy_speed_mult
        dmg_mult = (diff_cfg["enemy_dmg"] * s["difficulty"].enemy_damage_mult
                    * ev.get_enemy_dmg_mult())

        prev_wave = s["enemies"].wave
        s["enemies"].spawn_timer -= dt
        spawn_count_bonus = 2 if ev.double_enemies else 0
        if s["enemies"].spawn_timer <= 0:
            s["enemies"]._spawn_wave(s["player"].x, s["player"].y)
            for _ in range(spawn_count_bonus):
                s["enemies"]._spawn_wave(s["player"].x, s["player"].y)
            s["enemies"].spawn_timer   = s["enemies"].spawn_interval
            s["enemies"].spawn_interval= max(8.0, s["enemies"].spawn_interval-0.4)

        killed = []
        for enemy in s["enemies"].enemies:
            if not enemy.alive: killed.append(enemy); continue
            enemy.update(dt, s["player"].x, s["player"].y)
            if dist(enemy.x,enemy.y,s["player"].x,s["player"].y) \
                    < enemy.size + s["player"].RADIUS:
                if s["player"].take_damage(int(enemy.dmg * dmg_mult)):
                    s["particles"].burst(s["player"].x,s["player"].y,
                                         (255,80,80),count=10)
                    s["weather"].spawn_ring(s["player"].x,s["player"].y,
                                           C_DANGER,max_radius=80,speed=200,width=2)
                    s["nodmg_wave"]=False
                enemy.alive=False; killed.append(enemy)

        for e in killed:
            if e in s["enemies"].enemies:
                s["enemies"].enemies.remove(e)
                if not e.alive and e.hp <= 0:
                    reward = int(e.reward * s["xp_sys"].income_mult
                                 * ev.get_resource_mult()
                                 * (5.0 if ev.blood_moon else 1.0))
                    xp     = s["xp_sys"].register_kill(e.reward)
                    s["resources"] += reward
                    s["particles"].burst(e.x,e.y,e.color,count=15,speed=150)
                    s["weather"].spawn_ring(e.x,e.y,e.color,
                                           max_radius=60,speed=180,width=2)
                    s["floats"].add(e.x,e.y-20,f"+{reward}✦",
                                    font_sm,(255,220,80))
                    s["floats"].add(e.x,e.y-38,f"+{xp}xp",
                                    font_sm,C_ACCENT,speed=-55,life=0.9)
                    achievements.update_stat("kills",1)
                    s["loot_sys"].drop(e.x,e.y,e.loot_type)

        if s["enemies"].wave != prev_wave:
            nw = s["enemies"].wave
            s["hud"].announce_wave(nw)
            s["camera"].shake(10,0.3)
            s["difficulty"].wave=nw
            achievements.update_stat("max_wave",nw,"max")
            if s.get("nodmg_wave") and nw>=3:
                achievements.update_stat("nodmg_wave3",1)
            s["weather"].spawn_ring(s["player"].x,s["player"].y,
                                    (120,60,255),max_radius=350,speed=280,width=3)
            if s["boss_mgr"].check_spawn(nw,s["player"].x,s["player"].y):
                s["camera"].shake(15,0.5)
                s["weather"].spawn_ring(s["player"].x,s["player"].y,
                                        (255,70,90),max_radius=500,speed=350,width=5)

        boss_reward = s["boss_mgr"].update(
            dt, s["player"], s["particles"], s["floats"], font_md)
        if boss_reward:
            evmul = ev.get_resource_mult()
            bxp   = s["xp_sys"].register_kill(boss_reward, is_boss=True)
            s["resources"] += int(boss_reward * s["xp_sys"].income_mult * evmul)
            s["camera"].shake(20,0.6)
            s["floats"].add(s["player"].x,s["player"].y-60,
                            f"+{bxp} XP",font_sm,C_ACCENT,speed=-50,life=1.5)
            achievements.update_stat("bosses_killed",1)
            if s["boss_mgr"].boss:
                b=s["boss_mgr"].boss
                s["loot_sys"].drop(b.x,b.y,"boss",is_boss=True)
            s["weather"].spawn_ring(s["player"].x,s["player"].y,
                                    (200,100,255),max_radius=600,speed=400,width=6)

    s["combo"].update(dt)
    s["difficulty"].tick(dt, s["enemies"].wave)
    s["xp_sys"].update(dt)
    s["xp_sys"].apply_to_player(s["player"])
    achievements.update_stat("player_level",s["xp_sys"].level,"max")
    achievements.update(dt)

    s["particles"].update(dt)
    s["floats"].update(dt)

    if ambient_timer <= 0:
        ambient_timer=0.07
        for ore in random.sample(s["res_sys"].ores,
                                 min(3,len(s["res_sys"].ores))):
            s["particles"].emit(
                ore.x+random.uniform(-ore.radius,ore.radius),
                ore.y+random.uniform(-ore.radius,ore.radius),
                random.uniform(-15,15), random.uniform(-45,-10),
                life=random.uniform(0.3,0.7),
                color=ore.glow, end_color=(20,10,40),
                size=random.uniform(1,3), glow=True)

    if s["player"].dashing:
        s["particles"].trail(s["player"].x,s["player"].y,
                             vx=s["player"].vx,vy=s["player"].vy,color=C_SECONDARY, life=0.4)

    s["hud"].update(raw_dt,s["resources"],time_slow)
    s["up_panel"].update(raw_dt,inp.mouse_pos,s["upgrades"])

   
    cam = s["camera"]
    screen.fill(C_BG)

    world_obj.draw(screen, cam)
    s["weather"].draw(screen, cam)         
    s["res_sys"].draw(screen, cam)
    s["loot_sys"].draw(screen, cam, font_xs)
    s["particles"].draw(screen, cam.dx, cam.dy)
    if not s["no_enemies"]:
        s["enemies"].draw(screen, cam)
        s["boss_mgr"].draw(screen, cam)
    s["player"].draw(screen, cam)
    s["weapons"].draw(screen, cam)
    s["floats"].draw(screen, cam.dx, cam.dy)

    screen.blit(get_vignette(WIDTH, HEIGHT), (0,0))
    s["weather"].draw_overlays(screen)     

    if time_slow or s["loot_sys"].time_warp_active:
        rem  = time_slow_timer if time_slow else s["loot_sys"].effect_ratio("time_warp")*TIME_SLOW_DUR
        a    = int(50*(rem/TIME_SLOW_DUR))
        ov   = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        ov.fill((60,20,120,a)); screen.blit(ov,(0,0))
        ts = font_sm.render("◈  TEMPORAL SURGE  ◈",True,(200,150,255))
        screen.blit(ts,(WIDTH//2-ts.get_width()//2,18))

    
    s["hud"].draw(screen, s["player"], s["upgrades"], s["enemies"].wave, time_slow)
    s["hud"].draw_stats(screen, s["upgrades"])
    s["hud"].draw_xp_bar(screen, s["xp_sys"])
    s["hud"].draw_fps(screen, clock.get_fps())

    if not s["no_upgrades"]:
        s["up_panel"].draw(screen, s["resources"], s["upgrades"])

    draw_minimap(screen, s["player"], s["res_sys"].ores,
                 s["enemies"].enemies, s["boss_mgr"], cam)

    s["combo"].draw(screen, font_md, font_xs)
    s["xp_sys"].draw(screen, font_lg, font_md, font_xs)
    s["abilities"].draw_hud(screen, font_sm, font_xs)
    s["weapons"].draw_hud(screen, font_sm, font_xs)
    s["wave_timer"].draw(screen, s["enemies"], s["boss_mgr"])
    s["loot_sys"].draw_effects_hud(screen, font_xs)

    draw_danger_badge(screen, s["difficulty"])
    draw_mode_badge(screen, s["mode_id"], s["difficulty_id"])

    if not s["no_enemies"]:
        draw_warning_arrows(screen,s["player"],s["enemies"].enemies,
                            s["boss_mgr"],cam,font_xs)
        s["boss_mgr"].draw_intro(screen,font_lg,font_md)

    s["event_sys"].draw_announcement(screen, font_lg, font_md, font_xs)
    s["event_sys"].draw_active_banner(screen, font_xs)

    if s["time_left"] > 0:
        draw_timed_countdown(screen, s["time_left"])

    achievements.draw(screen, font_md, font_sm, font_xs)

    if save_flash > 0:
        a  = int(255*smooth_step(min(save_flash,1.0)))
        ms = font_sm.render("✓  Game Saved",True,C_SUCCESS)
        ms.set_alpha(a)
        screen.blit(ms,(WIDTH//2-ms.get_width()//2,HEIGHT-60))

    pygame.display.flip()

if session:
    save_game(session["resources"],session["upgrades"],session["enemies"].wave,
              session["xp_sys"],session["mode_id"],session["difficulty_id"])
achievements.save()
pygame.quit()
sys.exit()

