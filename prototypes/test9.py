#added larger area and wave system with increasing difficulty, added particle effects and floating damage text

import pygame
import math
import sys
import random

# 1. System Constants & Colors
WIDTH, HEIGHT = 1000, 1000  # Expanded to a larger, square resolution
BASE_X, BASE_Y = WIDTH // 2, HEIGHT // 2
FPS = 60

WHITE = (20, 20, 30)
BLACK = (0, 0, 0)
GREEN = (100, 255, 100)
RED = (255, 50, 50)
YELLOW = (255, 255, 150)
CYAN = (50, 255, 255)
ORANGE = (255, 165, 0)
PURPLE = (150, 50, 255)

ENEMY_COLORS = {
    "Tank": (200, 80, 80),
    "Scout": (200, 200, 80),
    "Boss": (180, 80, 200)
}

# --- ANIMATION CLASSES ---
class Particle:
    def __init__(self, x, y, color, speed, life):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, math.pi * 2)
        velocity = random.uniform(1, speed)
        self.vx = math.cos(angle) * velocity
        self.vy = math.sin(angle) * velocity
        self.life = life
        self.max_life = life
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size = max(0, self.size * 0.95)

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class FloatingText:
    def __init__(self, text, x, y, color, font):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.life = 60
        self.vy = -1.5

    def update(self):
        self.y += self.vy
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            text_surf = self.font.render(self.text, True, self.color)
            surface.blit(text_surf, (self.x, self.y))

# 2. GAME ENTITIES
class Base:
    def __init__(self, x, y, hp):
        self.x = x
        self.y = y
        self.max_hp = hp
        self.hp = hp
        self.radius = 70  # Increased size for the larger map
        self.pulse = 0

    def draw(self, surface, font, current_time):
        self.pulse = math.sin(current_time * 0.005) * 5
        
        pygame.draw.circle(surface, GREEN, (self.x, self.y), self.radius + int(self.pulse), 2)
        pygame.draw.rect(surface, (50, 150, 50), (self.x - 40, self.y - 40, 80, 80)) # Square core
        
        # Health Bar
        bar_width = 400
        bar_height = 20
        bar_x = (WIDTH // 2) - (bar_width // 2)
        bar_y = 20
        
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        bar_color = GREEN if hp_ratio > 0.5 else ORANGE if hp_ratio > 0.25 else RED
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, bar_width * hp_ratio, bar_height))
        
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
        self.attack_cooldown = 1000

    def update_state(self, base, current_time):
        distance = math.hypot(base.x - self.x, base.y - self.y)
        
        if distance > self.radius + base.radius:
            angle = math.atan2(base.y - self.y, base.x - self.x)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed
        else:
            if current_time - self.last_attack_time > self.attack_cooldown:
                base.hp -= self.damage
                self.last_attack_time = current_time

    def draw(self, surface, current_time):
        wobble = math.sin(current_time * 0.01 * self.speed) * 2
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius + wobble))
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), int(self.radius + wobble), 2)
        
        bar_width = self.radius * 2
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, (50, 50, 50), (self.x - self.radius, self.y - self.radius - 12, bar_width, 5))
        pygame.draw.rect(surface, RED, (self.x - self.radius, self.y - self.radius - 12, bar_width * hp_ratio, 5))

class Projectile:
    def __init__(self, x, y, target, damage, color):
        self.x = x
        self.y = y
        self.target = target
        self.speed = 15.0
        self.damage = damage
        self.active = True
        self.color = color
        self.trail = []

    def update(self):
        if self.target.hp <= 0:
            self.active = False
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)

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
            for i, pos in enumerate(self.trail):
                size = i + 1
                pygame.draw.circle(surface, self.color, (int(pos[0]), int(pos[1])), size // 2)
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 4)
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 5, 1)

class Tower:
    def __init__(self, name, x, y, attack_range, color, weights):
        self.name = name
        self.x = x
        self.y = y
        self.attack_range = attack_range
        self.color = color
        self.weights = weights
        self.target = None
        self.attack_damage = 75
        self.cooldown = 500
        self.last_shot_time = 0
        self.muzzle_flash = 0
        self.angle = 0

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
            self.muzzle_flash = 10 
            return Projectile(self.x, self.y, self.target, self.attack_damage, self.color)
        return None

    def draw(self, surface, current_time):
        pygame.draw.circle(surface, (40, 40, 40), (self.x, self.y), self.attack_range, 1)
        pygame.draw.rect(surface, (100, 100, 100), (self.x - 15, self.y - 15, 30, 30))
        pygame.draw.rect(surface, self.color, (self.x - 15, self.y - 15, 30, 30), 3)

        if self.target:
            self.angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
        else:
            self.angle += 0.01 

        barrel_length = 25
        end_x = self.x + math.cos(self.angle) * barrel_length
        end_y = self.y + math.sin(self.angle) * barrel_length

        pygame.draw.line(surface, WHITE, (self.x, self.y), (end_x, end_y), 6)
        pygame.draw.line(surface, self.color, (self.x, self.y), (end_x, end_y), 2)

        if self.muzzle_flash > 0:
            pygame.draw.circle(surface, YELLOW, (int(end_x), int(end_y)), self.muzzle_flash)
            self.muzzle_flash -= 1

