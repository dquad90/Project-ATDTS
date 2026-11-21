"""
Core Game Entities for Clash of Clans-style Base-Defence Battlefield.
Includes Base, Tower, Enemy, Projectile, Particle, and FloatingText.
"""

import math
import random
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pygame

from core.agent import UtilityBasedAgent, TargetingStrategy, CandidateEvaluation

# ---------------------------------------------------------
# Colors & Visual Theme
# ---------------------------------------------------------
WHITE = (245, 245, 250)
BLACK = (0, 0, 0)
GREEN = (80, 240, 100)
RED = (255, 60, 60)
YELLOW = (255, 230, 80)
CYAN = (60, 230, 255)
ORANGE = (255, 160, 40)
PURPLE = (175, 75, 255)
CRIMSON = (230, 30, 70)
GOLD = (255, 215, 0)
GRAY_BAR = (40, 40, 45)

# ---------------------------------------------------------
# Enemy Knowledge Base / Archetype Definitions
# ---------------------------------------------------------
ENEMY_DATABASE: Dict[str, Dict[str, Any]] = {
    "Scout": {
        "name": "Scout",
        "base_hp": 100.0,
        "ap": 10.0,          # Attack Power (AP)
        "speed": 1.8,        # Movement Speed (SPD)
        "radius": 12,
        "color": (210, 210, 70),
        "desc": "Fast reconnaissance runner; low threat alone but distracts towers."
    },
    "Tank": {
        "name": "Tank",
        "base_hp": 500.0,
        "ap": 50.0,
        "speed": 0.65,
        "radius": 22,
        "color": (220, 80, 80),
        "desc": "Armored battering ram; high durability and dangerous base damage."
    },
    "Boss": {
        "name": "Boss",
        "base_hp": 1000.0,
        "ap": 150.0,
        "speed": 0.4,
        "radius": 34,
        "color": (180, 70, 210),
        "desc": "Devastating siege juggernaut; capable of crushing base if not prioritized."
    },
    "Swarm": {
        "name": "Swarm",
        "base_hp": 60.0,
        "ap": 15.0,
        "speed": 2.2,
        "radius": 10,
        "color": (255, 140, 50),
        "desc": "Rapid swarm infantry; dangerous when clustered."
    }
}


