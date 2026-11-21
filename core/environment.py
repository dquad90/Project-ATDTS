"""
Battlefield Simulation Environment.
Manages game state, entity lifecycles, wave progression, scenario scripting,
and real-time dual-arena side-by-side comparative benchmarking with synchronized mirrored waves.
"""

import math
import random
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import pygame

from core.entities import (
    Base, Tower, Enemy, Projectile, Particle, FloatingText,
    ENEMY_DATABASE, CYAN, ORANGE, PURPLE, CRIMSON, RED, WHITE
)
from core.agent import TargetingStrategy
from core.sound import SoundManager
from scenarios.presets import ALL_SCENARIOS, ScenarioInfo


class BattlefieldEnvironment:
    """
    Simulated 2D base-defence environment representing the Clash of Clans-style
    battlefield specified in PEAS and Section 7 Methodology.
    """

    def __init__(self, width: int = 1000, height: int = 1000, sfx: Optional[SoundManager] = None):
        self.width = width
        self.height = height
        self.base_x = width // 2
        self.base_y = height // 2
        self.sfx = sfx

        self.base: Base = Base(self.base_x, self.base_y, hp=10000.0)
        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []

        self.game_time: int = 0
        self.is_paused: bool = False
        self.game_speed: int = 1
        self.shake_frames: int = 0

        # Wave state machine
        self.wave_state: str = "WAITING"
        self.wave_number: int = 1
        self.enemies_spawned: int = 0
        self.spawn_interval: int = 1200
        self.wave_cooldown: int = 4000
        self.last_spawn_time: int = 0
        self.wave_timer_start: int = 0
        self.enemies_per_wave: int = 10

        # Scenario mode
        self.current_scenario: Optional[ScenarioInfo] = None
        self.scenario_finished: bool = False
        self.scenario_countdown_ms: int = 0

        # Metrics for evaluation
        self.total_enemies_killed: int = 0
        self.bosses_killed: int = 0
        self.total_base_damage_taken: float = 0.0

        self.init_default_defense()

    def trigger_shake(self, frames: int):
        self.shake_frames = max(self.shake_frames, frames)

    def init_default_defense(self, global_strategy: TargetingStrategy = TargetingStrategy.UTILITY_AI):
        """Initializes the 4 canonical towers with their report-specified weights."""
        Enemy.reset_counter()
        self.base = Base(self.base_x, self.base_y, hp=10000.0)
        self.enemies.clear()
        self.projectiles.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.wave_state = "WAITING"
        self.current_scenario = None
        self.scenario_finished = False
        self.scenario_countdown_ms = 0

        # 4 Defensive Towers from Signed Report Specification
        self.towers = [
            # 1. Standard Tower (Balanced Report Multipliers)
            Tower(
                name="Standard",
                x=self.base_x - 150, y=self.base_y - 150,
                attack_range=380, color=CYAN,
                weights={'AP': 2.0, 'SPD': 1.5, 'DIST_PROX': 1.0, 'HP': 0.5},
                damage=55, cooldown=400, splash=0, sfx_name="sniper",
                strategy=global_strategy
            ),
            # 2. Artillery Tower (Heavy Threat Focus)
            Tower(
                name="Artillery",
                x=self.base_x + 150, y=self.base_y - 150,
                attack_range=360, color=ORANGE,
                weights={'AP': 3.0, 'SPD': 0.5, 'DIST_PROX': 1.0, 'HP': 1.5},
                damage=260, cooldown=1400, splash=0, sfx_name="artillery",
                strategy=global_strategy
            ),
            # 3. Defender Tower (Perimeter Guardian)
            Tower(
                name="Defender",
                x=self.base_x - 150, y=self.base_y + 150,
                attack_range=300, color=PURPLE,
                weights={'AP': 1.0, 'SPD': 1.0, 'DIST_PROX': 5.0, 'HP': 0.2},
                damage=85, cooldown=600, splash=0, sfx_name="sniper",
                strategy=global_strategy
            ),
            # 4. Mortar Tower (Cluster AoE Bombardment)
            Tower(
                name="Mortar",
                x=self.base_x + 150, y=self.base_y + 150,
                attack_range=410, color=CRIMSON,
                weights={'AP': 1.0, 'SPD': -1.0, 'DIST_PROX': 1.0, 'HP': 0.5, 'cluster': 15.0},
                damage=160, cooldown=2400, splash=105, sfx_name="mortar",
                strategy=global_strategy
            )
        ]

    def set_global_strategy(self, strategy: TargetingStrategy):
        """Applies a uniform targeting strategy to all towers."""
        for tower in self.towers:
            tower.strategy = strategy

    def start_normal_waves(self, wave_number: int = 1):
        """Switches out of scenario mode and starts continuous procedural waves."""
        self.current_scenario = None
        self.scenario_finished = False
        self.scenario_countdown_ms = 0
        self.init_default_defense()
        self.wave_state = "WAITING"
        self.wave_number = wave_number
        self.wave_cooldown = 1800
        # Start first wave in 800ms
        self.wave_timer_start = self.game_time - (self.wave_cooldown - 800)
        self.enemies_spawned = 0
        self.last_spawn_time = 0

    def load_scenario(self, scenario_id: int, strategy: Optional[TargetingStrategy] = None):
        """Loads a predefined tactical scenario (Objective 5)."""
        if scenario_id not in ALL_SCENARIOS:
            return

        scenario = ALL_SCENARIOS[scenario_id]
        strat = strategy if strategy else (self.towers[0].strategy if self.towers else TargetingStrategy.UTILITY_AI)
        self.init_default_defense(global_strategy=strat)
        self.current_scenario = scenario
        self.scenario_finished = False
        self.scenario_countdown_ms = 2500  # 2.5s preparation countdown

        # Generate scenario scripted enemies
        self.enemies = scenario.spawn_generator(self.base_x, self.base_y)
        self.wave_state = "SCENARIO"

    def spawn_random_enemy(self, wave_mult: float) -> Enemy:
        """Spawns an enemy at random perimeter border."""
        edge = random.choice(["top", "bottom", "left", "right"])
        offset = 25
        if edge == "top":
            x, y = random.randint(40, self.width - 40), -offset
        elif edge == "bottom":
            x, y = random.randint(40, self.width - 40), self.height + offset
        elif edge == "left":
            x, y = -offset, random.randint(40, self.height - 40)
        else:
            x, y = self.width + offset, random.randint(40, self.height - 40)

        if wave_mult < 3:
            enemy_type = random.choices(["Scout", "Tank", "Swarm"], weights=[55, 30, 15], k=1)[0]
        else:
            enemy_type = random.choices(["Scout", "Tank", "Boss", "Swarm"], weights=[40, 30, 15, 15], k=1)[0]
        return Enemy(enemy_type, x, y, wave_multiplier=wave_mult)

    def step(self, dt_ms: int, font: Optional[pygame.font.Font] = None):
        """Executes one full simulation step (wave spawner + combat logic)."""
        self.game_time += dt_ms

        # In scenario preparation countdown, keep towers aimed at candidates but hold fire and movement
        if self.scenario_countdown_ms > 0:
            self.scenario_countdown_ms = max(0, self.scenario_countdown_ms - dt_ms)
            for tower in self.towers:
                tower.evaluate_targets(self.enemies)
            return

        # 1. Wave / Spawner State Machine
        if self.base.hp > 0:
            if self.wave_state == "WAITING":
                if self.game_time - self.wave_timer_start > self.wave_cooldown:
                    self.wave_state = "SPAWNING"
                    self.enemies_per_wave = 8 + (self.wave_number * 4)
                    self.spawn_interval = max(280, 1200 - (self.wave_number * 80))
                    # Spawn first enemy immediately on wave start!
                    self.enemies.append(self.spawn_random_enemy(self.wave_number))
                    self.enemies_spawned = 1
                    self.last_spawn_time = self.game_time
            elif self.wave_state == "SPAWNING":
                if self.enemies_spawned >= self.enemies_per_wave:
                    self.wave_state = "CLEANUP"
                elif self.game_time - self.last_spawn_time > self.spawn_interval:
                    self.enemies.append(self.spawn_random_enemy(self.wave_number))
                    self.last_spawn_time = self.game_time
                    self.enemies_spawned += 1
                    if self.enemies_spawned >= self.enemies_per_wave:
                        self.wave_state = "CLEANUP"
            elif self.wave_state == "CLEANUP":
                if not self.enemies:
                    self.wave_state = "WAITING"
                    self.wave_number += 1
                    self.wave_timer_start = self.game_time
            elif self.wave_state == "SCENARIO":
                if not self.enemies:
                    self.scenario_finished = True

        self.step_combat_only(dt_ms, font)

    def step_combat_only(self, dt_ms: int, font: Optional[pygame.font.Font] = None):
        """Executes combat, movement, AI retargeting, and collisions without internal spawner."""
        # 1. Update Enemy Movements and Base Combat
        for enemy in self.enemies:
            old_hp = self.base.hp
            damaged = enemy.update_state(self.base, self.game_time, self.sfx, self.trigger_shake)
            if damaged:
                dmg = old_hp - self.base.hp
                self.total_base_damage_taken += dmg
                if font:
                    self.floating_texts.append(FloatingText(f"-{int(dmg)} BASE", self.base_x, self.base_y - 40, RED, font))

        # 2. Dynamic Retargeting: Tower AI Decision & Attack Execution
        for tower in self.towers:
            if self.base.hp > 0:
                tower.evaluate_targets(self.enemies)
                proj = tower.try_attack(self.game_time, self.sfx)
                if proj:
                    self.projectiles.append(proj)
            else:
                tower.target = None
                tower.action_status = "Disabled"

        # 3. Projectile Motion and Hit Resolution
        for p in self.projectiles:
            p.update()
            if p.hit:
                if p.splash_radius > 0:
                    if self.sfx:
                        self.sfx.play('explosion')
                    self.trigger_shake(5)
                    # AoE splash damage to all enemies within splash radius
                    for e in self.enemies:
                        dist = float(np.linalg.norm(np.array([e.x - p.x, e.y - p.y])))
                        if dist <= p.splash_radius:
                            e.hp -= p.damage
                            if font:
                                self.floating_texts.append(FloatingText(f"-{int(p.damage)}", e.x, e.y - 18, p.color, font))
                    for _ in range(30):
                        self.particles.append(Particle(p.x, p.y, RED, speed=6.0, life=35))
                else:
                    target = p.target
                    if target and target.hp > 0:
                        target.hp -= p.damage
                        if font:
                            self.floating_texts.append(FloatingText(f"-{int(p.damage)}", target.x, target.y - 18, p.color, font))
                    for _ in range(8):
                        self.particles.append(Particle(p.x, p.y, WHITE, speed=3.0, life=18))
                p.hit = False

        # 4. Visual FX updates
        for part in self.particles:
            part.update()
        for ft in self.floating_texts:
            ft.update()

        # 5. Enemy Defeat Handling
        for e in self.enemies:
            if e.hp <= 0:
                self.total_enemies_killed += 1
                if e.name == "Boss":
                    self.bosses_killed += 1
                    self.trigger_shake(12)
                if self.sfx:
                    self.sfx.play('explosion')
                for _ in range(25):
                    self.particles.append(Particle(e.x, e.y, e.color, speed=4.5, life=35))

        # 6. Entity Cleanup
        self.enemies = [e for e in self.enemies if e.hp > 0]
        self.projectiles = [p for p in self.projectiles if p.active]
        self.particles = [p for p in self.particles if p.life > 0]
        self.floating_texts = [ft for ft in self.floating_texts if ft.life > 0]

        for tower in self.towers:
            if tower.target and tower.target not in self.enemies:
                tower.target = None


