"""
HUD Overlay, Telemetry Displays, Top Bar Controls, and Arena Scoreboard.
"""

from typing import Dict, List, Optional, Tuple, Any
import pygame

from core.entities import Base, Tower, WHITE, BLACK, GREEN, RED, YELLOW, CYAN, ORANGE, PURPLE, CRIMSON
from core.agent import TargetingStrategy
from gui.controls import Button
from scenarios.presets import ALL_SCENARIOS, ScenarioInfo

UI_GRAY = (35, 38, 50)
UI_GRAY_BORDER = (65, 70, 90)


class HUD:
    """Manages all persistent HUD overlays, interactive buttons, and telemetry strips."""

    def __init__(self, win_w: int, win_h: int):
        self.win_w = win_w
        self.win_h = win_h
        self.scenario_menu_open = False
        self.buttons = self._init_buttons(win_w, win_h)

    def _init_buttons(self, w: int, h: int) -> Dict[str, Button]:
        top_btn_y = 10
        btn_h = 32
        
        # Right aligned controls
        x_cursor = w - 105
        btns = {
            'explain': Button(x_cursor, top_btn_y, 95, btn_h, "AI STATS", default_color=(35, 65, 110), hover_color=CYAN, text_color=WHITE, tooltip="Open AI Stats & Target Inspector (TAB)"),
        }
        x_cursor -= 105
        btns['arena'] = Button(x_cursor, top_btn_y, 95, btn_h, "ARENA (C)", default_color=(80, 45, 100), hover_color=PURPLE, text_color=WHITE, tooltip="Toggle Side-by-Side Dual Arena (C)")
        
        x_cursor -= 115
        btns['scenario'] = Button(x_cursor, top_btn_y, 105, btn_h, "SCENARIOS", default_color=(45, 80, 60), hover_color=GREEN, text_color=WHITE, tooltip="Select Test Scenarios (1-5)")

        x_cursor -= 95
        btns['speed'] = Button(x_cursor, top_btn_y, 85, btn_h, "1x SPEED", default_color=UI_GRAY, hover_color=YELLOW, text_color=WHITE, tooltip="Cycle Speed: 1x, 2x, 4x")

        x_cursor -= 90
        btns['pause'] = Button(x_cursor, top_btn_y, 80, btn_h, "PAUSE", default_color=UI_GRAY, hover_color=ORANGE, text_color=WHITE, tooltip="Pause / Resume (SPACE)")

        x_cursor -= 75
        btns['mute'] = Button(x_cursor, top_btn_y, 65, btn_h, "SFX ON", default_color=UI_GRAY, hover_color=WHITE, text_color=WHITE, tooltip="Toggle SFX Mute (M)")

        # Scenario menu popup buttons
        menu_y = 52
        for s_id, s_info in ALL_SCENARIOS.items():
            btns[f'scen_{s_id}'] = Button(
                w // 2 - 220, menu_y, 440, 36,
                f"[{s_id}] {s_info.name}: {s_info.subtitle}",
                default_color=(40, 45, 60), hover_color=(60, 100, 140)
            )
            menu_y += 42
        btns['scen_endless'] = Button(
            w // 2 - 220, menu_y, 440, 36,
            "[6] Endless Procedural Wave Defense",
            default_color=(50, 60, 40), hover_color=GREEN
        )

        return btns

    def resize(self, win_w: int, win_h: int):
        self.win_w = win_w
        self.win_h = win_h
        self.buttons = self._init_buttons(win_w, win_h)

    def draw_top_bar(
        self,
        surface: pygame.Surface,
        base: Base,
        wave_number: int,
        wave_state: str,
        current_scenario: Optional[ScenarioInfo],
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        is_arena: bool = False,
        countdown_ms: int = 0,
        scenario_finished: bool = False
    ):
        # Top banner background
        bar_h = 52
        pygame.draw.rect(surface, (20, 22, 30), (0, 0, self.win_w, bar_h))
        pygame.draw.line(surface, UI_GRAY_BORDER, (0, bar_h), (self.win_w, bar_h), 2)

        # Mode title / Wave indicator
        if is_arena:
            if current_scenario:
                if countdown_ms > 0:
                    secs = countdown_ms / 1000.0
                    mode_text = f"ARENA: SCENARIO {current_scenario.id} — {current_scenario.name.upper()} [PREPARING: {secs:0.1f}s]"
                    title_surf = title_font.render(mode_text, True, YELLOW)
                elif scenario_finished:
                    mode_text = f"ARENA: SCENARIO {current_scenario.id} — {current_scenario.name.upper()} [COMPLETED]"
                    title_surf = title_font.render(mode_text, True, GREEN)
                else:
                    mode_text = f"ARENA: SCENARIO {current_scenario.id} — {current_scenario.name.upper()}"
                    title_surf = title_font.render(mode_text, True, YELLOW)
            else:
                title_surf = title_font.render(f"ARENA: WAVE {wave_number} [{wave_state}]", True, CYAN)
        else:
            if current_scenario:
                if countdown_ms > 0:
                    secs = countdown_ms / 1000.0
                    mode_text = f"SCENARIO {current_scenario.id}: {current_scenario.name.upper()} [PREPARING: {secs:0.1f}s]"
                    title_surf = title_font.render(mode_text, True, YELLOW)
                elif scenario_finished:
                    mode_text = f"SCENARIO {current_scenario.id}: {current_scenario.name.upper()} [COMPLETED]"
                    title_surf = title_font.render(mode_text, True, GREEN)
                else:
                    mode_text = f"SCENARIO {current_scenario.id}: {current_scenario.name.upper()}"
                    title_surf = title_font.render(mode_text, True, YELLOW)
            else:
                title_surf = title_font.render(f"WAVE {wave_number} [{wave_state}]", True, CYAN)
        surface.blit(title_surf, (20, 14))

        # Base HP Bar (Center - in Single Player Mode only; Arena Mode has scoreboard below)
        if not is_arena:
            hp_ratio = max(0.0, base.hp / base.max_hp)
            bar_w = min(280, self.win_w // 4)
            bar_x = (self.win_w // 2) - (bar_w // 2) - 40
            bar_y = 16
            pygame.draw.rect(surface, (30, 30, 35), (bar_x, bar_y, bar_w, 20), border_radius=4)
            bar_col = GREEN if hp_ratio > 0.5 else ORANGE if hp_ratio > 0.25 else RED
            pygame.draw.rect(surface, bar_col, (bar_x, bar_y, int(bar_w * hp_ratio), 20), border_radius=4)
            pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, 20), 2, border_radius=4)

            hp_text = font.render(f"BASE HP: {int(max(0, base.hp))}", True, WHITE)
            hp_rect = hp_text.get_rect(center=(bar_x + bar_w // 2, bar_y + 10))
            surface.blit(hp_text, hp_rect)
        else:
            # Subtle centered indicator in arena
            arena_tag = font.render("DUAL ARENA: NEAREST ENEMY vs UTILITY AI", True, (160, 140, 200))
            surface.blit(arena_tag, arena_tag.get_rect(center=(self.win_w // 2 - 40, 26)))

        # Draw top controls
        for k in ['mute', 'pause', 'speed', 'scenario', 'arena', 'explain']:
            if k in self.buttons:
                self.buttons[k].draw(surface, font)

        # Draw Scenario selection modal if open
        if self.scenario_menu_open:
            overlay_h = len(ALL_SCENARIOS) * 44 + 80
            modal_rect = pygame.Rect(self.win_w // 2 - 240, 48, 480, overlay_h)
            pygame.draw.rect(surface, (25, 28, 40), modal_rect, border_radius=10)
            pygame.draw.rect(surface, CYAN, modal_rect, 2, border_radius=10)

            m_title = font.render("CHOOSE TEST SCENARIO (Or Press Keys 1-6):", True, CYAN)
            surface.blit(m_title, (modal_rect.x + 20, modal_rect.y + 12))

            for s_id in ALL_SCENARIOS:
                self.buttons[f'scen_{s_id}'].draw(surface, font)
            self.buttons['scen_endless'].draw(surface, font)

    def draw_scenario_banner(
        self,
        surface: pygame.Surface,
        current_scenario: Optional[ScenarioInfo],
        countdown_ms: int,
        scenario_finished: bool,
        font: pygame.font.Font,
        is_arena: bool = False
    ):
        """Draws a sleek in-game status banner during scenario countdown or completion."""
        if not current_scenario:
            return

        banner_w = min(640, self.win_w - 40)
        banner_h = 46
        banner_x = (self.win_w - banner_w) // 2
        banner_y = 132 if is_arena else 62

        if countdown_ms > 0:
            secs = countdown_ms / 1000.0
            bg_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
            bg_surf.fill((18, 22, 34, 235))
            surface.blit(bg_surf, (banner_x, banner_y))
            pygame.draw.rect(surface, YELLOW, (banner_x, banner_y, banner_w, banner_h), 2, border_radius=6)

            t1 = font.render(f"SCENARIO {current_scenario.id}: {current_scenario.name.upper()} — STARTING IN {secs:0.1f}s", True, YELLOW)
            t2 = font.render("[SPACE] Pause to Inspect  |  [ENTER/W] Start Immediately", True, WHITE)
            surface.blit(t1, t1.get_rect(center=(banner_x + banner_w // 2, banner_y + 14)))
            surface.blit(t2, t2.get_rect(center=(banner_x + banner_w // 2, banner_y + 32)))

        elif scenario_finished:
            bg_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
            bg_surf.fill((16, 32, 24, 235))
            surface.blit(bg_surf, (banner_x, banner_y))
            pygame.draw.rect(surface, GREEN, (banner_x, banner_y, banner_w, banner_h), 2, border_radius=6)

            t1 = font.render(f"✓ SCENARIO {current_scenario.id} COMPLETED", True, GREEN)
            t2 = font.render("Press [6] for Endless Waves  |  Click [SCENARIOS] to Select Another", True, WHITE)
            surface.blit(t1, t1.get_rect(center=(banner_x + banner_w // 2, banner_y + 14)))
            surface.blit(t2, t2.get_rect(center=(banner_x + banner_w // 2, banner_y + 32)))

    def draw_telemetry_strip(
        self,
        surface: pygame.Surface,
        towers: List[Tower],
        code_font: pygame.font.Font,
        drawer_open: bool
    ):
        """Draws explainable 4-tower status strip at bottom-left when drawer is closed."""
        if drawer_open or not towers:
            return

        panel_w = 680
        panel_h = len(towers) * 24 + 30
        panel_x = 20
        panel_y = self.win_h - panel_h - 15

        # Semitransparent background
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill((18, 20, 28, 220))
        surface.blit(bg, (panel_x, panel_y))
        pygame.draw.rect(surface, (60, 65, 80), (panel_x, panel_y, panel_w, panel_h), 1, border_radius=6)

        hdr = code_font.render("REAL-TIME AI AGENT DECISIONS (Press TAB for AI Stats):", True, YELLOW)
        surface.blit(hdr, (panel_x + 10, panel_y + 6))

        for idx, tower in enumerate(towers):
            y_pos = panel_y + 26 + (idx * 22)
            strat_abbr = "UTILITY-AI" if tower.strategy == TargetingStrategy.UTILITY_AI else "NEAREST" if tower.strategy == TargetingStrategy.NEAREST_ENEMY else tower.strategy.name[:9]
            if tower.target:
                line = f"[{tower.name:9}] Strat: {strat_abbr:10} | Action: Attack -> {tower.target.id} ({tower.target.name}) | Score: {tower.target_score:6.1f}"
            else:
                line = f"[{tower.name:9}] Strat: {strat_abbr:10} | Action: Patrolling | No Target In Range"

            surf = code_font.render(line, True, tower.color)
            surface.blit(surf, (panel_x + 10, y_pos))

    def draw_arena_scoreboard(
        self,
        surface: pygame.Surface,
        left_base: Base,
        right_base: Base,
        left_kills: int,
        right_kills: int,
        font: pygame.font.Font,
        large_font: pygame.font.Font
    ):
        """Draws top comparison split scoreboard with dual graphic HP bars during Dual Arena Mode."""
        score_w = min(820, self.win_w - 30)
        score_h = 68
        score_x = (self.win_w // 2) - (score_w // 2)
        score_y = 56

        pygame.draw.rect(surface, (18, 22, 32), (score_x, score_y, score_w, score_h), border_radius=8)
        pygame.draw.rect(surface, PURPLE, (score_x, score_y, score_w, score_h), 2, border_radius=8)

        # Half width for each team's status block
        team_w = (score_w - 40) // 2

        # 1. Left: Baseline Nearest Enemy (Title + HP Bar)
        left_hp_ratio = max(0.0, left_base.hp / left_base.max_hp)
        left_hp_pct = max(0, int(left_hp_ratio * 100))
        l_text = font.render(f"BASELINE (NEAREST ENEMY) — Kills: {left_kills}", True, RED)
        surface.blit(l_text, (score_x + 16, score_y + 6))

        # Left HP Bar
        l_bar_x = score_x + 16
        l_bar_y = score_y + 25
        l_bar_h = 16
        pygame.draw.rect(surface, (35, 18, 22), (l_bar_x, l_bar_y, team_w, l_bar_h), border_radius=3)
        l_col = GREEN if left_hp_ratio > 0.5 else ORANGE if left_hp_ratio > 0.25 else RED
        pygame.draw.rect(surface, l_col, (l_bar_x, l_bar_y, int(team_w * left_hp_ratio), l_bar_h), border_radius=3)
        pygame.draw.rect(surface, WHITE, (l_bar_x, l_bar_y, team_w, l_bar_h), 1, border_radius=3)
        l_hp_txt = font.render(f"BASE HP: {int(max(0, left_base.hp))} / {int(left_base.max_hp)} ({left_hp_pct}%)", True, WHITE)
        surface.blit(l_hp_txt, l_hp_txt.get_rect(center=(l_bar_x + team_w // 2, l_bar_y + l_bar_h // 2)))

        # 2. Right: Proposed Utility AI (Title + HP Bar)
        right_hp_ratio = max(0.0, right_base.hp / right_base.max_hp)
        right_hp_pct = max(0, int(right_hp_ratio * 100))
        r_bar_x = score_x + score_w - team_w - 16
        r_text = font.render(f"PROPOSED (UTILITY AI) — Kills: {right_kills}", True, GREEN)
        surface.blit(r_text, r_text.get_rect(topright=(score_x + score_w - 16, score_y + 6)))

        # Right HP Bar
        r_bar_y = score_y + 25
        r_bar_h = 16
        pygame.draw.rect(surface, (18, 35, 22), (r_bar_x, r_bar_y, team_w, r_bar_h), border_radius=3)
        r_col = GREEN if right_hp_ratio > 0.5 else ORANGE if right_hp_ratio > 0.25 else RED
        pygame.draw.rect(surface, r_col, (r_bar_x, r_bar_y, int(team_w * right_hp_ratio), r_bar_h), border_radius=3)
        pygame.draw.rect(surface, WHITE, (r_bar_x, r_bar_y, team_w, r_bar_h), 1, border_radius=3)
        r_hp_txt = font.render(f"BASE HP: {int(max(0, right_base.hp))} / {int(right_base.max_hp)} ({right_hp_pct}%)", True, WHITE)
        surface.blit(r_hp_txt, r_hp_txt.get_rect(center=(r_bar_x + team_w // 2, r_bar_y + r_bar_h // 2)))

        # 3. Center Divider & Performance delta comparison
        pygame.draw.line(surface, (60, 50, 75), (score_x + score_w // 2, score_y + 4), (score_x + score_w // 2, score_y + 44), 1)

        hp_diff = int(right_base.hp - left_base.hp)
        if hp_diff > 0:
            delta_msg = f"Utility AI Town Hall advantage: +{hp_diff} HP"
            d_col = GREEN
        elif hp_diff < 0:
            delta_msg = f"Nearest Enemy currently leading by {abs(hp_diff)} HP"
            d_col = RED
        else:
            delta_msg = "Parity: Both defensive strategies holding equal Town Hall HP"
            d_col = YELLOW
        d_surf = font.render(delta_msg, True, d_col)
        surface.blit(d_surf, d_surf.get_rect(center=(score_x + score_w // 2, score_y + 53)))
