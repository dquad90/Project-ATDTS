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
        self.damage = damage
        self.speed = speed
        self.radius = radius
        self.color = ENEMY_COLORS[name]

    def move_towards(self, target_x, target_y):
        # Calculate angle and update position
        angle = math.atan2(target_y - self.y, target_x - self.x)
        self.x += math.cos(angle) * self.speed
        self.y += math.sin(angle) * self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # Draw HP bar placeholder
        pygame.draw.rect(surface, BLACK, (self.x - 15, self.y - self.radius - 10, 30, 5))
        pygame.draw.rect(surface, RED, (self.x - 15, self.y - self.radius - 10, 30 * (self.hp/max(self.hp, 1)), 5))

class Tower:
    def __init__(self, x, y, attack_range):
        self.x = x
        self.y = y
        self.attack_range = attack_range
        self.target = None
        self.weights = {
            'damage': 0.5,    
            'health': -0.05,  # Negative weight = prefers weaker enemies
            'speed': 2.0,     
            'distance': 1.5   
        }

    def evaluate_targets(self, enemies):
        best_target = None
        highest_score = -float('inf')

        for enemy in enemies:
            # Calculate distance to tower
            distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
            
            # Only evaluate enemies within attack range
            if distance <= self.attack_range:
                proximity = self.attack_range - distance
                
                # The Utility Formula
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

    def draw(self, surface):
        # Draw Base/Tower structure
        pygame.draw.circle(surface, GREEN, (self.x, self.y), 40)
        pygame.draw.rect(surface, BLUE, (self.x - 15, self.y - 15, 30, 30))
        
        # Draw Attack Range Ring
        pygame.draw.circle(surface, BLUE, (self.x, self.y), self.attack_range, 1)

        # Draw Targeting Laser
        if self.target:
            pygame.draw.line(surface, RED, (self.x, self.y), (int(self.target.x), int(self.target.y)), 3)

# 3. Main Engine Loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Utility-Based Target Selector")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    # Initialize Tower in the center
    tower = Tower(WIDTH // 2, HEIGHT // 2, attack_range=250)

    # Spawn mock enemies outside the range
    enemies = [
        Enemy(name="Tank", x=100, y=100, hp=1000, damage=50, speed=0.5, radius=20),
        Enemy(name="Scout", x=700, y=150, hp=100, damage=10, speed=1.5, radius=10),
        Enemy(name="Boss", x=400, y=550, hp=2000, damage=150, speed=0.3, radius=30)
    ]

    running = True
    while running:
        # 1. Handle Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. Update Game State
        for enemy in enemies:
            enemy.move_towards(tower.x, tower.y)
        
        # The AI decides its target every frame based on updated positions
        tower.evaluate_targets(enemies)

        # 3. Render Graphics
        screen.fill(WHITE)
        tower.draw(screen)
        
        for enemy in enemies:
            enemy.draw(screen)

        # UI Overlay
        if tower.target:
            target_text = font.render(f"Current Target: {tower.target.name}", True, BLACK)
            screen.blit(target_text, (20, 20))
        else:
            idle_text = font.render("Current Target: None (Scanning...)", True, BLACK)
            screen.blit(idle_text, (20, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()