# 3. SPAWNER SYSTEM
def spawn_random_enemy(wave_multiplier):
    edge = random.choice(["top", "bottom", "left", "right"])
    offset = 50 
    
    if edge == "top": x, y = random.randint(0, WIDTH), -offset
    elif edge == "bottom": x, y = random.randint(0, WIDTH), HEIGHT + offset
    elif edge == "left": x, y = -offset, random.randint(0, HEIGHT)
    else: x, y = WIDTH + offset, random.randint(0, HEIGHT)

    enemy_type = random.choices(["Scout", "Tank", "Boss"], weights=[60, 30, 10], k=1)[0]
    
    # Scale enemy HP slightly with wave number
    hp_mult = 1 + (wave_multiplier * 0.1)
    
    if enemy_type == "Scout": return Enemy("Scout", x, y, hp=100 * hp_mult, damage=10, speed=1.8, radius=12)
    elif enemy_type == "Tank": return Enemy("Tank", x, y, hp=500 * hp_mult, damage=50, speed=0.6, radius=22)
    else: return Enemy("Boss", x, y, hp=1000 * hp_mult, damage=150, speed=0.4, radius=35)

# 4. MAIN ENGINE LOOP
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Utility AI: Waves & Expanded Map")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("impact", 20)
    dmg_font = pygame.font.SysFont("arial", 18, bold=True)
    large_font = pygame.font.SysFont("impact", 72)
    wave_font = pygame.font.SysFont("impact", 48)

    base = Base(BASE_X, BASE_Y, hp=10000)

    sniper_weights = {'damage': 0.1, 'health': -0.1, 'speed': 5.0, 'distance': 0.5}
    artillery_weights = {'damage': 3.0, 'health': 2.0, 'speed': 0.1, 'distance': 0.1}
    defender_weights = {'damage': 0.1, 'health': 0.1, 'speed': 0.1, 'distance': 5.0}

    # Towers pushed further out into the larger 1000x1000 space
    towers = [
        Tower("Sniper", BASE_X - 150, BASE_Y + 100, 350, CYAN, sniper_weights),
        Tower("Artillery", BASE_X + 150, BASE_Y + 100, 350, ORANGE, artillery_weights),
        Tower("Defender", BASE_X, BASE_Y - 150, 300, PURPLE, defender_weights)
    ]
    
    enemies = []
    projectiles = []
    particles = []
    floating_texts = []
    
    # Wave State Machine variables
    wave_state = "WAITING"
    wave_number = 1
    enemies_per_wave = 10
    enemies_spawned = 0
    spawn_interval = 1200
    last_spawn_time = 0
    
    wave_cooldown_duration = 5000  # 5 seconds between waves
    wave_timer_start = pygame.time.get_ticks()

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- WAVE LOGIC ---
        if base.hp > 0:
            if wave_state == "WAITING":
                if current_time - wave_timer_start > wave_cooldown_duration:
                    wave_state = "SPAWNING"
                    enemies_spawned = 0
                    enemies_per_wave = 8 + (wave_number * 3) # Waves get bigger
                    spawn_interval = max(300, 1200 - (wave_number * 80)) # Spawn faster
            
            elif wave_state == "SPAWNING":
                if current_time - last_spawn_time > spawn_interval:
                    enemies.append(spawn_random_enemy(wave_number))
                    last_spawn_time = current_time
                    enemies_spawned += 1
                    
                    if enemies_spawned >= enemies_per_wave:
                        wave_state = "CLEANUP"
            
            elif wave_state == "CLEANUP":
                # Wait until all spawned enemies are dead before starting the cooldown timer
                if len(enemies) == 0:
                    wave_state = "WAITING"
                    wave_number += 1
                    wave_timer_start = current_time

        # --- UPDATES ---
        for enemy in enemies:
            enemy.update_state(base, current_time)
        
        for tower in towers:
            if base.hp > 0:
                tower.evaluate_targets(enemies)
                new_projectile = tower.try_attack(current_time)
                if new_projectile:
                    projectiles.append(new_projectile)
            else:
                tower.target = None

        for p in projectiles:
            p.update()
            if not p.active and p.target.hp > 0: 
                floating_texts.append(FloatingText(f"-{p.damage}", p.target.x, p.target.y - 20, p.color, dmg_font))
                for _ in range(5):
                    particles.append(Particle(p.x, p.y, WHITE, speed=3, life=20))

        for part in particles: part.update()
        for ft in floating_texts: ft.update()

        for e in enemies:
            if e.hp <= 0:
                for _ in range(30):
                    particles.append(Particle(e.x, e.y, e.color, speed=5, life=40))

        # --- CLEANUP ---
        enemies = [e for e in enemies if e.hp > 0]
        projectiles = [p for p in projectiles if p.active]
        particles = [p for p in particles if p.life > 0]
        floating_texts = [ft for ft in floating_texts if ft.life > 0]

        for tower in towers:
            if tower.target not in enemies:
                tower.target = None

        # --- RENDERING ---
        screen.fill(WHITE)
        
        base.draw(screen, font, current_time)

        for tower in towers: tower.draw(screen, current_time)
        for enemy in enemies: enemy.draw(screen, current_time)
        for p in projectiles: p.draw(screen)
        for part in particles: part.draw(screen)
        for ft in floating_texts: ft.draw(screen)

        # UI Overlay
        for i, tower in enumerate(towers):
            target_name = tower.target.name if tower.target else "Patrolling"
            info = font.render(f"[{tower.name}] Target: {target_name}", True, tower.color)
            screen.blit(info, (20, HEIGHT - 100 + (i * 25)))
            
        wave_info = font.render(f"WAVE {wave_number}", True, WHITE)
        screen.blit(wave_info, (20, HEIGHT - 130))

        # Wave Cooldown Announcement
        if wave_state == "WAITING" and base.hp > 0:
            time_left = max(0, (wave_cooldown_duration - (current_time - wave_timer_start)) // 1000)
            announcement = wave_font.render(f"WAVE {wave_number} STARTING IN {time_left}...", True, YELLOW)
            rect = announcement.get_rect(center=(WIDTH//2, HEIGHT//2 + 150))
            screen.blit(announcement, rect)

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