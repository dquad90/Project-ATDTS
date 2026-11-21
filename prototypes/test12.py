#window resizing and scaling, added UI buttons for pause, speed, and wave call, added screen shake effect on base hit and boss death 

import pygame
import math
import sys
import random
import os

# 1. System Constants & Colors
# We now separate internal game logic size from the actual window size
GAME_WIDTH, GAME_HEIGHT = 1000, 1000
BASE_X, BASE_Y = GAME_WIDTH // 2, GAME_HEIGHT // 2
FPS = 60

BG_COLOR = (20, 20, 30)
WHITE = (240, 240, 245)
BLACK = (0, 0, 0)
GREEN = (100, 255, 100)
RED = (255, 50, 50)
YELLOW = (255, 255, 150)
CYAN = (50, 255, 255)
ORANGE = (255, 165, 0)
PURPLE = (150, 50, 255)
CRIMSON = (220, 20, 60)
UI_GRAY = (50, 50, 60)

ENEMY_COLORS = {
    "Tank": (200, 80, 80),
    "Scout": (200, 200, 80),
    "Boss": (180, 80, 200)
}

# --- AUDIO MANAGER ---
class SoundManager:
    def __init__(self):
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        self.sounds = {}
        base_dir = os.path.dirname(os.path.abspath(__file__))
        asset_dir = os.path.join(base_dir, 'assets')
        files = {
            'sniper': 'sniper.wav', 
            'artillery': 'artillery.wav', 
            'mortar': 'mortar.wav', 
            'explosion': 'explosion.wav', 
            'base_hit': 'base_hit.wav'
        }
        for name, filename in files.items():
            path = os.path.join(asset_dir, filename)
            if not os.path.exists(path):
                path = os.path.join(base_dir, filename)
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                    self.sounds[name].set_volume(0.4)
                except pygame.error:
                    pass
        if 'base_hit' not in self.sounds and 'explosion' in self.sounds:
            self.sounds['base_hit'] = self.sounds['explosion']

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

# --- UI COMPONENTS ---
class Button:
    def __init__(self, x, y, width, height, text, default_color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.default_color = default_color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface, font):
        color = self.hover_color if self.is_hovered else self.default_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
        
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

# --- ANIMATION CLASSES ---
class Particle:
    def __init__(self, x, y, color, speed, life):
        self.x, self.y = x, y
        self.color = color
        angle = random.uniform(0, math.pi * 2)
        velocity = random.uniform(1, speed)
        self.vx, self.vy = math.cos(angle) * velocity, math.sin(angle) * velocity
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
        self.text, self.x, self.y, self.color, self.font = text, x, y, color, font
        self.life, self.vy = 45, -1.5

    def update(self):
        self.y += self.vy
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            surface.blit(self.font.render(self.text, True, self.color), (self.x, self.y))

# 2. GAME ENTITIES
class Base:
    def __init__(self, x, y, hp):
        self.x, self.y, self.max_hp, self.hp, self.radius = x, y, hp, hp, 70

    def draw(self, surface, current_time):
        pulse = math.sin(current_time * 0.005) * 5
        pygame.draw.circle(surface, GREEN, (self.x, self.y), self.radius + int(pulse), 2)
        pygame.draw.rect(surface, (50, 150, 50), (self.x - 40, self.y - 40, 80, 80))

class Enemy:
    def __init__(self, name, x, y, hp, damage, speed, radius):
        self.name, self.x, self.y, self.hp, self.max_hp = name, x, y, hp, hp
        self.damage, self.speed, self.radius = damage, speed, radius
        self.color = ENEMY_COLORS[name]
        self.last_attack_time = 0
        self.attack_cooldown = 1000

    def update_state(self, base, game_time, sfx, trigger_shake):
        distance = math.hypot(base.x - self.x, base.y - self.y)
        if distance > self.radius + base.radius:
            angle = math.atan2(base.y - self.y, base.x - self.x)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed
        else:
            if game_time - self.last_attack_time > self.attack_cooldown:
                base.hp -= self.damage
                self.last_attack_time = game_time
                sfx.play('base_hit')
                trigger_shake(8)

    def draw(self, surface, game_time):
        wobble = math.sin(game_time * 0.01 * self.speed) * 2
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius + wobble))
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), int(self.radius + wobble), 2)
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, (50, 50, 50), (self.x - self.radius, self.y - self.radius - 12, self.radius * 2, 5))
        pygame.draw.rect(surface, RED, (self.x - self.radius, self.y - self.radius - 12, (self.radius * 2) * hp_ratio, 5))

