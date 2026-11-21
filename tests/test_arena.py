"""
Automated Verification for Arena Dual HP Bars, Aspect Ratio, Mirrored Spawning, and Retractable AI Stats Window.
"""

import os
import sys
import math
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import numpy as np

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.entities import Base, Tower, Enemy
from core.environment import BattlefieldEnvironment, DualArenaEnvironment
from core.agent import TargetingStrategy
from gui.hud import HUD
from gui.telemetry import ExplainableAIDrawer


class TestArenaMode(unittest.TestCase):

    def test_arena_aspect_ratio_and_hp_bar_geometry(self):
        resolutions = [
            (960, 960),
            (1366, 768),
            (1600, 900),
            (1920, 1080),
            (2560, 1440)
        ]
        GAME_WIDTH, GAME_HEIGHT = 1000, 1000
        top_margin = 130
        bottom_margin = 14
        badge_h = 52

        for win_w, win_h in resolutions:
            avail_h = max(200, win_h - top_margin - bottom_margin)
            half_w = (win_w - 24) // 2

            scale_arena = min(half_w / GAME_WIDTH, (avail_h - badge_h) / GAME_HEIGHT)
            render_w_arena = int(GAME_WIDTH * scale_arena)
            render_h_arena = int(GAME_HEIGHT * scale_arena)
            card_w = render_w_arena
            card_h = render_h_arena + badge_h
            card_y = top_margin + (avail_h - card_h) // 2

            # 1. Check exact 1:1 aspect ratio (no horizontal or vertical stretching!)
            self.assertEqual(render_w_arena, render_h_arena, f"Distortion at {win_w}x{win_h}")

            # 2. Check no overlap with scoreboard (scoreboard ends at y=124)
            self.assertGreaterEqual(card_y, 130, f"Scoreboard overlap at {win_w}x{win_h}")

            # 3. Check fits within screen height
            self.assertLessEqual(card_y + card_h, win_h, f"Overflow at {win_w}x{win_h}")

    def test_dual_arena_mirrored_spawning_and_progression(self):
        dual = DualArenaEnvironment(sfx=None)
        dual.start_normal_waves(1)

        self.assertEqual(dual.wave_number, 1)
        self.assertEqual(dual.wave_state, "WAITING")
        self.assertEqual(dual.left_env.enemies, [])
        self.assertEqual(dual.right_env.enemies, [])

        # Step forward 1000ms: should transition to SPAWNING and immediately spawn enemy 1
        for _ in range(60):
            dual.step(16)

        self.assertEqual(dual.wave_state, "SPAWNING")
        self.assertGreaterEqual(len(dual.left_env.enemies), 1)
        self.assertEqual(len(dual.left_env.enemies), len(dual.right_env.enemies))

        e_left = dual.left_env.enemies[0]
        e_right = dual.right_env.enemies[0]

        # Verify mirrored parity
        self.assertEqual(e_left.name, e_right.name)
        self.assertAlmostEqual(e_left.x, e_right.x, places=2)
        self.assertAlmostEqual(e_left.y, e_right.y, places=2)
        self.assertAlmostEqual(e_left.hp, e_right.hp, places=2)
        self.assertAlmostEqual(e_left.ap, e_right.ap, places=2)
        self.assertAlmostEqual(e_left.speed, e_right.speed, places=2)

        # Step through until wave transitions to CLEANUP
        for _ in range(800):
            dual.step(16)
            if dual.wave_state == "CLEANUP":
                break

        self.assertEqual(dual.wave_state, "CLEANUP")

        # Clear remaining enemies artificially to verify wave advance to Wave 2
        dual.left_env.enemies.clear()
        dual.right_env.enemies.clear()
        dual.step(16)

        self.assertEqual(dual.wave_state, "WAITING")
        self.assertEqual(dual.wave_number, 2)

    def test_dual_arena_cleanup_resilience(self):
        """Verify that if one base is eliminated, waves do not get stuck in CLEANUP."""
        dual = DualArenaEnvironment(sfx=None)
        dual.start_normal_waves(1)
        dual.wave_state = "CLEANUP"
        # Suppose left base is dead with lingering enemies, while right base cleared all enemies
        dual.left_env.base.hp = 0
        dual.left_env.enemies.append(Enemy("Tank", 500, 500))
        dual.right_env.base.hp = 8000
        dual.right_env.enemies.clear()

        dual.step(16)
        # Should advance to WAITING for Wave 2 without freezing!
        self.assertEqual(dual.wave_state, "WAITING")
        self.assertEqual(dual.wave_number, 2)

    def test_hud_ai_stats_button_and_scoreboard_hp_bars(self):
        pygame.init()
        screen = pygame.display.set_mode((960, 960))
        hud = HUD(960, 960)
        self.assertIn('explain', hud.buttons)
        self.assertEqual(hud.buttons['explain'].text, "AI STATS")
        self.assertIn("ai stats", hud.buttons['explain'].tooltip.lower())

        # Test scoreboard rendering with HP bars
        left_base = Base(500, 500, 10000)
        right_base = Base(500, 500, 10000)
        left_base.take_damage(2500, 100)
        font = pygame.font.SysFont("arial", 14)
        large_font = pygame.font.SysFont("arial", 24)
        hud.draw_arena_scoreboard(screen, left_base, right_base, 3, 5, font, large_font)
        # Verified drawing without exceptions

    def test_retractable_ai_stats_drawer(self):
        pygame.init()
        towers = [Tower("Standard", 300, 300, 280, (0, 255, 255), {'AP': 2.0, 'SPD': 1.5, 'DIST_PROX': 1.0, 'HP': 0.5}, 42, 450)]
        drawer = ExplainableAIDrawer(960, 960)

        # 1. Closed state: drawer is clean with no edge tab
        self.assertFalse(drawer.is_open)
        self.assertFalse(drawer.is_retracted)
        # Mouse clicks outside do not hit drawer
        handled = drawer.handle_mouse_events((950, 150), mouse_clicked=True, mouse_pressed=False, towers=towers)
        self.assertFalse(handled)

        # Toggle to open (via TAB key or HUD AI STATS button)
        drawer.toggle()
        self.assertTrue(drawer.is_open)
        self.assertFalse(drawer.is_retracted)

        # 2. Retract window: click retract button
        retract_pos = (drawer.retract_btn.rect.centerx, drawer.retract_btn.rect.centery)
        handled = drawer.handle_mouse_events(retract_pos, mouse_clicked=True, mouse_pressed=False, towers=towers)
        self.assertTrue(handled)
        self.assertTrue(drawer.is_retracted)
        # Rect height should be slim title bar
        self.assertEqual(drawer.rect.height, drawer.retracted_h)
        self.assertEqual(drawer.resize_grip_rect.height, 0)  # No resize grip while retracted

        # 3. Expand window back: click expand button
        handled = drawer.handle_mouse_events(retract_pos, mouse_clicked=True, mouse_pressed=False, towers=towers)
        self.assertTrue(handled)
        self.assertFalse(drawer.is_retracted)
        self.assertEqual(drawer.rect.height, drawer.panel_h)
        self.assertGreater(drawer.resize_grip_rect.height, 0)

    def test_scenario_transition_and_scene_6_normal_waves(self):
        """Verifies that after loading a scenario, Scene 6 starts normal waves cleanly."""
        env = BattlefieldEnvironment(1000, 1000, sfx=None)

        # 1. Load Scenario 1
        env.load_scenario(1)
        self.assertEqual(env.wave_state, "SCENARIO")
        self.assertIsNotNone(env.current_scenario)
        self.assertGreater(env.scenario_countdown_ms, 0)
        self.assertFalse(env.scenario_finished)

        # 2. Transition back to normal waves (Scene 6)
        env.start_normal_waves(1)
        self.assertEqual(env.wave_state, "WAITING")
        self.assertIsNone(env.current_scenario)
        self.assertEqual(env.wave_number, 1)
        self.assertEqual(env.scenario_countdown_ms, 0)

        # 3. Step forward 1000ms: normal waves must spawn!
        for _ in range(70):
            env.step(16)

        self.assertEqual(env.wave_state, "SPAWNING")
        self.assertGreaterEqual(len(env.enemies), 1)

    def test_scenario_preparation_countdown_and_aiming(self):
        """Verifies scenario countdown prevents premature combat while towers acquire initial targets."""
        env = BattlefieldEnvironment(1000, 1000, sfx=None)
        env.load_scenario(1)

        initial_hp = env.base.hp
        initial_enemy_count = len(env.enemies)

        # Step forward 500ms (within 2500ms countdown)
        for _ in range(30):
            env.step(16)

        self.assertGreater(env.scenario_countdown_ms, 0)
        # Base takes 0 damage and no projectiles fired during countdown
        self.assertEqual(env.base.hp, initial_hp)
        self.assertEqual(len(env.projectiles), 0)
        self.assertEqual(len(env.enemies), initial_enemy_count)
        # Towers must have evaluated targets
        aimed_towers = [t for t in env.towers if t.target is not None]
        self.assertGreater(len(aimed_towers), 0)


if __name__ == "__main__":
    unittest.main()
