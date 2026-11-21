from dataclasses import dataclass

# 1. Define the Enemy structure
@dataclass
class Enemy:
    name: str
    hp: float
    damage: float
    speed: float
    distance: float  # Distance from the tower

# 2. Define the Utility / Threat scoring function
def calculate_threat_score(enemy: Enemy, weights: dict, max_range: float = 100.0) -> float:
    """
    Calculates a single priority score based on enemy attributes and strategic weights.
    Higher score = higher priority target.
    """
    # For distance, closer is more dangerous. We invert distance so a smaller 
    # distance yields a higher score (e.g., 100 - 20 = 80 threat points).
    proximity = max(0, max_range - enemy.distance)
    
    # Calculate utility formula: U = (w1*D) + (w2*H) + (w3*S) + (w4*Prox)
    score = (
        (enemy.damage * weights['damage']) +
        (enemy.hp * weights['health']) +
        (enemy.speed * weights['speed']) +
        (proximity * weights['distance'])
    )
    return score

# 3. Target Selection Logic
def select_best_target(enemies: list[Enemy], weights: dict) -> Enemy:
    print(f"--- Evaluating Targets ---")
    best_target = None
    highest_score = -float('inf')

    for enemy in enemies:
        score = calculate_threat_score(enemy, weights)
        print(f"[{enemy.name}] Threat Score: {score:.2f} (Dist: {enemy.distance}, Dmg: {enemy.damage})")
        
        if score > highest_score:
            highest_score = score
            best_target = enemy
            
    return best_target

# --- EXECUTION & TESTING ---
if __name__ == "__main__":
    # Mock Battlefield Data: Three different types of enemies
    visible_enemies = [
        Enemy(name="Tank", hp=1000, damage=50, speed=1.0, distance=30),
        Enemy(name="Scout", hp=100, damage=10, speed=5.0, distance=15),
        Enemy(name="Boss", hp=2000, damage=150, speed=0.8, distance=80)
    ]

    # AI Configuration: Adjust these weights to change the tower's "personality"
    ai_weights = {
        'damage': 0.5,    # How much the tower fears high damage
        'health': 0.01,   # How much the tower prioritizes healthy/weak targets
        'speed': 2.0,     # How much the tower fears fast movement
        'distance': 1.5   # How much the tower prioritizes immediate proximity
    }

    # Run the selection
    target = select_best_target(visible_enemies, ai_weights)
    
    print(f"\n>> TARGET SELECTED: {target.name} <<")