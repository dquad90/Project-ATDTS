#added multi-tower system with independent target selection and shooting and health bar for central base

import pygame
import math
import sys
import random

# 1. System Constants & Colors
WIDTH, HEIGHT = 800, 600
BASE_X, BASE_Y = WIDTH // 2, HEIGHT // 2
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
GREEN = (100, 200, 100)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
ENEMY_COLORS = {
    "Tank": (150, 100, 100),
    "Scout": (200, 200, 50),
    "Boss": (100, 50, 150)
}

# 2. Game Entities
class Base:
    def __init__(self, x, y, hp):
        self.x = x
        self.y = y
        self.max_hp = hp
        self.hp = hp
        self.radius = 50

    def draw(self, surface, font):
        # Draw the physical base
        pygame.draw.circle(surface, GREEN, (self.x, self.y), self.radius)
        
        # Draw Unique Top-Screen Health Bar
        bar_width = 400
        bar_height = 25
        bar_x = (WIDTH // 2) - (bar_width // 2)
        bar_y = 20
        
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height))
        
        # Color dynamically changes from Green -> Yellow -> Red based on health
        bar_color = GREEN if hp_ratio > 0.5 else YELLOW if hp_ratio > 0.25 else RED
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, bar_width * hp_ratio, bar_height))
        
        # Base HP Text
        hp_text = font.render(f"BASE INTEGRITY: {int(max(0, self.hp))} / {self.max_hp}", True, WHITE)
        text_rect = hp_text.get_rect(center=(WIDTH // 2, bar_y + bar_height // 2))
        surface.blit(hp_text, text_rect)

class Enemy:
    def __init__(self, name, x, y, hp, damage, speed, radius):
        self.name = name
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.damage = damage
        self.speed = speed
        self.radius = radius
        self.color = ENEMY_COLORS[name]
        self.last_attack_time = 0
        self.attack_cooldown = 1000  # Attacks base once per second

    def update_state(self, base, current_time):
        distance = math.hypot(base.x - self.x, base.y - self.y)
        
        # If outside base radius, keep moving
        if distance > self.radius + base.radius:
            angle = math.atan2(base.y - self.y, base.x - self.x)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed
        else:
            # If touching the base, attack it every 1 second (1000ms)
            if current_time - self.last_attack_time > self.attack_cooldown:
                base.hp -= self.damage
                self.last_attack_time = current_time

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        bar_width = 30
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, BLACK, (self.x - 15, self.y - self.radius - 10, bar_width, 5))
        pygame.draw.rect(surface, RED, (self.x - 15, self.y - self.radius - 10, bar_width * hp_ratio, 5))

class Projectile:
    def __init__(self, x, y, target, damage):
        self.x = x
        self.y = y
        self.target = target
        self.speed = 10.0
        self.damage = damage
        self.active = True

    def update(self):
        if self.target.hp <= 0:
            self.active = False
            return

        distance = math.hypot(self.target.x - self.x, self.target.y - self.y)
        if distance < self.target.radius:
            self.target.hp -= self.damage
            self.active = False
        else:
            angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed

    def draw(self, surface):
        if self.active:
            pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), 4)

class Tower:
    def __init__(self, x, y, attack_range):
        self.x = x
        self.y = y
        self.attack_range = attack_range
        self.target = None
        self.attack_damage = 75  # INCREASED DAMAGE (Previously 25)
        self.cooldown = 500
        self.last_shot_time = 0
        self.weights = {
            'damage': 0.5,    
            'health': -0.05,  
            'speed': 2.0,     
            'distance': 1.5   
        }

    def evaluate_targets(self, enemies):
        best_target = None
        highest_score = -float('inf')

        for enemy in enemies:
            distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if distance <= self.attack_range:
                proximity = self.attack_range - distance
                score = (
                    (enemy.damage * self.weights['damage']) +
                    (enemy.hp * self.weights['health']) +
                    (enemy.speed * self.weights['speed']) +
                    (proximity * self.weights['distance'])
                )
                
                if score > highest_score:
                    highest_score = score
                    best_target = enemy

        self.target = best_target

    def try_attack(self, current_time):
        if self.target and (current_time - self.last_shot_time) > self.cooldown:
            self.last_shot_time = current_time
            return Projectile(self.x, self.y, self.target, self.attack_damage)
        return None

    def draw(self, surface):
        pygame.draw.rect(surface, BLUE, (self.x - 15, self.y - 15, 30, 30))
        pygame.draw.circle(surface, BLUE, (self.x, self.y), self.attack_range, 1)
        if self.target:
            pygame.draw.line(surface, RED, (self.x, self.y), (int(self.target.x), int(self.target.y)), 1)

