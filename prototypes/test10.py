#added mortar tower with AoE splash damage and cluster targeting, added particle effects and floating damage text, added wave system with increasing difficulty

import pygame
import math
import sys
import random

# 1. System Constants & Colors
WIDTH, HEIGHT = 1000, 1000
BASE_X, BASE_Y = WIDTH // 2, HEIGHT // 2
FPS = 60

WHITE = (20, 20, 30)
BLACK = (0, 0, 0)
GREEN = (100, 255, 100)
RED = (255, 50, 50)
YELLOW = (255, 255, 150)
CYAN = (50, 255, 255)       # Sniper
ORANGE = (255, 165, 0)      # Artillery
PURPLE = (150, 50, 255)     # Defender
CRIMSON = (220, 20, 60)     # Mortar (New)

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
        self.size = random.randint(2, 6)

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
        self.life = 45
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
        self.radius = 70

    def draw(self, surface, font, current_time):
        pulse = math.sin(current_time * 0.005) * 5
        pygame.draw.circle(surface, GREEN, (self.x, self.y), self.radius + int(pulse), 2)
        pygame.draw.rect(surface, (50, 150, 50), (self.x - 40, self.y - 40, 80, 80))
        
        bar_width = 400
        bar_height = 20
        bar_x = (WIDTH // 2) - (bar_width // 2)
        bar_y = 20
        
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        bar_color = GREEN if hp_ratio > 0.5 else ORANGE if hp_ratio > 0.25 else RED
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, bar_width * hp_ratio, bar_height))
        
        hp_text = font.render(f"BASE INTEGRITY: {int(max(0, self.hp))} / {self.max_hp}", True, WHITE)
        surface.blit(hp_text, hp_text.get_rect(center=(WIDTH // 2, bar_y + bar_height // 2)))

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
        
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, (50, 50, 50), (self.x - self.radius, self.y - self.radius - 12, self.radius * 2, 5))
        pygame.draw.rect(surface, RED, (self.x - self.radius, self.y - self.radius - 12, (self.radius * 2) * hp_ratio, 5))

class Projectile:
    def __init__(self, x, y, target, damage, color, splash_radius=0):
        self.x = x
        self.y = y
        self.target = target
        self.speed = 12.0
        self.damage = damage
        self.active = True
        self.color = color
        self.splash_radius = splash_radius
        self.trail = []
        self.hit = False # New flag to tell main engine when to apply damage

    def update(self):
        if self.target.hp <= 0:
            if self.splash_radius > 0:
                self.hit = True  # Mortars "airburst" if target dies early
            self.active = False
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > 5: self.trail.pop(0)

        distance = math.hypot(self.target.x - self.x, self.target.y - self.y)
        if distance < self.target.radius:
            self.hit = True
            self.active = False
        else:
            angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed

    def draw(self, surface):
        if self.active:
            for i, pos in enumerate(self.trail):
                pygame.draw.circle(surface, self.color, (int(pos[0]), int(pos[1])), (i + 1) // 2)
            # Mortar shells are drawn larger
            radius = 8 if self.splash_radius > 0 else 4
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), radius)
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), radius + 1, 1)

class Tower:
    # Upgraded init to accept custom damage, cooldown, and splash properties
    def __init__(self, name, x, y, attack_range, color, weights, damage, cooldown, splash_radius=0):
        self.name = name
        self.x = x
        self.y = y
        self.attack_range = attack_range
        self.color = color
        self.weights = weights
        self.target = None
        self.attack_damage = damage
        self.cooldown = cooldown
        self.splash_radius = splash_radius
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
                
                # --- NEW: CLUSTER CALCULATION ---
                cluster_count = 0
                if self.splash_radius > 0:
                    for other in enemies:
                        if other != enemy and math.hypot(other.x - enemy.x, other.y - enemy.y) <= self.splash_radius:
                            cluster_count += 1
                
                # Use .get() to safely fallback to 0 if a tower doesn't care about a certain weight
                score = (
                    (enemy.damage * self.weights.get('damage', 0)) +
                    (enemy.hp * self.weights.get('health', 0)) +
                    (enemy.speed * self.weights.get('speed', 0)) +
                    (proximity * self.weights.get('distance', 0)) +
                    (cluster_count * self.weights.get('cluster', 0)) # Applies AoE priority
                )
                
                if score > highest_score:
                    highest_score = score
                    best_target = enemy
                    
        self.target = best_target

    def try_attack(self, current_time):
        if self.target and (current_time - self.last_shot_time) > self.cooldown:
            self.last_shot_time = current_time
            self.muzzle_flash = 12 
            return Projectile(self.x, self.y, self.target, self.attack_damage, self.color, self.splash_radius)
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
    hp_mult = 1 + (wave_multiplier * 0.1)
    
    if enemy_type == "Scout": return Enemy("Scout", x, y, hp=100 * hp_mult, damage=10, speed=1.8, radius=12)
    elif enemy_type == "Tank": return Enemy("Tank", x, y, hp=500 * hp_mult, damage=50, speed=0.6, radius=22)
    else: return Enemy("Boss", x, y, hp=1000 * hp_mult, damage=150, speed=0.4, radius=35)

