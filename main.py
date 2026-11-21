"""
Automated Tower Defence Target Selector (PROJECT-Ai)
Final Project Implementation compliant with CSE 3202 Course Specifications.

Features:
  - 5-Stage Architecture Pipeline & PEAS Specification Compliance
  - Utility-Based AI Agent with Vectorized NumPy Threat Scoring
  - Explainable AI (XAI) Inspector with Real-time Candidate Matrix & Natural Language Rationale
  - Interactive Strategy Switcher (Utility AI vs Nearest Enemy vs Greedy Heuristics)
  - Real-Time AI Weight Tuning (w_AP, w_SPD, w_PROX, w_HP steppers)
  - 5 Calibrated Tactical Test Scenarios + Endless Procedural Defense
  - Dual Arena Side-by-Side Comparison Mode (Nearest vs Utility AI)
  - Audio FX with Procedural Synthesizer Fallback & Responsive Canvas Scaling
"""

import math
import os
import random
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import numpy as np
import pygame

# Set up project path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.entities import (
    Base, Tower, Enemy, Projectile, Particle, FloatingText,
    ENEMY_DATABASE, WHITE, BLACK, GREEN, RED, YELLOW, CYAN, ORANGE, PURPLE, CRIMSON
)
from core.agent import TargetingStrategy, CandidateEvaluation
from core.sound import SoundManager
from core.environment import BattlefieldEnvironment, DualArenaEnvironment
from scenarios.presets import ALL_SCENARIOS, ScenarioInfo
from gui.controls import Button, NumberStepper
from gui.hud import HUD
from gui.telemetry import ExplainableAIDrawer


# ---------------------------------------------------------
# Simulation Constants
# ---------------------------------------------------------
GAME_WIDTH, GAME_HEIGHT = 1000, 1000
BASE_X, BASE_Y = GAME_WIDTH // 2, GAME_HEIGHT // 2
FPS = 60
BG_COLOR = (18, 20, 28)
GRID_COLOR = (26, 30, 42)


def draw_battlefield_grid(surface: pygame.Surface, w: int, h: int):
    """Draws a tactical grid overlay on the battlefield."""
    grid_spacing = 50
    for x in range(0, w, grid_spacing):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, h), 1)
    for y in range(0, h, grid_spacing):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (w, y), 1)


def render_environment(
    env: BattlefieldEnvironment,
    canvas: pygame.Surface,
    game_time: int,
    font: pygame.font.Font,
    selected_tower_idx: int = 0,
    show_threat_badges: bool = False,
    is_left_arena: bool = False,
    is_right_arena: bool = False
):
    """Renders a complete battlefield environment onto a target canvas surface."""
    canvas.fill(BG_COLOR)
    draw_battlefield_grid(canvas, env.width, env.height)

    # 1. Base (Town Hall)
    env.base.draw(canvas, game_time, font=font)

    # 2. Defensive Towers
    for idx, tower in enumerate(env.towers):
        is_sel = (idx == selected_tower_idx)
        tower.draw(canvas, is_selected=is_sel, show_range=True)

    # 3. Advancing Enemies
    curr_tower = env.towers[selected_tower_idx % len(env.towers)] if env.towers else None

    for enemy in env.enemies:
        rank_label = ""
        is_targeted = False
        target_label = "TARGET"
        target_color = (255, 60, 60)

        # Check which towers in this environment are actively targeting this enemy
        targeting_towers = [t for t in env.towers if t.target == enemy and env.base.hp > 0] if env.towers else []

        if is_left_arena:
            # Baseline Nearest Enemy side
            if targeting_towers:
                is_targeted = True
                target_label = "TARGET"
                target_color = (255, 65, 75)  # Crimson for Nearest
        elif is_right_arena:
            # Proposed Utility-Based AI side
            if targeting_towers:
                is_targeted = True
                target_label = "#1 TARGET"
                target_color = (50, 255, 120)  # Neon Green for Utility AI
        else:
            # Single Battlefield Mode
            if curr_tower and curr_tower.target == enemy and env.base.hp > 0:
                is_targeted = True
                target_label = "#1 TARGET"
                target_color = curr_tower.color
            elif targeting_towers:
                is_targeted = True
                target_label = "TARGET"
                target_color = targeting_towers[0].color

        # Candidate ranking info if available
        if curr_tower:
            rec = next((r for r in curr_tower.candidate_records if r.enemy_id == enemy.id), None)
            if rec:
                rank_label = "#1 TARGET" if rec.is_selected else f"#{rec.rank}"

        enemy.draw(
            canvas,
            game_time,
            font=font,
            show_threat_badge=show_threat_badges,
            rank_label=rank_label,
            is_targeted=is_targeted,
            target_label=target_label,
            target_color=target_color
        )

    # 4. Projectiles
    for p in env.projectiles:
        p.draw(canvas)

    # 5. Visual Particles & Floating Combat Text
    for part in env.particles:
        part.draw(canvas)
    for ft in env.floating_texts:
        ft.draw(canvas)


