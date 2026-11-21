#improved animation

import pygame
import math
import sys
import random

# 1. System Constants & Colors
WIDTH, HEIGHT = 800, 600
BASE_X, BASE_Y = WIDTH // 2, HEIGHT // 2
FPS = 60

WHITE = (20, 20, 30)      # Darkened background for better contrast
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

# --- NEW ANIMATION CLASSES ---

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
        self.size = max(0, self.size * 0.95) # Shrink over time

    def draw(self, surface):
        if self.life > 0:
            # Fade out by calculating alpha (requires drawing to a temp surface, simplified here)
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

# 2. Game Entities
class Base:
    def __init__(self, x, y, hp):
        self.x = x
        self.y = y
        self.max_hp = hp
        self.hp = hp
        self.radius = 50
        self.pulse = 0

    def draw(self, surface, font, current_time):
        # Pulsating effect for the base core
        self.pulse = math.sin(current_time * 0.005) * 5
        
        # Outer shield
        pygame.draw.circle(surface, GREEN, (self.x, self.y), self.radius + int(self.pulse), 2)
        # Inner core
        pygame.draw.circle(surface, (50, 150, 50), (self.x, self.y), self.radius - 10)
        
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
        # Wobble animation based on movement
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
            # Draw Trail
            for i, pos in enumerate(self.trail):
                size = i + 1
                pygame.draw.circle(surface, self.color, (int(pos[0]), int(pos[1])), size // 2)
            # Draw Head
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
            self.muzzle_flash = 10 # Frames of flash
            return Projectile(self.x, self.y, self.target, self.attack_damage, self.color)
        return None

    def draw(self, surface, current_time):
        # Draw attack radius (faint)
        pygame.draw.circle(surface, (40, 40, 40), (self.x, self.y), self.attack_range, 1)
        
        # Tower Base
        pygame.draw.rect(surface, (100, 100, 100), (self.x - 15, self.y - 15, 30, 30))
        pygame.draw.rect(surface, self.color, (self.x - 15, self.y - 15, 30, 30), 3)

        # Turret Rotation Logic
        if self.target:
            target_angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
            self.angle = target_angle # Snap to target
        else:
            self.angle += 0.01 # Idle patrol rotation

        # Calculate barrel end position
        barrel_length = 25
        end_x = self.x + math.cos(self.angle) * barrel_length
        end_y = self.y + math.sin(self.angle) * barrel_length

        # Draw Barrel
        pygame.draw.line(surface, WHITE, (self.x, self.y), (end_x, end_y), 6)
        pygame.draw.line(surface, self.color, (self.x, self.y), (end_x, end_y), 2)

        # Draw Muzzle Flash
        if self.muzzle_flash > 0:
            pygame.draw.circle(surface, YELLOW, (int(end_x), int(end_y)), self.muzzle_flash)
            self.muzzle_flash -= 1

# 3. Spawner System (Unchanged)
def spawn_random_enemy():
    edge = random.choice(["top", "bottom", "left", "right"])
    offset = 50 
    
    if edge == "top": x, y = random.randint(0, WIDTH), -offset
    elif edge == "bottom": x, y = random.randint(0, WIDTH), HEIGHT + offset
    elif edge == "left": x, y = -offset, random.randint(0, HEIGHT)
    else: x, y = WIDTH + offset, random.randint(0, HEIGHT)

    enemy_type = random.choices(["Scout", "Tank", "Boss"], weights=[60, 30, 10], k=1)[0]
    if enemy_type == "Scout": return Enemy("Scout", x, y, hp=100, damage=10, speed=1.8, radius=12)
    elif enemy_type == "Tank": return Enemy("Tank", x, y, hp=500, damage=50, speed=0.6, radius=22)
    else: return Enemy("Boss", x, y, hp=1000, damage=150, speed=0.4, radius=35)

# 4. Main Engine Loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Utility AI: Animated Edition")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("impact", 20)
    dmg_font = pygame.font.SysFont("arial", 18, bold=True)
    large_font = pygame.font.SysFont("impact", 72)

    base = Base(BASE_X, BASE_Y, hp=5000)

    sniper_weights = {'damage': 0.1, 'health': -0.1, 'speed': 5.0, 'distance': 0.5}
    artillery_weights = {'damage': 3.0, 'health': 2.0, 'speed': 0.1, 'distance': 0.1}
    defender_weights = {'damage': 0.1, 'health': 0.1, 'speed': 0.1, 'distance': 5.0}

    towers = [
        Tower("Sniper", BASE_X - 100, BASE_Y + 70, 250, CYAN, sniper_weights),
        Tower("Artillery", BASE_X + 100, BASE_Y + 70, 250, ORANGE, artillery_weights),
        Tower("Defender", BASE_X, BASE_Y - 110, 200, PURPLE, defender_weights)
    ]
    
    enemies = []
    projectiles = []
    particles = []
    floating_texts = []
    
    spawn_cooldown = 1500
    last_spawn_time = pygame.time.get_ticks()
    wave_count = 0

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Spawning
        if base.hp > 0 and current_time - last_spawn_time > spawn_cooldown:
            enemies.append(spawn_random_enemy())
            last_spawn_time = current_time
            wave_count += 1
            if spawn_cooldown > 400 and wave_count % 10 == 0:
                spawn_cooldown -= 100

        # Updates
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
            # If projectile hit target this frame (became inactive)
            if not p.active and p.target.hp > 0: 
                # Spawn damage text
                floating_texts.append(FloatingText(f"-{p.damage}", p.target.x, p.target.y - 20, p.color, dmg_font))
                # Spawn impact particles
                for _ in range(5):
                    particles.append(Particle(p.x, p.y, WHITE, speed=3, life=20))

        for part in particles: part.update()
        for ft in floating_texts: ft.update()

        # Death logic & Particle Explosions
        for e in enemies:
            if e.hp <= 0:
                # Big explosion when enemy dies
                for _ in range(30):
                    particles.append(Particle(e.x, e.y, e.color, speed=5, life=40))

        # Cleanup
        enemies = [e for e in enemies if e.hp > 0]
        projectiles = [p for p in projectiles if p.active]
        particles = [p for p in particles if p.life > 0]
        floating_texts = [ft for ft in floating_texts if ft.life > 0]

        for tower in towers:
            if tower.target not in enemies:
                tower.target = None

        # Rendering
        screen.fill(WHITE) # Now a darker color for visual contrast
        
        base.draw(screen, font, current_time)

        for tower in towers: tower.draw(screen, current_time)
        for enemy in enemies: enemy.draw(screen, current_time)
        for p in projectiles: p.draw(screen)
        for part in particles: part.draw(screen)
        for ft in floating_texts: ft.draw(screen)

        # UI
        for i, tower in enumerate(towers):
            target_name = tower.target.name if tower.target else "Patrolling"
            info = font.render(f"[{tower.name}] Target: {target_name}", True, tower.color)
            screen.blit(info, (20, HEIGHT - 80 + (i * 25)))

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