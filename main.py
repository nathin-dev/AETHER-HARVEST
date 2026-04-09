"""
AETHER HARVEST v2.0
"""

import pygame 
import sys
import math
import random
import os 

sys.path.insert(0, os.path.dirname(__file__))

from utils.constants import (WIDTH, HEIGHT, FPS, TITLE,
                             C_BG, C_WHITE, C_PRIMARY, C_SECONDARY,
                             C_ACCENT, C_DANGER, C_SUCCESS, C_GRAY, UPGRADES)

from utils.math_utils import format_number, lerp, smooth_step

from engine.camera import Camera
from engine.input import InputHandler
from engine.particles import ParticleSystem, FloatingTextManager
from engine.renderer import (draw_panel, draw_glow_circle,
                             draw_glow_rect, get_vignette)

from entities.player import Player
from entities.enemy import EnemyManager
from entities.boss import BossManager 

from systems.resource_system import ResourceSystem,  WORLD_W, WORLD_H
from systems.upgrade_system import UpgradeSystem
from systems.combo  import ComboSystem

from ui.hud import HUD, UpgradePanel
from ui.menu import MainMenu, GameOverScreen

from world.world import World

from core.save  import save_game, load_game
from core.difficulty import DifficultyScaler


# --- Pygame Init -----

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF   )
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

def load_font(size, bold=False):
    for name in ("Segoe UI", "Ubuntu", "Dejavu Sans", "veranda", "Arial"):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

font_lg = load_font(36, bold=True)
font_md = load_font(24)
font_sm = load_font(18)
font_xs = load_font(13)

# ---- MiniMap ----
def draw_minimap(surf, player, ores, enemy_list, boss_mgr, cam):
    MM_W, MM_H = 150, 95
    MM_X = WIDTH - MM_W - 12
    MM_Y = HEIGHT - MM_H -35
    mm_rect = pygame.Rect(MM_X, MM_Y, MM_W, MM_H)
    draw_panel(surf, mm_rect, alpha=210, radius=6)

    sx = MM_W / WORLD_W
    sy = MM_H / WORLD_H

    for ore in ores:
        ox = MM_X + int(ore.x * sx)
        oy = MM_Y + int(ore.y * sy)
        pygame.draw.circle(surf, ore.color, (ox, oy), 2)

    for e in enemy_list:
        if e.alive:
            ex = MM_X + int(e.x * sx)
            ey = MM_Y + int(e.y * sy)
            pygame.draw.circle(surf, C_DANGER, (ex, ey), 2)

    if boss_mgr.boss and boss_mgr.boss.alive:
        bx = MM_X +  int(boss_mgr.boss.x * sx)
        by = MM_Y + int(boss_mgr.boss.y * sy)
        pygame.draw.circle(surf, (255, 100, 255), (bx, by), 5)
        pygame.draw.circle(surf, C_WHITE, (bx, by), 5, 1)

    
    px =MM_X + int(player.x * sx)
    py = MM_Y + int(player.y * sy)
    pygame.draw.circle(surf, C_SECONDARY, (px, py), 4)
    pygame.draw.circle(surf, C_WHITE, (px, py), 4, 1)

    vx1 = MM_X + int(cam.x * sx)
    vy1 = MM_Y + int(cam.y * sy)
    vx2 = MM_X + int ((cam.x + WIDTH) * sx)
    vy2 = MM_Y + int((cam.y + HEIGHT) * sy)
    pygame.draw.rect(surf, C_GRAY, (vx1, vy1, vx2 - vx1, vy2 - vy1),1 )

    lbl = font_xs.render("MINIMAP", True, C_GRAY)
    surf.blit(lbl, (MM_X + 4, MM_Y + 2))

def draw_danger_badge(surf, difficulty):
    col = difficulty.danger_color
    txt = font_xs.render(
        f" {difficulty.danger_label} W{difficulty.wave}", True, col)
    rect = pygame(surf, rect, alpha=180, border=col, radius=6)
    surf.blit(txt, (rect.x + 8, rect.y + 4))


# ---- Session factory -----