def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    # Window initialization with resizable flag
    win_w, win_h = 960, 960
    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    pygame.display.set_caption("Automated Tower Defence Target Selector — Utility-Based AI Agent")

    clock = pygame.time.Clock()
    sfx = SoundManager(volume=0.35)

    # Load high-readability fonts
    font = pygame.font.SysFont("arial", 15, bold=True)
    ui_font = pygame.font.SysFont("arial", 16, bold=True)
    code_font = pygame.font.SysFont("consolas", 13, bold=True)
    title_font = pygame.font.SysFont("impact", 22)
    large_font = pygame.font.SysFont("impact", 64)

    # Primary game canvas
    canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

    # Core simulation environments
    env = BattlefieldEnvironment(GAME_WIDTH, GAME_HEIGHT, sfx=sfx)
    dual_arena: Optional[DualArenaEnvironment] = None
    arena_mode = False

    # GUI Components
    hud = HUD(win_w, win_h)
    xai_drawer = ExplainableAIDrawer(win_w, win_h)
    xai_drawer.sync_weights_from_tower(env.towers[0])

    # Game loop state
    is_paused = False
    game_speed = 1
    selected_tower_index = 0
    running = True

    # Restart button for game over overlay
    restart_btn = Button(win_w // 2 - 80, win_h // 2 + 50, 160, 44, "RESTART (R)", default_color=(40, 70, 40), hover_color=GREEN)

    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        # Update button hover states
        for b in hud.buttons.values():
            b.check_hover(mouse_pos)
        if env.base.hp <= 0:
            restart_btn.check_hover(mouse_pos)

        # -------------------------------------------------
        # Input & Event Dispatcher
        # -------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                win_w, win_h = max(700, event.w), max(700, event.h)
                screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
                hud.resize(win_w, win_h)
                xai_drawer.resize(win_w, win_h)
                restart_btn.rect.center = (win_w // 2, win_h // 2 + 50)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    is_paused = not is_paused
                    hud.buttons['pause'].text = "RESUME" if is_paused else "PAUSE"

                elif event.key == pygame.K_TAB:
                    xai_drawer.toggle()

                elif event.key == pygame.K_m:
                    muted = sfx.toggle_mute()
                    hud.buttons['mute'].text = "SFX OFF" if muted else "SFX ON"

                elif event.key == pygame.K_c:
                    arena_mode = not arena_mode
                    if arena_mode:
                        dual_arena = DualArenaEnvironment(sfx=sfx)
                        dual_arena.start_normal_waves(wave_number=1)
                    else:
                        dual_arena = None

                elif event.key == pygame.K_t:
                    # Quick cycle targeting strategy for active tower
                    if env.towers:
                        curr_t = env.towers[selected_tower_index % len(env.towers)]
                        curr_t.cycle_strategy()

                elif event.key == pygame.K_r:
                    # Instant Restart
                    if arena_mode and dual_arena:
                        dual_arena.start_normal_waves(1)
                    else:
                        env.start_normal_waves(1)

                elif event.key == pygame.K_w:
                    # Call wave early or skip scenario countdown
                    if arena_mode and dual_arena:
                        if dual_arena.scenario_countdown_ms > 0:
                            dual_arena.scenario_countdown_ms = 0
                            dual_arena.left_env.scenario_countdown_ms = 0
                            dual_arena.right_env.scenario_countdown_ms = 0
                        else:
                            dual_arena.call_wave_early()
                    else:
                        if env.scenario_countdown_ms > 0:
                            env.scenario_countdown_ms = 0
                        elif env.wave_state == "WAITING" and env.base.hp > 0:
                            env.wave_timer_start = env.game_time - env.wave_cooldown

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    # Enter key immediately engages scenario combat without waiting for countdown
                    if arena_mode and dual_arena:
                        dual_arena.scenario_countdown_ms = 0
                        dual_arena.left_env.scenario_countdown_ms = 0
                        dual_arena.right_env.scenario_countdown_ms = 0
                    else:
                        env.scenario_countdown_ms = 0

                # Numeric keys 1-5 for instant test scenario loading
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    s_id = event.key - pygame.K_0
                    if arena_mode and dual_arena:
                        dual_arena.load_scenario(s_id)
                    else:
                        env.load_scenario(s_id)
                    hud.scenario_menu_open = False

                elif event.key == pygame.K_6:
                    if arena_mode and dual_arena:
                        dual_arena.start_normal_waves(1)
                    else:
                        env.start_normal_waves(1)
                    hud.scenario_menu_open = False

        # -------------------------------------------------
        # Mouse Input & Drag / Resize Handling
        # -------------------------------------------------
        mouse_pressed = pygame.mouse.get_pressed()[0]
        active_towers = dual_arena.right_env.towers if (arena_mode and dual_arena) else env.towers
        handled_by_drawer = xai_drawer.handle_mouse_events(mouse_pos, mouse_clicked, mouse_pressed, active_towers)

        # Precompute arena card geometry for mouse picking & rendering
        top_margin = 130
        bottom_margin = 14
        avail_h = max(200, win_h - top_margin - bottom_margin)
        half_w = (win_w - 24) // 2
        badge_h = 52
        scale_arena = min(half_w / GAME_WIDTH, (avail_h - badge_h) / GAME_HEIGHT)
        render_w_arena = int(GAME_WIDTH * scale_arena)
        render_h_arena = int(GAME_HEIGHT * scale_arena)
        card_w = render_w_arena
        card_h = render_h_arena + badge_h
        card_y = top_margin + (avail_h - card_h) // 2
        left_x = 10 + (half_w - card_w) // 2
        right_x = (win_w // 2 + 2) + (half_w - card_w) // 2

        if mouse_clicked and not handled_by_drawer:
                # Top HUD Bar Buttons
                if hud.buttons['pause'].is_clicked(mouse_pos):
                    is_paused = not is_paused
                    hud.buttons['pause'].text = "RESUME" if is_paused else "PAUSE"

                elif hud.buttons['speed'].is_clicked(mouse_pos):
                    game_speed = 2 if game_speed == 1 else (4 if game_speed == 2 else 1)
                    hud.buttons['speed'].text = f"{game_speed}x SPEED"

                elif hud.buttons['mute'].is_clicked(mouse_pos):
                    muted = sfx.toggle_mute()
                    hud.buttons['mute'].text = "SFX OFF" if muted else "SFX ON"

                elif hud.buttons['arena'].is_clicked(mouse_pos):
                    arena_mode = not arena_mode
                    if arena_mode:
                        dual_arena = DualArenaEnvironment(sfx=sfx)
                        dual_arena.start_normal_waves(wave_number=1)
                    else:
                        dual_arena = None

                elif hud.buttons['explain'].is_clicked(mouse_pos):
                    xai_drawer.toggle()

                elif hud.buttons['scenario'].is_clicked(mouse_pos):
                    hud.scenario_menu_open = not hud.scenario_menu_open

                # Scenario modal selections
                elif hud.scenario_menu_open:
                    for s_id in ALL_SCENARIOS:
                        if hud.buttons[f'scen_{s_id}'].is_clicked(mouse_pos):
                            if arena_mode and dual_arena:
                                dual_arena.load_scenario(s_id)
                            else:
                                env.load_scenario(s_id)
                            hud.scenario_menu_open = False
                            break
                    if hud.buttons['scen_endless'].is_clicked(mouse_pos):
                        if arena_mode and dual_arena:
                            dual_arena.start_normal_waves(1)
                        else:
                            env.start_normal_waves(1)
                        hud.scenario_menu_open = False

                # Restart button on Game Over
                elif restart_btn.is_clicked(mouse_pos) and (env.base.hp <= 0 or (arena_mode and dual_arena and (dual_arena.left_env.base.hp <= 0 or dual_arena.right_env.base.hp <= 0))):
                    if arena_mode and dual_arena:
                        dual_arena.start_normal_waves(1)
                    else:
                        env.start_normal_waves(1)

                # Click on a tower in the battlefield to select it
                else:
                    if arena_mode and dual_arena:
                        # Allow selecting Proposed AI towers in right arena
                        right_canvas_x = mouse_pos[0] - right_x
                        right_canvas_y = mouse_pos[1] - (card_y + badge_h)
                        if 0 <= right_canvas_x <= render_w_arena and 0 <= right_canvas_y <= render_h_arena:
                            c_mx = right_canvas_x / scale_arena
                            c_my = right_canvas_y / scale_arena
                            for t_idx, tower in enumerate(dual_arena.right_env.towers):
                                if math.hypot(tower.x - c_mx, tower.y - c_my) <= 35:
                                    selected_tower_index = t_idx
                                    xai_drawer.selected_tower_index = t_idx
                                    xai_drawer.sync_weights_from_tower(tower)
                                    xai_drawer.is_open = True
                                    break
                    else:
                        scale = min(win_w / GAME_WIDTH, win_h / GAME_HEIGHT)
                        render_w = int(GAME_WIDTH * scale)
                        render_h = int(GAME_HEIGHT * scale)
                        offset_x = (win_w - render_w) // 2
                        offset_y = (win_h - render_h) // 2

                        # Convert mouse to canvas coordinates
                        canvas_mx = (mouse_pos[0] - offset_x) / scale
                        canvas_my = (mouse_pos[1] - offset_y) / scale

                        for t_idx, tower in enumerate(env.towers):
                            dist_to_tower = math.hypot(tower.x - canvas_mx, tower.y - canvas_my)
                            if dist_to_tower <= 35:
                                selected_tower_index = t_idx
                                xai_drawer.selected_tower_index = t_idx
                                xai_drawer.sync_weights_from_tower(tower)
                                break

        # -------------------------------------------------
        # Simulation Step Loop (Dynamic Retargeting)
        # -------------------------------------------------
        update_cycles = 0 if is_paused else game_speed
        for _ in range(update_cycles):
            dt_ms = 1000 // FPS
            if arena_mode and dual_arena:
                dual_arena.step(dt_ms, font)
            else:
                env.step(dt_ms, font)

        # -------------------------------------------------
        # Rendering & Compositing
        # -------------------------------------------------
        screen.fill(BLACK)

        if arena_mode and dual_arena:
            # ---------------- Dual Arena Mode (Side-by-Side) ----------------
            # Vertical divider down center
            pygame.draw.line(screen, (70, 50, 95), (win_w // 2, 56), (win_w // 2, win_h - 10), 2)

            # Scoreboard at top
            hud.draw_arena_scoreboard(
                screen,
                dual_arena.left_env.base,
                dual_arena.right_env.base,
                dual_arena.left_env.total_enemies_killed,
                dual_arena.right_env.total_enemies_killed,
                font, large_font
            )

            # Render battlefields onto native 1000x1000 canvases
            left_canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
            right_canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

            render_environment(dual_arena.left_env, left_canvas, dual_arena.game_time, font, is_left_arena=True)
            render_environment(dual_arena.right_env, right_canvas, dual_arena.game_time, font, is_right_arena=True)

            # 1:1 Aspect Ratio Preserving Scaling (render_w_arena == render_h_arena -> perfect circles!)
            scaled_left = pygame.transform.scale(left_canvas, (render_w_arena, render_h_arena))
            scaled_right = pygame.transform.scale(right_canvas, (render_w_arena, render_h_arena))

            # ---- Left Card: Baseline Nearest Enemy ----
            pygame.draw.rect(screen, (22, 18, 26), (left_x, card_y, card_w, card_h), border_radius=6)
            header_left_rect = pygame.Rect(left_x, card_y, card_w, badge_h)
            pygame.draw.rect(screen, (45, 20, 28), header_left_rect, border_top_left_radius=6, border_top_right_radius=6)
            pygame.draw.line(screen, (120, 45, 55), (left_x, card_y + badge_h), (left_x + card_w, card_y + badge_h), 1)

            # Left Title
            l_badge_txt = font.render("⚔ BASELINE: NEAREST ENEMY", True, RED)
            screen.blit(l_badge_txt, l_badge_txt.get_rect(center=(left_x + card_w // 2, card_y + 14)))

            # Left Graphical HP Bar
            left_base = dual_arena.left_env.base
            l_hp_ratio = max(0.0, left_base.hp / left_base.max_hp)
            l_hp_pct = max(0, int(l_hp_ratio * 100))
            l_bar_w = card_w - 24
            l_bar_h = 16
            l_bar_x = left_x + 12
            l_bar_y = card_y + 28
            pygame.draw.rect(screen, (35, 18, 22), (l_bar_x, l_bar_y, l_bar_w, l_bar_h), border_radius=3)
            l_col = GREEN if l_hp_ratio > 0.5 else ORANGE if l_hp_ratio > 0.25 else RED
            pygame.draw.rect(screen, l_col, (l_bar_x, l_bar_y, int(l_bar_w * l_hp_ratio), l_bar_h), border_radius=3)
            pygame.draw.rect(screen, WHITE, (l_bar_x, l_bar_y, l_bar_w, l_bar_h), 1, border_radius=3)
            l_hp_txt = font.render(f"BASE HP: {int(max(0, left_base.hp))} / {int(left_base.max_hp)} ({l_hp_pct}%)", True, WHITE)
            screen.blit(l_hp_txt, l_hp_txt.get_rect(center=(l_bar_x + l_bar_w // 2, l_bar_y + l_bar_h // 2)))

            screen.blit(scaled_left, (left_x, card_y + badge_h))
            pygame.draw.rect(screen, (100, 45, 55), (left_x, card_y, card_w, card_h), 2, border_radius=6)

            # ---- Right Card: Proposed Utility-Based AI ----
            pygame.draw.rect(screen, (18, 24, 22), (right_x, card_y, card_w, card_h), border_radius=6)
            header_right_rect = pygame.Rect(right_x, card_y, card_w, badge_h)
            pygame.draw.rect(screen, (20, 45, 30), header_right_rect, border_top_left_radius=6, border_top_right_radius=6)
            pygame.draw.line(screen, (45, 120, 65), (right_x, card_y + badge_h), (right_x + card_w, card_y + badge_h), 1)

            # Right Title
            r_badge_txt = font.render("⚡ PROPOSED: UTILITY-BASED AI", True, GREEN)
            screen.blit(r_badge_txt, r_badge_txt.get_rect(center=(right_x + card_w // 2, card_y + 14)))

            # Right Graphical HP Bar
            right_base = dual_arena.right_env.base
            r_hp_ratio = max(0.0, right_base.hp / right_base.max_hp)
            r_hp_pct = max(0, int(r_hp_ratio * 100))
            r_bar_w = card_w - 24
            r_bar_h = 16
            r_bar_x = right_x + 12
            r_bar_y = card_y + 28
            pygame.draw.rect(screen, (18, 35, 22), (r_bar_x, r_bar_y, r_bar_w, r_bar_h), border_radius=3)
            r_col = GREEN if r_hp_ratio > 0.5 else ORANGE if r_hp_ratio > 0.25 else RED
            pygame.draw.rect(screen, r_col, (r_bar_x, r_bar_y, int(r_bar_w * r_hp_ratio), r_bar_h), border_radius=3)
            pygame.draw.rect(screen, WHITE, (r_bar_x, r_bar_y, r_bar_w, r_bar_h), 1, border_radius=3)
            r_hp_txt = font.render(f"BASE HP: {int(max(0, right_base.hp))} / {int(right_base.max_hp)} ({r_hp_pct}%)", True, WHITE)
            screen.blit(r_hp_txt, r_hp_txt.get_rect(center=(r_bar_x + r_bar_w // 2, r_bar_y + r_bar_h // 2)))

            screen.blit(scaled_right, (right_x, card_y + badge_h))
            pygame.draw.rect(screen, (45, 120, 65), (right_x, card_y, card_w, card_h), 2, border_radius=6)

        else:
            # ---------------- Standard Mode (Single Battlefield) ----------------
            render_environment(
                env, canvas, env.game_time, font,
                selected_tower_idx=selected_tower_index,
                show_threat_badges=xai_drawer.is_open
            )

            # Preserve aspect ratio (letterbox / pillarbox)
            scale = min(win_w / GAME_WIDTH, win_h / GAME_HEIGHT)
            render_w = int(GAME_WIDTH * scale)
            render_h = int(GAME_HEIGHT * scale)
            offset_x = (win_w - render_w) // 2
            offset_y = (win_h - render_h) // 2

            scaled_canvas = pygame.transform.scale(canvas, (render_w, render_h))

            # Screen shake effect
            shake_x, shake_y = 0, 0
            if env.shake_frames > 0:
                shake_x = random.randint(-7, 7)
                shake_y = random.randint(-7, 7)
                env.shake_frames -= 1

            screen.blit(scaled_canvas, (offset_x + shake_x, offset_y + shake_y))

            # Bottom quick-telemetry strip
            hud.draw_telemetry_strip(screen, env.towers, code_font, xai_drawer.is_open)

        # AI Stats slide-over drawer (accessible in both Single Player and Dual Arena modes!)
        xai_drawer.draw(screen, active_towers, font, code_font)

        # ---------------- Native HUD Overlay ----------------
        if arena_mode and dual_arena:
            active_base = dual_arena.right_env.base
            active_wave_num = dual_arena.wave_number
            active_wave_state = dual_arena.wave_state
            active_scenario = dual_arena.current_scenario
            active_countdown = dual_arena.scenario_countdown_ms
            active_scen_finished = dual_arena.scenario_finished
        else:
            active_base = env.base
            active_wave_num = env.wave_number
            active_wave_state = env.wave_state
            active_scenario = env.current_scenario
            active_countdown = env.scenario_countdown_ms
            active_scen_finished = env.scenario_finished

        hud.draw_top_bar(
            screen,
            active_base,
            active_wave_num,
            active_wave_state,
            active_scenario,
            font,
            title_font,
            is_arena=arena_mode,
            countdown_ms=active_countdown,
            scenario_finished=active_scen_finished
        )

        # In-game scenario preparation countdown & completion banner
        hud.draw_scenario_banner(
            screen,
            active_scenario,
            active_countdown,
            active_scen_finished,
            font,
            is_arena=arena_mode
        )

        # Game Over Screen Overlay
        is_game_over = False
        if arena_mode and dual_arena:
            if dual_arena.left_env.base.hp <= 0 and dual_arena.right_env.base.hp <= 0:
                is_game_over = True
        else:
            if env.base.hp <= 0:
                is_game_over = True

        if is_game_over:
            overlay = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            screen.blit(overlay, (0, 0))

            go_surf = large_font.render("BASE DESTROYED", True, RED)
            screen.blit(go_surf, go_surf.get_rect(center=(win_w // 2, win_h // 2 - 30)))
            restart_btn.rect.center = (win_w // 2, win_h // 2 + 45)
            restart_btn.draw(screen, ui_font)

        # Single display flip and 60 FPS clock tick
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