class Projectile:
    def __init__(self, x, y, target, damage, color, splash_radius=0):
        self.x, self.y, self.target, self.damage, self.color = x, y, target, damage, color
        self.speed, self.active, self.hit, self.splash_radius = 12.0, True, False, splash_radius
        self.trail = []

    def update(self):
        if self.target.hp <= 0:
            if self.splash_radius > 0: self.hit = True 
            self.active = False
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > 5: self.trail.pop(0)

        distance = math.hypot(self.target.x - self.x, self.target.y - self.y)
        if distance < self.target.radius:
            self.hit, self.active = True, False
        else:
            angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed

    def draw(self, surface):
        if self.active:
            for i, pos in enumerate(self.trail):
                pygame.draw.circle(surface, self.color, (int(pos[0]), int(pos[1])), (i + 1) // 2)
            radius = 8 if self.splash_radius > 0 else 4
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), radius)
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), radius + 1, 1)

class Tower:
    def __init__(self, name, x, y, attack_range, color, weights, damage, cooldown, splash=0, sfx_name="sniper"):
        self.name, self.x, self.y, self.attack_range = name, x, y, attack_range
        self.color, self.weights, self.attack_damage = color, weights, damage
        self.cooldown, self.splash_radius, self.sfx_name = cooldown, splash, sfx_name
        self.target, self.last_shot_time, self.muzzle_flash, self.angle = None, 0, 0, 0

    def evaluate_targets(self, enemies):
        best_target, highest_score = None, -float('inf')
        for enemy in enemies:
            distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if distance <= self.attack_range:
                proximity = self.attack_range - distance
                cluster_count = sum(1 for e in enemies if e != enemy and math.hypot(e.x - enemy.x, e.y - enemy.y) <= self.splash_radius) if self.splash_radius > 0 else 0
                
                score = (
                    (enemy.damage * self.weights.get('damage', 0)) +
                    (enemy.hp * self.weights.get('health', 0)) +
                    (enemy.speed * self.weights.get('speed', 0)) +
                    (proximity * self.weights.get('distance', 0)) +
                    (cluster_count * self.weights.get('cluster', 0))
                )
                if score > highest_score:
                    highest_score, best_target = score, enemy
        self.target = best_target

    def try_attack(self, game_time, sfx):
        if self.target and (game_time - self.last_shot_time) > self.cooldown:
            self.last_shot_time = game_time
            self.muzzle_flash = 12 
            sfx.play(self.sfx_name)
            return Projectile(self.x, self.y, self.target, self.attack_damage, self.color, self.splash_radius)
        return None

    def draw(self, surface):
        pygame.draw.circle(surface, (40, 40, 40), (self.x, self.y), self.attack_range, 1)
        pygame.draw.rect(surface, (100, 100, 100), (self.x - 15, self.y - 15, 30, 30))
        pygame.draw.rect(surface, self.color, (self.x - 15, self.y - 15, 30, 30), 3)

        if self.target: self.angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
        else: self.angle += 0.01 

        end_x, end_y = self.x + math.cos(self.angle) * 25, self.y + math.sin(self.angle) * 25
        pygame.draw.line(surface, WHITE, (self.x, self.y), (end_x, end_y), 6)
        pygame.draw.line(surface, self.color, (self.x, self.y), (end_x, end_y), 2)

        if self.muzzle_flash > 0:
            pygame.draw.circle(surface, YELLOW, (int(end_x), int(end_y)), self.muzzle_flash)
            self.muzzle_flash -= 1

# 3. SPAWNER
def spawn_random_enemy(wave_multiplier):
    edge = random.choice(["top", "bottom", "left", "right"])
    offset = 50 
    if edge == "top": x, y = random.randint(0, GAME_WIDTH), -offset
    elif edge == "bottom": x, y = random.randint(0, GAME_WIDTH), GAME_HEIGHT + offset
    elif edge == "left": x, y = -offset, random.randint(0, GAME_HEIGHT)
    else: x, y = GAME_WIDTH + offset, random.randint(0, GAME_HEIGHT)

    enemy_type = random.choices(["Scout", "Tank", "Boss"], weights=[60, 30, 10], k=1)[0]
    hp_mult = 1 + (wave_multiplier * 0.1)
    
    if enemy_type == "Scout": return Enemy("Scout", x, y, hp=100 * hp_mult, damage=10, speed=1.8, radius=12)
    elif enemy_type == "Tank": return Enemy("Tank", x, y, hp=500 * hp_mult, damage=50, speed=0.6, radius=22)
    else: return Enemy("Boss", x, y, hp=1000 * hp_mult, damage=150, speed=0.4, radius=35)