class DualArenaEnvironment:
    """
    Side-by-Side Dual Battlefield Arena with Synchronized Mirrored Wave Spawning.
    Runs:
      - Left Battlefield (1000x1000): Baseline Nearest-Enemy Heuristic
      - Right Battlefield (1000x1000): Proposed Utility-Based AI Agent
    Enemies spawn continuously in waves like normal, with identical attributes and positions mirrored simultaneously!
    """

    def __init__(self, sfx: Optional[SoundManager] = None):
        self.sfx = sfx
        self.arena_width = 1000
        self.arena_height = 1000

        self.left_env = BattlefieldEnvironment(self.arena_width, self.arena_height, sfx=None)
        self.right_env = BattlefieldEnvironment(self.arena_width, self.arena_height, sfx=sfx)

        self.left_env.set_global_strategy(TargetingStrategy.NEAREST_ENEMY)
        self.right_env.set_global_strategy(TargetingStrategy.UTILITY_AI)

        # Synchronized wave state machine
        self.game_time: int = 0
        self.wave_state: str = "WAITING"
        self.wave_number: int = 1
        self.enemies_spawned: int = 0
        self.enemies_per_wave: int = 8
        self.spawn_interval: int = 850
        self.wave_cooldown: int = 2000
        self.last_spawn_time: int = 0
        self.wave_timer_start: int = 0

        self.current_scenario: Optional[ScenarioInfo] = None
        self.scenario_finished: bool = False
        self.scenario_countdown_ms: int = 0

    def load_scenario(self, scenario_id: int):
        """Loads identical scenario enemies into both arenas."""
        if scenario_id not in ALL_SCENARIOS:
            return

        scenario = ALL_SCENARIOS[scenario_id]
        self.current_scenario = scenario
        self.scenario_finished = False
        self.wave_state = "SCENARIO"
        self.scenario_countdown_ms = 2500

        self.left_env.init_default_defense(global_strategy=TargetingStrategy.NEAREST_ENEMY)
        self.right_env.init_default_defense(global_strategy=TargetingStrategy.UTILITY_AI)

        # Generate scenario enemies once and clone exact copies for right side
        left_enemies = scenario.spawn_generator(self.left_env.base_x, self.left_env.base_y)
        right_enemies = []
        for e in left_enemies:
            re = Enemy(e.name, e.x, e.y, custom_id=e.id)
            re.hp = e.hp
            re.max_hp = e.max_hp
            re.ap = e.ap
            re.speed = e.speed
            right_enemies.append(re)

        self.left_env.enemies = left_enemies
        self.right_env.enemies = right_enemies
        self.left_env.wave_state = "SCENARIO"
        self.right_env.wave_state = "SCENARIO"
        self.left_env.current_scenario = scenario
        self.right_env.current_scenario = scenario
        self.left_env.scenario_countdown_ms = self.scenario_countdown_ms
        self.right_env.scenario_countdown_ms = self.scenario_countdown_ms

    def start_normal_waves(self, wave_number: int = 1):
        """Resets arena to continuous normal wave progression."""
        self.current_scenario = None
        self.scenario_finished = False
        self.scenario_countdown_ms = 0
        self.left_env.init_default_defense(global_strategy=TargetingStrategy.NEAREST_ENEMY)
        self.right_env.init_default_defense(global_strategy=TargetingStrategy.UTILITY_AI)
        self.wave_state = "WAITING"
        self.wave_number = wave_number
        self.wave_cooldown = 1800
        # Start first wave in 800ms
        self.wave_timer_start = self.game_time - (self.wave_cooldown - 800)
        self.enemies_spawned = 0
        self.last_spawn_time = 0
        self.left_env.wave_state = "WAITING"
        self.right_env.wave_state = "WAITING"
        self.left_env.current_scenario = None
        self.right_env.current_scenario = None
        self.left_env.scenario_countdown_ms = 0
        self.right_env.scenario_countdown_ms = 0

    def call_wave_early(self):
        """Calls the next wave immediately during intermission."""
        if self.wave_state == "WAITING":
            self.wave_timer_start = self.game_time - self.wave_cooldown

    def step(self, dt_ms: int, font: Optional[pygame.font.Font] = None):
        """Advances synchronized wave spawning and combat simulation on both sides."""
        self.game_time += dt_ms
        self.left_env.game_time = self.game_time
        self.right_env.game_time = self.game_time

        if self.scenario_countdown_ms > 0:
            self.scenario_countdown_ms = max(0, self.scenario_countdown_ms - dt_ms)
            self.left_env.scenario_countdown_ms = self.scenario_countdown_ms
            self.right_env.scenario_countdown_ms = self.scenario_countdown_ms
            for t in self.left_env.towers:
                t.evaluate_targets(self.left_env.enemies)
            for t in self.right_env.towers:
                t.evaluate_targets(self.right_env.enemies)
            return

        # Synchronized wave spawner for normal continuous waves
        if self.current_scenario is None:
            both_alive = (self.left_env.base.hp > 0 or self.right_env.base.hp > 0)
            if both_alive:
                if self.wave_state == "WAITING":
                    if self.game_time - self.wave_timer_start > self.wave_cooldown:
                        self.wave_state = "SPAWNING"
                        self.enemies_per_wave = 8 + (self.wave_number * 3)
                        self.spawn_interval = max(300, 950 - (self.wave_number * 60))
                        # Spawn first enemy immediately on wave start!
                        e_left = self.left_env.spawn_random_enemy(self.wave_number)
                        e_right = Enemy(e_left.name, e_left.x, e_left.y, wave_multiplier=self.wave_number, custom_id=e_left.id)
                        if self.left_env.base.hp > 0:
                            self.left_env.enemies.append(e_left)
                        if self.right_env.base.hp > 0:
                            self.right_env.enemies.append(e_right)
                        self.enemies_spawned = 1
                        self.last_spawn_time = self.game_time
                elif self.wave_state == "SPAWNING":
                    if self.enemies_spawned >= self.enemies_per_wave:
                        self.wave_state = "CLEANUP"
                    elif self.game_time - self.last_spawn_time > self.spawn_interval:
                        # Spawn identical random enemy mirrored to both sides
                        e_left = self.left_env.spawn_random_enemy(self.wave_number)
                        e_right = Enemy(e_left.name, e_left.x, e_left.y, wave_multiplier=self.wave_number, custom_id=e_left.id)
                        
                        if self.left_env.base.hp > 0:
                            self.left_env.enemies.append(e_left)
                        if self.right_env.base.hp > 0:
                            self.right_env.enemies.append(e_right)

                        self.last_spawn_time = self.game_time
                        self.enemies_spawned += 1
                        if self.enemies_spawned >= self.enemies_per_wave:
                            self.wave_state = "CLEANUP"
                elif self.wave_state == "CLEANUP":
                    # Wave completes when surviving bases have cleared enemies
                    left_done = (not self.left_env.enemies) or (self.left_env.base.hp <= 0)
                    right_done = (not self.right_env.enemies) or (self.right_env.base.hp <= 0)
                    if left_done and right_done:
                        self.wave_state = "WAITING"
                        self.wave_number += 1
                        self.wave_timer_start = self.game_time
                        self.wave_cooldown = 2000

        else:
            # Scenario mode
            self.wave_state = "SCENARIO"
            if not self.left_env.enemies and not self.right_env.enemies:
                self.scenario_finished = True

        # Keep wave states in sync for UI display
        self.left_env.wave_number = self.wave_number
        self.right_env.wave_number = self.wave_number
        self.left_env.wave_state = self.wave_state
        self.right_env.wave_state = self.wave_state

        # Step combat on both sides
        self.left_env.step_combat_only(dt_ms, font)
        self.right_env.step_combat_only(dt_ms, font)