def build_session(load_save=False):
    upgrades = UpgradeSystem()
    resources = 0.0
    saved_wave = 0

    if load_save:
        resources, saved_wave = load_game(upgrades)

    player  = Player(WORLD_W // 2, WORLD_H // 2)
    player.collect_range_bonus = upgrades.collect_range_bonus

    enemies = EnemyManager()
    enemies.wave = saved_wave

    boss_mgr = BossManager()
    res_sys = ResourceSystem()
    combo = ComboSystem()
    difficulty = DifficultyScaler()
    difficulty.wave = saved_wave

    particles = ParticleSystem()
    floats = FloatingTextManager()

    camera = Camera(WIDTH, HEIGHT, WORLD_W, WORLD_H)
    camera.x = player.x - WIDTH // 2
    camera.y = player.y - HEIGHT // 2

    hud = HUD(font_lg, font_md, font_sm, font_xs)
    up_panel = UpgradePanel(font_md, font_sm, font_xs)

    return dict(
        upgrades=upgrades, resources=resources, player=player,
        enemies=enemies, boss_mgr=boss_mgr, res_sys=res_sys,
        combo=combo, difficulty=difficulty,
        particles=particles, floats=floats,
        camera=camera, hud=hud, up_panel=up_panel,
    )


# --- State Machine ----
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAMEOVER = "gameover"

state = STATE_MENU
inp = InputHandler()
world_obj = World()

has_save = os.path.exists("data/save.json")
menu = MainMenu(font_lg, font_md, font_sm, font_xs, has_save=has_save)
session = None
go_screen = None

total_time = 0.0
time_slow = False 
time_slow_timer = 0.0
TIME_SLOW_DUR = 3.0
save_flash = 0.0
ambient_timer = 0.0


def on_time_slow():
    global time_slow, time_slow_timer
    if session and session["upgrades"].has_time_slow:
        time_slow = True 
        time_slow_timer = TIME_SLOW_DUR

# --- Main Loop ---

running = True
while running:

    raw_dt = min(clock.tick(FPS) / 1000.0, 0.05)

    events = pygame.event.get()
    inp.process_events(events)

    for event in events:
        if event.type == pygame.QUIT:
            running = False

        # -- menu ---
        if state == STATE_MENU:
            menu.handle_event(event)
            if menu.done:
                session = build_session(load_save=not menu.new_game)
                total_time = 0.0
                time_slow = False 
                state = STATE_PLAYING

        # -- Game Over -- 
        elif state == STATE_GAMEOVER and go_screen:
            go_screen.handle_event(event)
            if go_screen.restart:
                session = build_session(load_save=False)
                time_slow = False
                state = STATE_PLAYING
                go_screen = None 
            elif go_screen.quit:
                menu = MainMenu(font_lg, font_md, font_sm, font_xs,
                                has_save=os.path.exists("data/save.json"))
                state  =  STATE_MENU
                go_screen = None

        
        # --- playing --- 
        elif state == STATE_PLAYING and session:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_s:
                    save_game(session["resources"],
                              session["upgrades"],
                              session["enemies"].wave)
                    save_flash = 2.0 
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                s = session 
                mouse_p = inp.mouse_pos 

                if s["up_panel"].panel_rect.collidepoint(mouse_p):
                    s["resources"] = s["up_panel"].handle_click(
                        mouse_p, s["resources"], s["upgrades"])
                    s["player"].collect_range_bonus = s["upgrades"].collect_range_bonus
                else:
                    wx, wy = s["camera"].screen_to_world(*mouse_p)
                    gained = s["res_sys"].try_collect(
                        wx, wy, s["player"], s["particles"], s["floats"],
                        font_sm,
                        click_power = s["upgrades"].click_power,
                        rare_boost = s["upgrades"].rare_boost,
                        chain_chance = s["upgrades"].chain_chance,
                        time_slow_cb = on_time_slow,
                        cam = s["camera"],
                    )
                    if gained:
                        mult = s["combo"].register_collect()
                        total_gained = int(gained * mult )
                        s["resources"] += total_gained 
                        s["camera"].shake(intensity=3, duration=0.07)
                        if mult > 1.0:
                            s["floats"].add(wx, wy - 50,
                                           f"x{mult:.1f}", font_sm,
                                           C_ACCENT, speed=-60, life=0.8)
                            
    # --- Render by State ----
    if state == STATE_MENU:
        menu.update(raw_dt)
        screen.fill(C_BG)
        menu.draw(screen)
        pygame.display.flip()
        continue 
    if state ==  STATE_GAMEOVER and go_screen:
       go_screen.update(raw_dt)
       screen.fill(C_BG)
       go_screen.draw(screen)
       pygame.display.flip()
       continue 
    if state != STATE_PLAYING or session is None:
        pygame.display.flip()
        continue 
    # --- playing update ---
    s = session
    dt = raw_dt * (0.3 if time_slow else 1.0)
    total_time += raw_dt
    save_flash = max(0, save_flash - raw_dt)
    time_slow_timer = max(0, time_slow_timer - raw_dt)
    if time_slow_timer <= 0:
        time_slow = False 
    ambient_timer -= dt
    # Player
    s["player"].update(dt, inp, WORLD_W, WORLD_H)
    # Player death
    if s["player"].hp <= 0:
        save_game(s["resources"], s["upgrades"], s["enemies"].wave)
        s["particles"].burst(s["player"].x, s["player"].y,
                             C_SECONDARY, count=50, speed=200, life=1.5)
        s["camera"].shake(20, 0.8)
        go_screen = GameOverScreen(font_lg, font_md, font_sm, font_xs,
        s["resources"],s["enemies"].wave, total_time)
        state = STATE_GAMEOVER
        continue 
    # Camera
    s["camera"].follow(s["player"].x, s["player"].y, raw_dt, speed=5.0)
    s["camera"].update(raw_dt)
    # Ore passive update
    for ore in s["res_sys"].ores:
        ore.update(dt)
    # Auto income
    s["resources"] += s["res_sys"].auto_collect(dt, s["player"],
                                                s["upgrades"].auto_income)
    # Enemies 
    prev_wave = s["enemies"].wave
    reward = s["enemies"].update(dt, s["player"], s["particles"],
    s["floats"], font_sm)
    s["resources"] += reward or 0
    if s["enemies"].wave != prev_wave:
        nw =s["enemies"].wave
        s["hud"].announce_wave(nw)
        s["camera"].shake(10, 0.3)
        s["difficulty"].wave = nw 
        if s["boss_mgr"].check_spawn(nw, s["player"].x, s["player"].y):
            s["camera"].shake(15, 0.5)

    # Boss
    boss_reward = s["boss_mgr"].update(dt, s["player"], s["particles"],
    s["floats"], font_md)
    if boss_reward:
        s["resources"] += boss_reward 
        s["camera"].shake(20, 0.6)
    # Combo and Difficulty
    s["combo"].update(dt)
    s["difficulty"].tick(dt, s["enemies"].wave)
    # Particles / floats 
    s["particles"].update(dt)
    s["floats"].update(dt)
    # Ambient sparkles 
    if ambient_timer <= 0:
        ambient_timer = 0.67
        for ore in random.sample(s["res_sys"].ores,
                                 min(3, len(s["res_sys"].ores))):
            s["particles"].emit(
                ore.x + random.uniform(-ore.radius, ore.radius),
                ore.y + random.uniform(-ore.radius, ore.radius),
                random.uniform(-15, 15), random.uniform(-45, -10),
                life=random.uniform(0.3, 0.7),
                color=ore.glow, end_color=(20, 10, 40),
                size=random.uniform(1, 3), glow=True,
            )
        
    # dash Trail 
    if s["player"].dashing:
        s["particles"].trail(s["player"].x, s["player"].y, C_SECONDARY,
                            vx=s["player"].vx, vy=s["player"].vy)
         
    # HUD
    s["hud"].update(raw_dt, s["resources"], time_slow)
    s["up_panel"].update(raw_dt, inp.mouse_pos, s["upgrades"])
    # --- Draw ---
    cam= s["camera"]
    screen.fill(C_BG)
    world_obj.draw(screen, cam)
    s["res_sys"].draw(screen, cam)
    s["particles"].draw(screen, cam.dx, cam.dy)
    s["enemies"].draw(screen, cam)
    s["boss_mgr"].draw(screen, cam)
    s["player"].draw(screen, cam)
    s["floats"].draw(screen, cam.dx, cam.dy)
    screen.blit(get_vignette(WIDTH, HEIGHT), (0, 0))
    # Time-slow overlay
    if time_slow:
        alpha = int(50 * (time_slow_timer / TIME_SLOW_DUR))
        over = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        over.fill((60, 20, 120, alpha))
        screen.blit(over, (0, 0))
        ts = font_sm.render(" * TEMPORAL SURGE *", True, (200, 150, 255))
        screen.blit(ts, ( WIDTH // 2 - ts.get_width() //  2, 18))
    s["hud"].draw(screen, s["player"], s["upgrades"], s["enemies"].wave, time_slow)
    s["up_panel"].draw(screen, s["resources"], s["upgrades"])
    s["combo"].draw(screen, font_md, font_xs)
    draw_minimap(screen, s["player"], s["res_sys"].ores,
                    s["enemies"].enemies, s["boss_mgr"], cam)
    s["boss_mgr"].draw_intro(screen, font_lg, font_md)
    if save_flash > 0:
         a = int(255 * smooth_step(min(save_flash, 1.0)))
         msg = font_sm.render("✓  Game Saved", True, C_SUCCESS)
         msg.set_alpha(a)
         screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT - 60))
    fps_s = font_xs.render(f"{int(clock.get_fps())} fps", True, C_GRAY)
    screen.blit(fps_s, (8, HEIGHT - 18))
    pygame.display.flip()
# --- cleanup ----
if session:
    save_game(session["resources"], session["upgrades"],
              session["enemies"].wave)

pygame.quit()
sys.exit()