# 4. MAIN ENGINE
def main():
    pygame.init()
    
    # --- RESIZABLE WINDOW SETUP ---
    win_w, win_h = 800, 800  # Default starting window size
    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    # The canvas remains fixed at 1000x1000 for game logic calculations
    canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT)) 
    pygame.display.set_caption("Utility AI: Resizable Window Edition")
    
    clock, sfx = pygame.time.Clock(), SoundManager()
    font = pygame.font.SysFont("impact", 20)
    ui_font = pygame.font.SysFont("arial", 18, bold=True)
    large_font = pygame.font.SysFont("impact", 72)

    # UI Buttons (Anchored using win_w instead of GAME_WIDTH)
    btn_pause = Button(win_w - 120, 70, 100, 40, "PAUSE", UI_GRAY, ORANGE)
    btn_speed = Button(win_w - 120, 120, 100, 40, "1x SPEED", UI_GRAY, GREEN)
    btn_wave = Button(win_w - 120, 170, 100, 40, "CALL WAVE", UI_GRAY, CYAN)
    
    base = Base(BASE_X, BASE_Y, hp=10000)

    towers = [
        Tower("Sniper", BASE_X-150, BASE_Y-150, 450, CYAN, {'speed': 5.0, 'health': -0.1}, 40, 300, 0, "sniper"),
        Tower("Artillery", BASE_X+150, BASE_Y-150, 350, ORANGE, {'damage': 3.0, 'health': 2.0}, 250, 1500, 0, "artillery"),
        Tower("Defender", BASE_X-150, BASE_Y+150, 300, PURPLE, {'distance': 5.0}, 80, 600, 0, "sniper"),
        Tower("Mortar", BASE_X+150, BASE_Y+150, 400, CRIMSON, {'cluster': 15.0, 'speed': -2.0}, 150, 2500, 100, "mortar")
    ]
    
    enemies, projectiles, particles, floating_texts = [], [], [], []
    
    game_time = 0
    is_paused = False
    game_speed = 1
    shake_frames = 0
    
    wave_state, wave_number, enemies_spawned = "WAITING", 1, 0
    spawn_interval, wave_cooldown = 1200, 5000
    last_spawn_time, wave_timer_start = 0, 0

    def trigger_shake(frames):
        nonlocal shake_frames
        shake_frames = max(shake_frames, frames)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        btn_pause.check_hover(mouse_pos)
        btn_speed.check_hover(mouse_pos)
        btn_wave.check_hover(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # --- HANDLE WINDOW RESIZING ---
            elif event.type == pygame.VIDEORESIZE:
                win_w, win_h = event.w, event.h
                # Recreate screen surface with new dimensions
                screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
                # Re-anchor the UI buttons to the new right edge
                btn_pause.rect.x = win_w - 120
                btn_speed.rect.x = win_w - 120
                btn_wave.rect.x = win_w - 120

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_pause.rect.collidepoint(mouse_pos):
                    is_paused = not is_paused
                    btn_pause.text = "RESUME" if is_paused else "PAUSE"
                elif btn_speed.rect.collidepoint(mouse_pos):
                    game_speed = 2 if game_speed == 1 else 1
                    btn_speed.text = "2x SPEED" if game_speed == 2 else "1x SPEED"
                elif btn_wave.rect.collidepoint(mouse_pos) and wave_state == "WAITING":
                    wave_timer_start = game_time - wave_cooldown

        # 2. LOGIC UPDATES
        update_cycles = 0 if is_paused else game_speed
        
        for _ in range(update_cycles):
            game_time += 1000 // FPS 
            
            if base.hp > 0:
                if wave_state == "WAITING":
                    if game_time - wave_timer_start > wave_cooldown:
                        wave_state = "SPAWNING"
                        enemies_per_wave = 10 + (wave_number * 5)
                        spawn_interval = max(250, 1200 - (wave_number * 100))
                        enemies_spawned = 0
                elif wave_state == "SPAWNING":
                    if game_time - last_spawn_time > spawn_interval:
                        enemies.append(spawn_random_enemy(wave_number))
                        last_spawn_time = game_time
                        enemies_spawned += 1
                        if enemies_spawned >= enemies_per_wave:
                            wave_state = "CLEANUP"
                elif wave_state == "CLEANUP":
                    if not enemies:
                        wave_state, wave_number = "WAITING", wave_number + 1
                        wave_timer_start = game_time

            for enemy in enemies:
                enemy.update_state(base, game_time, sfx, trigger_shake)
            
            for tower in towers:
                if base.hp > 0:
                    tower.evaluate_targets(enemies)
                    proj = tower.try_attack(game_time, sfx)
                    if proj: projectiles.append(proj)
                else: tower.target = None

            for p in projectiles:
                p.update()
                if p.hit:
                    if p.splash_radius > 0:
                        sfx.play('explosion')
                        trigger_shake(5)
                        for e in enemies:
                            if math.hypot(e.x - p.x, e.y - p.y) <= p.splash_radius:
                                e.hp -= p.damage
                                floating_texts.append(FloatingText(f"-{p.damage}", e.x, e.y - 20, p.color, ui_font))
                        for _ in range(40):
                            particles.append(Particle(p.x, p.y, RED, speed=7, life=35))
                    else:
                        p.target.hp -= p.damage
                        floating_texts.append(FloatingText(f"-{p.damage}", p.target.x, p.target.y - 20, p.color, ui_font))
                        for _ in range(8): particles.append(Particle(p.x, p.y, WHITE, speed=3, life=20))
                    p.hit = False

            for part in particles: part.update()
            for ft in floating_texts: ft.update()

            for e in enemies:
                if e.hp <= 0:
                    if e.name == "Boss": trigger_shake(12)
                    sfx.play('explosion')
                    for _ in range(30):
                        particles.append(Particle(e.x, e.y, e.color, speed=5, life=40))

            enemies = [e for e in enemies if e.hp > 0]
            projectiles = [p for p in projectiles if p.active]
            particles = [p for p in particles if p.life > 0]
            floating_texts = [ft for ft in floating_texts if ft.life > 0]
            for tower in towers:
                if tower.target not in enemies: tower.target = None

        # 3. RENDERING TO CANVAS (Fixed Internal Resolution)
        canvas.fill(BG_COLOR)
        base.draw(canvas, game_time)
        for tower in towers: tower.draw(canvas)
        for enemy in enemies: enemy.draw(canvas, game_time)
        for p in projectiles: p.draw(canvas)
        for part in particles: part.draw(canvas)
        for ft in floating_texts: ft.draw(canvas)

        # 4. COMPOSITING TO SCREEN
        screen.fill(BLACK) 
        
        # Scale the game canvas to fit the user's current window size
        scaled_canvas = pygame.transform.scale(canvas, (win_w, win_h))
        
        shake_x, shake_y = 0, 0
        if shake_frames > 0:
            shake_x = random.randint(-8, 8)
            shake_y = random.randint(-8, 8)
            shake_frames -= 1
            
        screen.blit(scaled_canvas, (shake_x, shake_y))

        # 5. RENDER STATIC NATIVE UI
        btn_pause.draw(screen, ui_font)
        btn_speed.draw(screen, ui_font)
        if wave_state == "WAITING" and base.hp > 0:
            btn_wave.draw(screen, ui_font)
            
        # Top HUD spans the width of the window
        pygame.draw.rect(screen, UI_GRAY, (0, 0, win_w, 50))
        hp_ratio = max(0, base.hp / base.max_hp)
        bar_color = GREEN if hp_ratio > 0.5 else ORANGE if hp_ratio > 0.25 else RED
        
        # Center the HP bar horizontally based on the current window size
        bar_width = min(400, win_w - 40)
        bar_x = (win_w // 2) - (bar_width // 2)
        pygame.draw.rect(screen, bar_color, (bar_x, 15, bar_width * hp_ratio, 20))
        pygame.draw.rect(screen, WHITE, (bar_x, 15, bar_width, 20), 2)
        
        # Text positioning dynamically anchored
        screen.blit(font.render(f"WAVE {wave_number}", True, WHITE), (20, 15))
        screen.blit(font.render(f"BASE HP: {int(max(0, base.hp))}", True, WHITE), (bar_x + 10, 15))

        # --- MISSING TOWER NAMES & TARGET INFO ---
        # Drawn dynamically relative to the bottom of the window (win_h)
        for i, tower in enumerate(towers):
            target_name = tower.target.name if tower.target else "Patrolling"
            info = font.render(f"[{tower.name}] Target: {target_name}", True, tower.color)
            screen.blit(info, (20, win_h - 130 + (i * 25)))
        # -----------------------------------------

        if base.hp <= 0:
            game_over_text = large_font.render("BASE DESTROYED", True, RED)
            screen.blit(game_over_text, game_over_text.get_rect(center=(win_w//2, win_h//2)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()