print("GAME STARTED")

import pygame
import sys
import random

# ------CONFIG ------
WIDTH, HEIGHT = 800, 600
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game Prototype")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)

# -------PLAYER ------------

player_pos = [WIDTH // 2, HEIGHT // 2]
player_speed = 5

# -------- RESOURCE -----------

resource_pos = [random.randint(50, 750), random.randint(50, 550)]
resource_radius = 20
resource_scale = 1.0



# --------- GAME DATA ---------

resources = 0
click_power = 1
auto_income = 0

upgrade_cost = 10
auto_cost = 25

click_effects = []
shake_time = 0

button_scale = {
    "upgrade": 1.0,
    "auto": 1.0

}



# --------COLORS ----------
WHITE = (255, 255, 255)
GREEN = (50, 200, 50)
BLUE = (50, 150, 255)
BLACK = (20, 20, 20)
GRAY = (100, 100, 100)

# ---------BUTTONS   --------

upgrade_button = pygame.Rect(600, 100, 150, 50)
auto_button = pygame.Rect(600, 180, 150, 50)

# ------- FUNCTIONS ----------


def draw_text(text, x, y):
    label = font.render(text, True, WHITE)
    screen.blit(label, (x, y))

def move_player(keys):
    if keys[pygame.K_w]:
        player_pos[1] -= player_speed
    if keys[pygame.K_s]:
        player_pos[1] += player_speed
    if keys[pygame.K_a]:
        player_pos[0] -= player_speed
    if keys[pygame.K_d]:
        player_pos[0] += player_speed
    

def check_collision():
    dx = player_pos[0] - resource_pos[0]
    dy = player_pos[1] - resource_pos[1]
    return dx * dx + dy * dy < (resource_radius + 15) ** 2


def respawn_resource():
    resource_pos[0] = random.randint(50, 750)
    resource_pos[1] = random.randint(50, 550)

def draw_button(rect, text, key):
    mouse_pos = pygame.mouse.get_pos()

    if rect.collidepoint(mouse_pos):
        color = (150, 150, 150)
    else:
        color = GRAY    
    
    scale = button_scale[key]
    new_rect = rect.inflate(rect.width * (scale - 1), rect.height * (scale - 1))

    pygame.draw.rect(screen, color, new_rect)
    draw_text(text, new_rect.x + 10, new_rect.y + 10)




# --------- GAME LOOP ------------

running = True
while running:
    dt = clock.tick(FPS) / 1000 # delta time

    # SCREEN SHAKE
    offset_x, offset_y = 0, 0
    if shake_time > 0:
        shake_time -= dt
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)


    screen.fill(BLACK)

    #   EVENTS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False 

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # BUTTONS FIRST
            if upgrade_button.collidepoint(mouse_pos):
                print("Upgrade clicked")  # DEBUG

                if resources >= upgrade_cost:
                    resources -= upgrade_cost
                    click_power += 1
                    upgrade_cost = int(upgrade_cost * 1.5)
                    button_scale["upgrade"] = 1.2

            elif auto_button.collidepoint(mouse_pos):
                print("Auto clicked")  # DEBUG

                if resources >= auto_cost:
                    resources -= auto_cost
                    auto_income += 1
                    auto_cost = int(auto_cost * 1.7)
                    button_scale["auto"] = 1.2

            # RESOURCE CLICK
            else:
                dx = mouse_pos[0] - resource_pos[0]
                dy = mouse_pos[1] - resource_pos[1]

                if dx * dx + dy * dy < resource_radius ** 2:
                    print("Resource clicked")  # DEBUG

                    resources += click_power
                    click_effects.append([resource_pos[0], resource_pos[1], 1.0])
                    respawn_resource()
                    resource_scale = 1.5
                    shake_time = 0.1   


    # INPUT 
    keys = pygame.key.get_pressed()
    move_player(keys)



    # Clamp player
    player_pos[0] = max(15, min(WIDTH - 15, player_pos[0]))
    player_pos[1] = max(15, min(HEIGHT - 15, player_pos[1]))



    # AUTO INCOME
    resources += auto_income * dt

    # SMOOTH ANIMATIONNS

    resource_scale += (1.0 - resource_scale) * 5 * dt
    for key in button_scale:
        button_scale[key] += (1.0 - button_scale[key]) * 8 * dt



    # DRAW PLAYER

    pygame.draw.circle(
        screen, BLUE,
        (player_pos[0] + offset_x, player_pos[1] + offset_y),
        15
    )

    # DRAW RESOURCE
    scaled_radius =  int(resource_radius * resource_scale)

    pygame.draw.circle(
        screen, GREEN,
        ( resource_pos[0] + offset_x, resource_pos[1] + offset_y),
        scaled_radius
    )


    # DRAW BUTTONS 

    draw_button(upgrade_button, f"Upgrade ({upgrade_cost})", "upgrade")
    draw_button(auto_button, f"Auto ({auto_cost})", "auto")

    # FLOATING   TEXT

    for effect in click_effects[:]:
        effect[1] -= 60 * dt
        effect[2] -= dt

        alpha = int(255 * effect[2])
        text_surface = font.render(f"+{click_power}", True, WHITE)
        text_surface.set_alpha(alpha)

        screen.blit(text_surface, (effect[0], effect[1]))

        if effect[2] <= 0:
            click_effects.remove(effect)




    # UI

    draw_text(f"Resources: {int(resources)}", 10, 10)
    draw_text(f"Click Power: {click_power}", 10, 40)
    draw_text(f"Auto Income: {auto_income}/sec", 10, 70)

    pygame.display.flip()

pygame.quit()
sys.exit()