# ---------------------------------------------------------
# Visual FX: Particle and Floating Text
# ---------------------------------------------------------
class Particle:
    """Explosion / spark / muzzle FX particle."""
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], speed: float = 4.0, life: int = 30):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        velocity = random.uniform(0.5, speed)
        self.vx = math.cos(angle) * velocity
        self.vy = math.sin(angle) * velocity
        self.life = life
        self.max_life = life
        self.size = random.uniform(2.0, 5.5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size = max(0.5, self.size * 0.94)

    def draw(self, surface: pygame.Surface):
        if self.life > 0:
            alpha_ratio = self.life / self.max_life
            c = (
                int(self.color[0] * alpha_ratio),
                int(self.color[1] * alpha_ratio),
                int(self.color[2] * alpha_ratio)
            )
            pygame.draw.circle(surface, c, (int(self.x), int(self.y)), max(1, int(self.size)))


class FloatingText:
    """Floating combat text showing damage numbers or status messages."""
    def __init__(self, text: str, x: float, y: float, color: Tuple[int, int, int], font: pygame.font.Font, life: int = 40):
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.font = font
        self.life = life
        self.vy = -1.2

    def update(self):
        self.y += self.vy
        self.life -= 1

    def draw(self, surface: pygame.Surface):
        if self.life > 0:
            surf = self.font.render(self.text, True, self.color)
            surface.blit(surf, (int(self.x), int(self.y)))


# ---------------------------------------------------------
# Base (Protected Town Hall)
# ---------------------------------------------------------
class Base:
    """The protected central base inspired by Clash of Clans Town Hall."""
    def __init__(self, x: float, y: float, hp: float = 10000.0):
        self.x = float(x)
        self.y = float(y)
        self.max_hp = hp
        self.hp = hp
        self.radius = 65.0
        self.last_hit_time = -9999

    def take_damage(self, amount: float, game_time: int) -> bool:
        """Applies damage to base. Returns True if destroyed."""
        self.hp = max(0.0, self.hp - amount)
        self.last_hit_time = game_time
        return self.hp <= 0.0

    def draw(self, surface: pygame.Surface, game_time: int, font: Optional[pygame.font.Font] = None):
        pulse = math.sin(game_time * 0.005) * 4.0
        
        # Perimeter shield / danger ring
        hp_ratio = max(0.0, self.hp / self.max_hp)
        shield_color = GREEN if hp_ratio > 0.5 else ORANGE if hp_ratio > 0.25 else RED
        pygame.draw.circle(surface, shield_color, (int(self.x), int(self.y)), int(self.radius + pulse), 2)

        # Core building
        rect_size = 70
        rect = pygame.Rect(int(self.x - rect_size // 2), int(self.y - rect_size // 2), rect_size, rect_size)
        pygame.draw.rect(surface, (40, 110, 60), rect, border_radius=12)
        pygame.draw.rect(surface, shield_color, rect, 3, border_radius=12)

        # Inner fortress cross
        inner_s = 36
        inner_rect = pygame.Rect(int(self.x - inner_s // 2), int(self.y - inner_s // 2), inner_s, inner_s)
        pygame.draw.rect(surface, (25, 75, 40), inner_rect, border_radius=6)
        pygame.draw.circle(surface, shield_color, (int(self.x), int(self.y)), 10)

        # Floating Town Hall Health Bar
        bar_w = 120
        bar_h = 10
        bar_x = int(self.x - bar_w // 2)
        bar_y = int(self.y - self.radius - 20)
        pygame.draw.rect(surface, (20, 22, 28), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        pygame.draw.rect(surface, shield_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h), border_radius=3)
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=3)

        if font:
            hp_txt = font.render(f"BASE HP: {int(max(0, self.hp))}", True, WHITE)
            surface.blit(hp_txt, hp_txt.get_rect(center=(bar_x + bar_w // 2, bar_y - 8)))


# ---------------------------------------------------------
# Enemy Troop
# ---------------------------------------------------------
class Enemy:
    """
    Advancing enemy troop whose multi-attribute state is tracked by the sensor parser:
    - ID (e.g. E-01)
    - AP (Attack Power)
    - SPD (Movement Speed)
    - HP (Current Health)
    - Coordinates (x, y)
    - Distance from base and tower
    """
    _counter = 1

    @classmethod
    def reset_counter(cls):
        cls._counter = 1

    def __init__(self, name: str, x: float, y: float, wave_multiplier: float = 1.0, custom_id: Optional[str] = None):
        if custom_id:
            self.id = custom_id
        else:
            self.id = f"E-{Enemy._counter:02d}"
            Enemy._counter += 1

        archetype = ENEMY_DATABASE[name]
        self.name = name
        self.x = float(x)
        self.y = float(y)
        hp_mult = 1.0 + (wave_multiplier - 1.0) * 0.12
        self.hp = float(archetype["base_hp"] * hp_mult)
        self.max_hp = self.hp
        self.ap = float(archetype["ap"])           # AP attribute
        self.speed = float(archetype["speed"])     # SPD attribute
        self.radius = float(archetype["radius"])
        self.color = archetype["color"]
        self.last_attack_time = -9999
        self.attack_cooldown = 1000                # ms between attacks on base

    def update_state(self, base: Base, game_time: int, sfx: Any, trigger_shake: Any) -> bool:
        """
        Advances toward the base. If in contact with base, inflicts attack power (AP).
        Returns True if enemy damaged the base this tick.
        """
        vec = np.array([base.x - self.x, base.y - self.y], dtype=np.float32)
        dist = float(np.linalg.norm(vec))

        min_dist = self.radius + base.radius
        if dist > min_dist:
            angle = float(np.arctan2(vec[1], vec[0]))
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed
            return False
        else:
            # Reached base! Attack town hall!
            if base.hp > 0 and (game_time - self.last_attack_time > self.attack_cooldown):
                base.take_damage(self.ap, game_time)
                self.last_attack_time = game_time
                if sfx:
                    sfx.play('base_hit')
                if trigger_shake:
                    trigger_shake(8)
                return True
        return False

    def draw(
        self,
        surface: pygame.Surface,
        game_time: int,
        font: Optional[pygame.font.Font] = None,
        show_threat_badge: bool = False,
        rank_label: str = "",
        is_targeted: bool = False,
        target_label: str = "TARGET",
        target_color: Tuple[int, int, int] = (255, 60, 60)
    ):
        wobble = math.sin(game_time * 0.01 * self.speed) * 1.5
        r = int(self.radius + wobble)

        # 1. Pulsing Tactical Reticle & Crosshairs on Body when Targeted
        if is_targeted or rank_label == "#1 TARGET":
            pulse = math.sin(game_time * 0.015) * 2.0
            reticle_r = int(r + 6 + pulse)
            pygame.draw.circle(surface, target_color, (int(self.x), int(self.y)), reticle_r, 2)
            tick = 5
            pygame.draw.line(surface, target_color, (int(self.x), int(self.y - reticle_r - tick)), (int(self.x), int(self.y - reticle_r + 1)), 2)
            pygame.draw.line(surface, target_color, (int(self.x), int(self.y + reticle_r - 1)), (int(self.x), int(self.y + reticle_r + tick)), 2)
            pygame.draw.line(surface, target_color, (int(self.x - reticle_r - tick), int(self.y)), (int(self.x - reticle_r + 1), int(self.y)), 2)
            pygame.draw.line(surface, target_color, (int(self.x + reticle_r - 1), int(self.y)), (int(self.x + reticle_r + tick), int(self.y)), 2)

        # 2. Body circle
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), r, 2)

        # 3. Health bar above enemy
        bar_w = int(self.radius * 2.2)
        bar_h = 5
        bar_x = int(self.x - bar_w // 2)
        bar_y = int(self.y - self.radius - 12)
        hp_ratio = max(0.0, self.hp / self.max_hp)

        pygame.draw.rect(surface, GRAY_BAR, (bar_x, bar_y, bar_w, bar_h))
        hp_color = GREEN if hp_ratio > 0.5 else ORANGE if hp_ratio > 0.25 else RED
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_w, bar_h), 1)

        # 4. Text and Indicators over head
        if font:
            # ID label
            id_text = font.render(self.id, True, WHITE)
            surface.blit(id_text, (bar_x, bar_y - 14))

            # PROMINENT "TARGET" BADGE DIRECTLY OVER ITS HEAD
            if is_targeted or rank_label == "#1 TARGET":
                disp_label = target_label if target_label else ("#1 TARGET" if rank_label == "#1 TARGET" else "TARGET")
                full_text = f"▼ {disp_label}" if not disp_label.startswith("▼") else disp_label
                lbl_surf = font.render(full_text, True, WHITE)
                pad_x, pad_y = 5, 2
                badge_w = lbl_surf.get_width() + pad_x * 2
                badge_h = lbl_surf.get_height() + pad_y * 2
                badge_x = int(self.x - badge_w // 2)
                badge_y = bar_y - 14 - badge_h - 3  # Directly over head above ID!

                # Rounded pill background
                badge_rect = pygame.Rect(badge_x, badge_y, badge_w, badge_h)
                pygame.draw.rect(surface, (18, 20, 28), badge_rect, border_radius=4)
                pygame.draw.rect(surface, target_color, badge_rect, 2, border_radius=4)

                # Downward pointer triangle pointing right at enemy's head
                tri_pts = [
                    (int(self.x - 4), badge_y + badge_h),
                    (int(self.x + 4), badge_y + badge_h),
                    (int(self.x), badge_y + badge_h + 4)
                ]
                pygame.draw.polygon(surface, target_color, tri_pts)

                # Render text inside badge
                surface.blit(lbl_surf, (badge_x + pad_x, badge_y + pad_y))

            elif show_threat_badge and rank_label:
                # Secondary candidate evaluation ranks (#2, #3, etc.)
                badge_color = YELLOW
                badge = font.render(rank_label, True, badge_color)
                surface.blit(badge, (int(self.x + self.radius + 4), int(self.y - 8)))


# ---------------------------------------------------------
# Projectile
# ---------------------------------------------------------
class Projectile:
    """Guided or ballistic projectile fired by towers."""
    def __init__(self, x: float, y: float, target: Enemy, damage: float, color: Tuple[int, int, int], splash_radius: float = 0.0, speed: float = 14.0):
        self.x = float(x)
        self.y = float(y)
        self.target = target
        self.target_last_pos = (float(target.x), float(target.y)) if target else (x, y)
        self.damage = damage
        self.color = color
        self.splash_radius = splash_radius
        self.speed = speed
        self.active = True
        self.hit = False
        self.trail: List[Tuple[float, float]] = []

    def update(self):
        if not self.active:
            return

        if self.target and self.target.hp > 0:
            dest_x, dest_y = self.target.x, self.target.y
            self.target_last_pos = (dest_x, dest_y)
        else:
            dest_x, dest_y = self.target_last_pos

        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)

        diff = np.array([dest_x - self.x, dest_y - self.y], dtype=np.float32)
        dist = float(np.linalg.norm(diff))

        if dist <= self.speed:
            self.x, self.y = dest_x, dest_y
            self.hit = True
            self.active = False
        else:
            angle = float(np.arctan2(diff[1], diff[0]))
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed

    def draw(self, surface: pygame.Surface):
        if self.active:
            for idx, pt in enumerate(self.trail):
                radius = max(1, (idx + 1) // 2)
                pygame.draw.circle(surface, self.color, (int(pt[0]), int(pt[1])), radius)

            p_radius = 8 if self.splash_radius > 0 else 4
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), p_radius)
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), p_radius + 1, 1)


# ---------------------------------------------------------
# Tower (Defensive Weapon Station)
# ---------------------------------------------------------
class Tower:
    """
    Defensive Tower implementing the 5-Stage Agent Architecture:
      - Sensor Parser: Measures enemy attributes & distance D
      - Threat Scorer: Computes score = (w_AP * AP) + (w_SPD * SPD) + (w_DIST_PROX * (1 - D/D_MAX)) + (w_HP * HP)
      - Target Selector Core: Isolates highest priority target
      - Action Executor (Actuator): Aims turret and attacks
    Supports live strategy switching (Utility AI, Nearest Enemy, etc.) for comparative analysis.
    """
    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        attack_range: float,
        color: Tuple[int, int, int],
        weights: Dict[str, float],
        damage: float,
        cooldown: int,
        splash: float = 0.0,
        sfx_name: str = "sniper",
        strategy: TargetingStrategy = TargetingStrategy.UTILITY_AI
    ):
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.attack_range = float(attack_range)    # D_MAX in Report Formula
        self.color = color
        self.weights = weights.copy()
        self.attack_damage = damage
        self.cooldown = cooldown
        self.splash_radius = splash
        self.sfx_name = sfx_name
        self.strategy = strategy

        # Dedicated Utility Agent instance
        self.agent = UtilityBasedAgent(self.weights)

        # Internal state
        self.target: Optional[Enemy] = None
        self.target_score: float = 0.0
        self.action_status: str = "Patrolling"
        self.last_shot_time: int = -9999
        self.muzzle_flash: int = 0
        self.angle: float = 0.0
        self.candidate_records: List[CandidateEvaluation] = []
        self.explanation: str = "Initial setup."
        self.shots_fired: int = 0
        self.total_damage_dealt: float = 0.0

    def update_weights(self, new_weights: Dict[str, float]):
        """Updates weighting configuration dynamically."""
        self.weights.update(new_weights)
        self.agent = UtilityBasedAgent(self.weights)

    def cycle_strategy(self):
        """Cycles through available targeting strategies for instant comparison."""
        strategies = list(TargetingStrategy)
        curr_idx = strategies.index(self.strategy)
        self.strategy = strategies[(curr_idx + 1) % len(strategies)]

    def evaluate_targets(self, enemies: List[Enemy]):
        """Executes the agent detection, scoring, and selection pipeline."""
        target, records, explanation = self.agent.evaluate_all(
            tower_x=self.x,
            tower_y=self.y,
            attack_range=self.attack_range,
            splash_radius=self.splash_radius,
            enemies=enemies,
            strategy=self.strategy
        )
        self.target = target
        self.candidate_records = records
        self.explanation = explanation

        if target and records:
            # Top candidate score
            top_rec = next((r for r in records if r.is_selected), records[0])
            self.target_score = top_rec.total_score
            self.action_status = f"Attack ({target.id})"
        else:
            self.target_score = 0.0
            self.action_status = "Patrolling"

    def try_attack(self, game_time: int, sfx: Any) -> Optional[Projectile]:
        """Tower Actuator: Aims and launches projectile if cooldown has passed."""
        if self.target and self.target.hp > 0 and (game_time - self.last_shot_time > self.cooldown):
            self.last_shot_time = game_time
            self.muzzle_flash = 12
            self.shots_fired += 1
            if sfx:
                sfx.play(self.sfx_name)
            return Projectile(
                self.x, self.y,
                self.target,
                self.attack_damage,
                self.color,
                splash_radius=self.splash_radius
            )
        return None

    def draw(self, surface: pygame.Surface, is_selected: bool = False, show_range: bool = True):
        # Range indicator (Sensor boundary)
        if show_range:
            range_surf = pygame.Surface((int(self.attack_range * 2), int(self.attack_range * 2)), pygame.SRCALPHA)
            pygame.draw.circle(
                range_surf,
                (self.color[0], self.color[1], self.color[2], 25 if is_selected else 12),
                (int(self.attack_range), int(self.attack_range)),
                int(self.attack_range)
            )
            pygame.draw.circle(
                range_surf,
                (self.color[0], self.color[1], self.color[2], 90 if is_selected else 40),
                (int(self.attack_range), int(self.attack_range)),
                int(self.attack_range),
                2 if is_selected else 1
            )
            surface.blit(range_surf, (int(self.x - self.attack_range), int(self.y - self.attack_range)))

        # Tower base platform
        size = 32
        base_rect = pygame.Rect(int(self.x - size // 2), int(self.y - size // 2), size, size)
        pygame.draw.rect(surface, (70, 70, 80), base_rect, border_radius=6)
        pygame.draw.rect(surface, self.color, base_rect, 3 if is_selected else 2, border_radius=6)

        # Barrel rotation toward active target
        if self.target and self.target.hp > 0:
            target_angle = float(np.arctan2(self.target.y - self.y, self.target.x - self.x))
            diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            self.angle += diff * 0.25
        else:
            self.angle += 0.015

        barrel_len = 28
        barrel_x = self.x + math.cos(self.angle) * barrel_len
        barrel_y = self.y + math.sin(self.angle) * barrel_len

        # Targeting laser line to chosen enemy
        if self.target and self.target.hp > 0:
            pygame.draw.line(surface, (self.color[0], self.color[1], self.color[2], 120), (self.x, self.y), (self.target.x, self.target.y), 1)

        # Draw turret cannon
        pygame.draw.line(surface, (190, 190, 205), (self.x, self.y), (barrel_x, barrel_y), 7)
        pygame.draw.line(surface, self.color, (self.x, self.y), (barrel_x, barrel_y), 3)

        # Turret dome
        pygame.draw.circle(surface, (90, 90, 100), (int(self.x), int(self.y)), 10)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 10, 2)

        # Muzzle flash
        if self.muzzle_flash > 0:
            pygame.draw.circle(surface, YELLOW, (int(barrel_x), int(barrel_y)), self.muzzle_flash + 2)
            pygame.draw.circle(surface, WHITE, (int(barrel_x), int(barrel_y)), max(1, self.muzzle_flash - 2))
            self.muzzle_flash -= 1
