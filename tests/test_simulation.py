"""
Comprehensive Unit & Integration Test Suite for Automated Tower Defence Target Selector.
Covers:
  - PEAS Specification & Sensor Boundaries (Partial Observability)
  - Mathematical correctness of Utility Threat Scoring Formula
  - Decision divergence (Nearest Enemy vs Utility AI)
  - Dynamic Retargeting on death & attribute changes
  - Cluster density AoE calculation
  - Scenario generation & headless execution
"""

import os
import sys
import unittest
from pathlib import Path
import numpy as np

# Headless setup
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

# Ensure PROJECT-Ai is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.entities import Base, Tower, Enemy, Projectile, ENEMY_DATABASE, CYAN, RED
from core.agent import UtilityBasedAgent, TargetingStrategy, CandidateEvaluation
from core.environment import BattlefieldEnvironment
from core.sound import SoundManager
from scenarios.presets import ALL_SCENARIOS


class TestAgentArchitectureAndPEAS(unittest.TestCase):
    """Verifies compliance with PEAS specifications and 7-stage Architecture."""

    def setUp(self):
        Enemy.reset_counter()
        self.weights = {'AP': 2.0, 'SPD': 1.5, 'DIST_PROX': 1.0, 'HP': 0.5, 'cluster': 15.0}
        self.agent = UtilityBasedAgent(self.weights)

    def test_peas_sensors_partial_observability(self):
        """Sensors must only detect enemies strictly within sensor/attack range D <= D_MAX."""
        tower_x, tower_y = 500.0, 500.0
        attack_range = 300.0

        in_range_enemy = Enemy("Scout", 500.0, 600.0)    # Distance = 100px <= 300px
        out_of_range_enemy = Enemy("Tank", 500.0, 900.0) # Distance = 400px > 300px

        enemies = [in_range_enemy, out_of_range_enemy]
        target, records, explanation = self.agent.evaluate_all(
            tower_x, tower_y, attack_range, 0.0, enemies, TargetingStrategy.UTILITY_AI
        )

        self.assertIsNotNone(target)
        self.assertEqual(target.id, in_range_enemy.id)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].enemy_id, in_range_enemy.id)
        self.assertNotIn(out_of_range_enemy.id, [r.enemy_id for r in records])

    def test_utility_threat_scoring_formula(self):
        """Verifies mathematical correctness of score = w_AP*AP + w_SPD*SPD + w_PROX*Prox*100 + w_HP*HP."""
        ap = 50.0
        spd = 1.2
        prox = 0.8  # (1 - D/D_MAX)
        hp = 500.0
        cluster = 2.0

        score, comp = self.agent.compute_threat_score(ap, spd, prox, hp, cluster)

        expected_ap = 2.0 * 50.0          # 100.0
        expected_spd = 1.5 * 1.2          # 1.8
        expected_prox = 1.0 * (0.8 * 100) # 80.0
        expected_hp = 0.5 * 500.0         # 250.0
        expected_cluster = 15.0 * 2.0     # 30.0
        expected_total = expected_ap + expected_spd + expected_prox + expected_hp + expected_cluster # 461.8

        self.assertAlmostEqual(comp.ap_score, expected_ap, places=2)
        self.assertAlmostEqual(comp.spd_score, expected_spd, places=2)
        self.assertAlmostEqual(comp.dist_prox_score, expected_prox, places=2)
        self.assertAlmostEqual(comp.hp_score, expected_hp, places=2)
        self.assertAlmostEqual(comp.cluster_score, expected_cluster, places=2)
        self.assertAlmostEqual(score, expected_total, places=2)

    def test_utility_ai_vs_nearest_decision_divergence(self):
        """
        Directly tests the central hypothesis:
        When a low-threat Scout is close and a high-threat Boss is farther,
        Nearest Enemy MUST select the Scout, and Utility AI MUST select the Boss.
        """
        tower_x, tower_y = 500.0, 500.0
        attack_range = 380.0

        # Scout is 60px from tower
        close_scout = Enemy("Scout", 500.0, 560.0, custom_id="Decoy-Scout")
        # Boss is 200px from tower
        far_boss = Enemy("Boss", 500.0, 700.0, custom_id="Deadly-Boss")

        enemies = [close_scout, far_boss]

        # 1. Nearest Enemy selection
        nearest_target, _, _ = self.agent.evaluate_all(
            tower_x, tower_y, attack_range, 0.0, enemies, TargetingStrategy.NEAREST_ENEMY
        )
        self.assertEqual(nearest_target.id, close_scout.id, "Nearest Enemy must pick closest decoy")

        # 2. Utility-Based AI selection
        utility_target, _, _ = self.agent.evaluate_all(
            tower_x, tower_y, attack_range, 0.0, enemies, TargetingStrategy.UTILITY_AI
        )
        self.assertEqual(utility_target.id, far_boss.id, "Utility AI must pick highest-threat Boss")

    def test_dynamic_retargeting_on_enemy_death(self):
        """When current target dies, agent must dynamically retarget on the next tick."""
        tower = Tower("Standard", 500, 500, 380, CYAN, self.weights, damage=50, cooldown=400)
        e1 = Enemy("Boss", 500, 650, custom_id="Boss-01")
        e2 = Enemy("Tank", 500, 600, custom_id="Tank-01")

        tower.evaluate_targets([e1, e2])
        self.assertEqual(tower.target.id, "Boss-01")

        # Simulate defeat of Boss-01
        e1.hp = 0.0
        tower.evaluate_targets([e1, e2])
        self.assertEqual(tower.target.id, "Tank-01", "Must dynamically retarget to living candidate")

    def test_dynamic_retargeting_on_proximity_change(self):
        """As a unit approaches the base perimeter, its proximity threat increases dynamically."""
        tower = Tower("Defender", 500, 500, 300, CYAN, {'AP': 1.0, 'SPD': 1.0, 'DIST_PROX': 5.0, 'HP': 0.1}, damage=80, cooldown=500)
        scout = Enemy("Scout", 500, 750, custom_id="Approaching-Scout") # D = 250px

        tower.evaluate_targets([scout])
        score_far = tower.target_score

        # Scout moves closer to 50px
        scout.y = 550.0
        tower.evaluate_targets([scout])
        score_near = tower.target_score

        self.assertGreater(score_near, score_far, "Proximity score must increase as distance decreases")

    def test_cluster_density_calculation(self):
        """AoE Mortar tower must calculate cluster count and award cluster score."""
        mortar = Tower("Mortar", 500, 500, 400, RED, self.weights, damage=150, cooldown=2000, splash=100)
        
        # Cluster of 4 enemies around (500, 700)
        c1 = Enemy("Scout", 500, 700, custom_id="C-1")
        c2 = Enemy("Scout", 510, 710, custom_id="C-2")
        c3 = Enemy("Scout", 490, 690, custom_id="C-3")
        c4 = Enemy("Scout", 520, 680, custom_id="C-4")

        # Isolated scout far from cluster at (300, 500)
        isolated = Enemy("Scout", 300, 500, custom_id="Iso")

        mortar.evaluate_targets([c1, c2, c3, c4, isolated])
        
        # C1 has 3 adjacent clustered allies within splash=100
        rec_c1 = next(r for r in mortar.candidate_records if r.enemy_id == "C-1")
        rec_iso = next(r for r in mortar.candidate_records if r.enemy_id == "Iso")

        self.assertEqual(rec_c1.cluster_count, 3)
        self.assertEqual(rec_iso.cluster_count, 0)
        self.assertGreater(rec_c1.total_score, rec_iso.total_score)

    def test_all_scenarios_run_cleanly(self):
        """Verifies all preset test scenarios initialize and step without exception."""
        env = BattlefieldEnvironment(1000, 1000)
        for s_id in ALL_SCENARIOS:
            env.load_scenario(s_id)
            self.assertGreater(len(env.enemies), 0, f"Scenario {s_id} must spawn enemies")
            # Run 30 steps
            for _ in range(30):
                env.step(16)
            self.assertGreaterEqual(env.base.hp, 0.0)

    def test_sound_manager_graceful_fallback(self):
        """Sound manager must safely initialize and handle missing audio gracefully."""
        sfx = SoundManager()
        self.assertTrue(sfx.initialized)
        # Should not raise exception
        sfx.play('sniper')
        sfx.play('nonexistent_sound')
        is_muted = sfx.toggle_mute()
        self.assertTrue(is_muted)


    def test_enemy_target_indicator_over_head(self):
        """Verifies that an enemy targeted by a tower renders target indicator over its head."""
        enemy = Enemy("Tank", 300, 300)
        surface = pygame.Surface((600, 600))
        font = pygame.font.SysFont("arial", 14, bold=True)

        # 1. Test drawing when targeted with target badge over head
        enemy.draw(
            surface,
            game_time=1000,
            font=font,
            is_targeted=True,
            target_label="#1 TARGET",
            target_color=(255, 60, 60)
        )

        # 2. Test drawing when not targeted
        enemy.draw(
            surface,
            game_time=1000,
            font=font,
            is_targeted=False
        )

        # 3. Test render_environment with is_left_arena and is_right_arena
        from main import render_environment
        env = BattlefieldEnvironment(1000, 1000)
        env.load_scenario(1)
        # Advance 1 step so towers lock onto targets
        env.step(16)
        canvas = pygame.Surface((1000, 1000))
        render_environment(env, canvas, 100, font, is_left_arena=True)
        render_environment(env, canvas, 100, font, is_right_arena=True)
        render_environment(env, canvas, 100, font, selected_tower_idx=0, show_threat_badges=True)


if __name__ == "__main__":
    unittest.main()
