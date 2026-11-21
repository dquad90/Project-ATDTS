#test3 shooting added

import pygame
import math
import sys

# 1. System Constants & Colors
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)    # Tower
GREEN = (100, 200, 100)  # Base Area
RED = (255, 50, 50)      # Targeting Laser
YELLOW = (255, 255, 0)   # Projectiles
ENEMY_COLORS = {
    "Tank": (150, 100, 100),
    "Scout": (200, 200, 50),
    "Boss": (100, 50, 150)
}

# 2. Game Entities
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

    def move_towards(self, target_x, target_y):
        # Stop moving if they reach the center
        if math.hypot(target_x - self.x, target_y - self.y) > self.radius + 20:
            angle = math.atan2(target_y - self.y, target_x - self.x)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # Draw HP bar
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
        # If target dies before projectile hits, destroy projectile
        if self.target.hp <= 0:
            self.active = False
            return

        # Move towards target
        distance = math.hypot(self.target.x - self.x, self.target.y - self.y)
        if distance < self.target.radius:  # Hit!
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
        self.attack_damage = 25
        self.cooldown = 500  # milliseconds between shots
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
        # Fire a projectile if we have a target and cooldown has passed
        if self.target and (current_time - self.last_shot_time) > self.cooldown:
            self.last_shot_time = current_time
            return Projectile(self.x, self.y, self.target, self.attack_damage)
        return None

    def draw(self, surface):
        pygame.draw.circle(surface, GREEN, (self.x, self.y), 40)
        pygame.draw.rect(surface, BLUE, (self.x - 15, self.y - 15, 30, 30))
        pygame.draw.circle(surface, BLUE, (self.x, self.y), self.attack_range, 1)
        if self.target:
            pygame.draw.line(surface, RED, (self.x, self.y), (int(self.target.x), int(self.target.y)), 1)

# 3. Main Engine Loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Utility-Based Target Selector: Combat")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    tower = Tower(WIDTH // 2, HEIGHT // 2, attack_range=250)
    
    enemies = [
        Enemy(name="Tank", x=100, y=100, hp=500, damage=50, speed=0.5, radius=20),
        Enemy(name="Scout", x=700, y=150, hp=100, damage=10, speed=1.5, radius=10),
        Enemy(name="Boss", x=400, y=550, hp=1000, damage=150, speed=0.3, radius=30)
    ]
    
    projectiles = []

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- 1. Entity Updates ---
        for enemy in enemies:
            enemy.move_towards(tower.x, tower.y)
        
        tower.evaluate_targets(enemies)
        
        # Tower firing logic
        new_projectile = tower.try_attack(current_time)
        if new_projectile:
            projectiles.append(new_projectile)

        # Update projectiles
        for p in projectiles:
            p.update()

        # --- 2. State Cleanup ---
        # Remove dead enemies and inactive projectiles
        enemies = [e for e in enemies if e.hp > 0]
        projectiles = [p for p in projectiles if p.active]

        # Force tower to drop target if target was killed
        if tower.target not in enemies:
            tower.target = None

        # --- 3. Rendering ---
        screen.fill(WHITE)
        tower.draw(screen)
        
        for enemy in enemies:
            enemy.draw(screen)
            
        for p in projectiles:
            p.draw(screen)

        # UI Overlay
        target_name = tower.target.name if tower.target else "None"
        screen.blit(font.render(f"Target: {target_name} | Enemies Left: {len(enemies)}", True, BLACK), (20, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()