# 4. MAIN ENGINE LOOP
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Utility AI: Area of Effect Tactics")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("impact", 20)
    dmg_font = pygame.font.SysFont("arial", 18, bold=True)
    large_font = pygame.font.SysFont("impact", 72)
    wave_font = pygame.font.SysFont("impact", 48)

    base = Base(BASE_X, BASE_Y, hp=10000)

    # --- TOWER CONFIGURATIONS ---
    sniper_weights = {'health': -0.1, 'speed': 5.0, 'distance': 0.5}
    artillery_weights = {'damage': 3.0, 'health': 2.0, 'distance': 0.1}
    defender_weights = {'distance': 5.0}
    
    # The Mortar hates fast things (speed: -2.0) because they dodge AoE, 
    # but LOVES clusters (cluster: 15.0).
    mortar_weights = {'speed': -2.0, 'distance': 0.1, 'cluster': 15.0}

    # Placed in a defensive box formation around the base
    towers = [
        Tower("Sniper", BASE_X - 150, BASE_Y - 150, 450, CYAN, sniper_weights, damage=40, cooldown=300),
        Tower("Artillery", BASE_X + 150, BASE_Y - 150, 350, ORANGE, artillery_weights, damage=250, cooldown=1500),
        Tower("Defender", BASE_X - 150, BASE_Y + 150, 300, PURPLE, defender_weights, damage=80, cooldown=600),
        # New Mortar Tower: Huge AoE (100 radius), massive cooldown (2.5s)
        Tower("Mortar", BASE_X + 150, BASE_Y + 150, 400, CRIMSON, mortar_weights, damage=150, cooldown=2500, splash_radius=100)
    ]
    
    enemies = []
    projectiles = []
    particles = []
    floating_texts = []
    
    wave_state = "WAITING"
    wave_number = 1
    enemies_per_wave = 10
    enemies_spawned = 0
    spawn_interval = 1200
    last_spawn_time = 0
    wave_cooldown_duration = 5000
    wave_timer_start = pygame.time.get_ticks()

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if base.hp > 0:
            if wave_state == "WAITING":
                if current_time - wave_timer_start > wave_cooldown_duration:
                    wave_state = "SPAWNING"
                    enemies_spawned = 0
                    enemies_per_wave = 10 + (wave_number * 5) # Larger swarms to feed the mortar
                    spawn_interval = max(250, 1200 - (wave_number * 100))
            elif wave_state == "SPAWNING":
                if current_time - last_spawn_time > spawn_interval:
                    enemies.append(spawn_random_enemy(wave_number))
                    last_spawn_time = current_time
                    enemies_spawned += 1
                    if enemies_spawned >= enemies_per_wave:
                        wave_state = "CLEANUP"
            elif wave_state == "CLEANUP":
                if len(enemies) == 0:
                    wave_state = "WAITING"
                    wave_number += 1
                    wave_timer_start = current_time

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

        # --- NEW: COMBAT & SPLASH DAMAGE LOGIC ---
        for p in projectiles:
            p.update()
            if p.hit:
                if p.splash_radius > 0:
                    # Apply Area of Effect
                    for e in enemies:
                        if math.hypot(e.x - p.x, e.y - p.y) <= p.splash_radius:
                            e.hp -= p.damage
                            floating_texts.append(FloatingText(f"-{p.damage}", e.x, e.y - 20, p.color, dmg_font))
                    
                    # Massive Explosion Visual
                    for _ in range(40):
                        particles.append(Particle(p.x, p.y, RED, speed=7, life=35))
                        particles.append(Particle(p.x, p.y, ORANGE, speed=4, life=25))
                else:
                    # Apply Single Target
                    p.target.hp -= p.damage
                    floating_texts.append(FloatingText(f"-{p.damage}", p.target.x, p.target.y - 20, p.color, dmg_font))
                    for _ in range(8):
                        particles.append(Particle(p.x, p.y, WHITE, speed=3, life=20))
                
                p.hit = False # Reset to prevent triggering again before cleanup

        for part in particles: part.update()
        for ft in floating_texts: ft.update()

        for e in enemies:
            if e.hp <= 0:
                for _ in range(30):
                    particles.append(Particle(e.x, e.y, e.color, speed=5, life=40))

        enemies = [e for e in enemies if e.hp > 0]
        projectiles = [p for p in projectiles if p.active]
        particles = [p for p in particles if p.life > 0]
        floating_texts = [ft for ft in floating_texts if ft.life > 0]

        for tower in towers:
            if tower.target not in enemies:
                tower.target = None

        screen.fill(WHITE)
        base.draw(screen, font, current_time)
        for tower in towers: tower.draw(screen, current_time)
        for enemy in enemies: enemy.draw(screen, current_time)
        for p in projectiles: p.draw(screen)
        for part in particles: part.draw(screen)
        for ft in floating_texts: ft.draw(screen)

        for i, tower in enumerate(towers):
            target_name = tower.target.name if tower.target else "Patrolling"
            info = font.render(f"[{tower.name}] Target: {target_name}", True, tower.color)
            screen.blit(info, (20, HEIGHT - 130 + (i * 25)))
            
        wave_info = font.render(f"WAVE {wave_number}", True, WHITE)
        screen.blit(wave_info, (20, HEIGHT - 160))

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