# 3. Spawner System
def spawn_random_enemy():
    edge = random.choice(["top", "bottom", "left", "right"])
    offset = 40 
    
    if edge == "top":
        x, y = random.randint(0, WIDTH), -offset
    elif edge == "bottom":
        x, y = random.randint(0, WIDTH), HEIGHT + offset
    elif edge == "left":
        x, y = -offset, random.randint(0, HEIGHT)
    else: 
        x, y = WIDTH + offset, random.randint(0, HEIGHT)

    enemy_type = random.choices(
        population=["Scout", "Tank", "Boss"],
        weights=[60, 30, 10], 
        k=1
    )[0]

    if enemy_type == "Scout":
        return Enemy("Scout", x, y, hp=100, damage=10, speed=1.5, radius=10)
    elif enemy_type == "Tank":
        return Enemy("Tank", x, y, hp=500, damage=50, speed=0.5, radius=20)
    else:
        return Enemy("Boss", x, y, hp=1000, damage=150, speed=0.3, radius=30)

# 4. Main Engine Loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Utility-Based Target Selector: Base Defense")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    large_font = pygame.font.SysFont(None, 64)

    # Initialize Base with 5000 HP
    base = Base(BASE_X, BASE_Y, hp=5000)

    # Initialize 3 towers
    towers = [
        Tower(BASE_X - 80, BASE_Y + 60, attack_range=200),
        Tower(BASE_X + 80, BASE_Y + 60, attack_range=200),
        Tower(BASE_X, BASE_Y - 90, attack_range=200)
    ]
    
    enemies = []
    projectiles = []
    
    spawn_cooldown = 1500
    last_spawn_time = pygame.time.get_ticks()
    wave_count = 0

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- 1. Spawner Logic (Stops if base is destroyed) ---
        if base.hp > 0 and current_time - last_spawn_time > spawn_cooldown:
            enemies.append(spawn_random_enemy())
            last_spawn_time = current_time
            wave_count += 1
            if spawn_cooldown > 400 and wave_count % 10 == 0:
                spawn_cooldown -= 100

        # --- 2. Entity Updates ---
        for enemy in enemies:
            enemy.update_state(base, current_time)
        
        for tower in towers:
            # Towers stop firing if the base is destroyed
            if base.hp > 0:
                tower.evaluate_targets(enemies)
                new_projectile = tower.try_attack(current_time)
                if new_projectile:
                    projectiles.append(new_projectile)
            else:
                tower.target = None

        for p in projectiles:
            p.update()

        # --- 3. State Cleanup ---
        enemies = [e for e in enemies if e.hp > 0]
        projectiles = [p for p in projectiles if p.active]

        for tower in towers:
            if tower.target not in enemies:
                tower.target = None

        # --- 4. Rendering ---
        screen.fill(WHITE)
        
        # Draw Base and UI Elements
        base.draw(screen, font)

        for tower in towers:
            tower.draw(screen)
        
        for enemy in enemies:
            enemy.draw(screen)
            
        for p in projectiles:
            p.draw(screen)

        # Bottom Left UI Overlay
        screen.blit(font.render(f"Enemies Alive: {len(enemies)}", True, BLACK), (20, HEIGHT - 40))
        screen.blit(font.render(f"Spawn Rate: {spawn_cooldown}ms", True, BLACK), (20, HEIGHT - 20))

        # Game Over Overlay
        if base.hp <= 0:
            game_over_text = large_font.render("BASE DESTROYED", True, RED)
            rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(game_over_text, rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()