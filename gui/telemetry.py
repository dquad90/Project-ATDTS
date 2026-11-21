"""
Explainable AI (XAI) Inspector & Candidate Threat Matrix Overlay.
Fully adjustable window: draggable by title bar, resizable by corner handle,
and auto-fitting content height to eliminate empty voids.
"""

from typing import List, Optional, Tuple, Dict, Any
import pygame

from core.entities import Tower, Enemy, WHITE, BLACK, GREEN, RED, YELLOW, CYAN, ORANGE, PURPLE, CRIMSON
from core.agent import TargetingStrategy, CandidateEvaluation
from gui.controls import Button, NumberStepper


class ExplainableAIDrawer:
    """
    Adjustable inspection window rendering real-time candidate threat matrices,
    mathematical score breakdowns, weight adjustment steppers, and natural-language rationales.
    Supports dragging, resizing, and auto-fitting.
    """

    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open = False
        self.is_retracted = False
        self.selected_tower_index = 0

        # Window dimensions: default to clean, compact content-adaptive size
        self.min_w = 480
        self.min_h = 260
        self.retracted_h = 42
        self.panel_w = min(600, screen_w - 40)
        self.panel_h = 440  # Compact default height (eliminates 300px empty void)
        self.saved_h = 440
        self.panel_x = screen_w - self.panel_w - 20
        self.panel_y = 65

        # Dragging and resizing state
        self.is_dragging = False
        self.drag_offset = (0, 0)
        self.is_resizing = False
        self.resize_start_pos = (0, 0)
        self.resize_start_size = (0, 0)
        self.last_click_time = -9999
        self.resize_grip_size = 20

        # UI Controls inside drawer
        self.close_btn = Button(
            self.panel_x + self.panel_w - 38, self.panel_y + 8,
            30, 26, "X",
            default_color=(120, 40, 40), hover_color=RED, border_radius=4,
            tooltip="Close Inspector"
        )
        self.retract_btn = Button(
            self.panel_x + self.panel_w - 74, self.panel_y + 8,
            32, 26, "▾",
            default_color=(45, 55, 80), hover_color=CYAN, border_radius=4,
            tooltip="Retract / Collapse Window"
        )
        self.fit_btn = Button(
            self.panel_x + self.panel_w - 124, self.panel_y + 8,
            46, 26, "FIT",
            default_color=(35, 50, 75), hover_color=CYAN, border_radius=4,
            tooltip="Auto-fit window height to content"
        )
        self.strat_btn = Button(
            self.panel_x + 16, self.panel_y + 84,
            self.panel_w - 32, 30, "STRATEGY: Utility-Based AI",
            default_color=(40, 65, 100), hover_color=(60, 95, 150), border_radius=6
        )

        # Weight steppers
        self.steppers: Dict[str, NumberStepper] = {
            'AP': NumberStepper(self.panel_x + 16, self.panel_y + 130, 130, 26, "w_AP", 2.0, min_val=0.0, max_val=10.0, step=0.5),
            'SPD': NumberStepper(self.panel_x + 155, self.panel_y + 130, 130, 26, "w_SPD", 1.5, min_val=0.0, max_val=10.0, step=0.5),
            'DIST_PROX': NumberStepper(self.panel_x + 295, self.panel_y + 130, 135, 26, "w_PROX", 1.0, min_val=0.0, max_val=15.0, step=0.5),
            'HP': NumberStepper(self.panel_x + 440, self.panel_y + 130, 125, 26, "w_HP", 0.5, min_val=0.0, max_val=5.0, step=0.1)
        }

        self._recalc_layout()

    @property
    def rect(self) -> pygame.Rect:
        h = self.retracted_h if self.is_retracted else self.panel_h
        return pygame.Rect(self.panel_x, self.panel_y, self.panel_w, h)

    @property
    def title_bar_rect(self) -> pygame.Rect:
        return pygame.Rect(self.panel_x, self.panel_y, self.panel_w - 130, 42)

    @property
    def resize_grip_rect(self) -> pygame.Rect:
        if self.is_retracted:
            return pygame.Rect(0, 0, 0, 0)
        return pygame.Rect(
            self.panel_x + self.panel_w - self.resize_grip_size,
            self.panel_y + self.panel_h - self.resize_grip_size,
            self.resize_grip_size, self.resize_grip_size
        )

    def _recalc_layout(self):
        """Recalculates all sub-component positions and responsive widths."""
        self.close_btn.rect.x = self.panel_x + self.panel_w - 36
        self.close_btn.rect.y = self.panel_y + 8

        self.retract_btn.rect.x = self.panel_x + self.panel_w - 72
        self.retract_btn.rect.y = self.panel_y + 8
        self.retract_btn.text = "▲" if self.is_retracted else "▾"
        self.retract_btn.tooltip = "Expand Window (▲)" if self.is_retracted else "Retract Window (▾)"

        self.fit_btn.rect.x = self.panel_x + self.panel_w - 120
        self.fit_btn.rect.y = self.panel_y + 8

        self.strat_btn.rect.x = self.panel_x + 16
        self.strat_btn.rect.y = self.panel_y + 82
        self.strat_btn.rect.width = self.panel_w - 32

        # Dynamically size and space all 4 steppers across available width
        stepper_y = self.panel_y + 128
        total_inner_w = self.panel_w - 32
        gap = 8
        stepper_w = max(95, (total_inner_w - (3 * gap)) // 4)

        keys = ['AP', 'SPD', 'DIST_PROX', 'HP']
        for i, k in enumerate(keys):
            sx = self.panel_x + 16 + i * (stepper_w + gap)
            self.steppers[k].reposition(sx, stepper_y, stepper_w, 26)

    def resize(self, screen_w: int, screen_h: int):
        """Called when main window resizes."""
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.panel_w = min(self.panel_w, screen_w - 30)
        self.panel_h = min(self.panel_h, screen_h - 40)
        self.panel_x = max(10, min(screen_w - self.panel_w - 10, self.panel_x))
        self.panel_y = max(10, min(screen_h - self.panel_h - 10, self.panel_y))
        self._recalc_layout()

    def toggle(self):
        self.is_open = not self.is_open

    def auto_fit_height(self, towers: List[Tower]):
        """Calculates exact content height and sizes window snugly to eliminate empty void."""
        if not towers:
            return
        curr_t = towers[self.selected_tower_index % len(towers)]
        record_count = min(8, max(1, len(curr_t.candidate_records)))
        
        # Content vertical stack:
        # Title(42) + Tabs(36) + Strategy(34) + Steppers(40) + TableHeader(24) + Rows(22*N) + Rationale(95) + BottomPadding(20)
        needed_h = 42 + 36 + 34 + 40 + 24 + (record_count * 22) + 105 + 20
        self.panel_h = max(self.min_h, min(self.screen_h - self.panel_y - 15, needed_h))
        self._recalc_layout()

    def sync_weights_from_tower(self, tower: Tower):
        """Synchronizes GUI steppers with the active tower's weights."""
        if 'AP' in tower.weights:
            self.steppers['AP'].value = tower.weights['AP']
        if 'SPD' in tower.weights:
            self.steppers['SPD'].value = tower.weights['SPD']
        if 'DIST_PROX' in tower.weights:
            self.steppers['DIST_PROX'].value = tower.weights['DIST_PROX']
        if 'HP' in tower.weights:
            self.steppers['HP'].value = tower.weights['HP']

    def sync_weights_to_tower(self, tower: Tower):
        """Pushes updated GUI steppers into tower's agent."""
        new_weights = {
            'AP': self.steppers['AP'].value,
            'SPD': self.steppers['SPD'].value,
            'DIST_PROX': self.steppers['DIST_PROX'].value,
            'HP': self.steppers['HP'].value,
        }
        if 'cluster' in tower.weights:
            new_weights['cluster'] = tower.weights['cluster']
        tower.update_weights(new_weights)

    def handle_mouse_events(
        self,
        mouse_pos: Tuple[int, int],
        mouse_clicked: bool,
        mouse_pressed: bool,
        towers: List[Tower]
    ) -> bool:
        """
        Handles interactive mouse dragging, resizing, clicks, and steppers.
        Returns True if mouse event is absorbed by the inspector window.
        """
        if not towers:
            return False

        if not self.is_open:
            self.is_dragging = False
            self.is_resizing = False
            return False

        # 1. Active Resizing Drag
        if self.is_resizing:
            if mouse_pressed:
                dx = mouse_pos[0] - self.resize_start_pos[0]
                dy = mouse_pos[1] - self.resize_start_pos[1]
                new_w = max(self.min_w, min(self.screen_w - self.panel_x - 10, self.resize_start_size[0] + dx))
                new_h = max(self.min_h, min(self.screen_h - self.panel_y - 10, self.resize_start_size[1] + dy))
                self.panel_w = new_w
                self.panel_h = new_h
                self._recalc_layout()
                return True
            else:
                self.is_resizing = False

        # 2. Active Window Repositioning Drag
        if self.is_dragging:
            if mouse_pressed:
                new_x = mouse_pos[0] - self.drag_offset[0]
                new_y = mouse_pos[1] - self.drag_offset[1]
                # Clamp within screen bounds
                self.panel_x = max(5, min(self.screen_w - self.panel_w - 5, new_x))
                self.panel_y = max(5, min(self.screen_h - 40, new_y))
                self._recalc_layout()
                return True
            else:
                self.is_dragging = False

        # Check button hovers
        self.close_btn.check_hover(mouse_pos)
        self.retract_btn.check_hover(mouse_pos)
        self.fit_btn.check_hover(mouse_pos)
        if not self.is_retracted:
            self.strat_btn.check_hover(mouse_pos)
            for s in self.steppers.values():
                s.check_hover(mouse_pos)

        # 3. Mouse Down / Click Actions
        if mouse_clicked:
            # Check close button
            if self.close_btn.is_clicked(mouse_pos):
                self.is_open = False
                return True

            # Check retract/collapse button
            if self.retract_btn.is_clicked(mouse_pos):
                self.is_retracted = not self.is_retracted
                if not self.is_retracted and self.panel_h < self.min_h:
                    self.panel_h = self.saved_h
                self._recalc_layout()
                return True

            # Check auto-fit button
            if self.fit_btn.is_clicked(mouse_pos):
                self.is_retracted = False
                self.auto_fit_height(towers)
                return True

            # Check title bar drag initiation (with double-click retract/expand detection)
            if self.title_bar_rect.collidepoint(mouse_pos):
                now = pygame.time.get_ticks()
                if now - self.last_click_time < 300:
                    # Double click: toggle retract / expand
                    self.is_retracted = not self.is_retracted
                    if not self.is_retracted and self.panel_h < self.min_h:
                        self.panel_h = self.saved_h
                    self._recalc_layout()
                else:
                    self.is_dragging = True
                    self.drag_offset = (mouse_pos[0] - self.panel_x, mouse_pos[1] - self.panel_y)
                self.last_click_time = now
                return True

            # If retracted, absorb clicks on the title bar only and return
            if self.is_retracted:
                return self.rect.collidepoint(mouse_pos)

            # Check resize corner grip
            if self.resize_grip_rect.collidepoint(mouse_pos):
                self.is_resizing = True
                self.resize_start_pos = mouse_pos
                self.resize_start_size = (self.panel_w, self.panel_h)
                return True

            current_tower = towers[self.selected_tower_index % len(towers)]

            # Tower tabs selection
            tab_w = (self.panel_w - 32) // len(towers)
            for idx in range(len(towers)):
                tab_rect = pygame.Rect(self.panel_x + 16 + (idx * tab_w), self.panel_y + 44, tab_w - 4, 30)
                if tab_rect.collidepoint(mouse_pos):
                    self.selected_tower_index = idx
                    self.sync_weights_from_tower(towers[idx])
                    return True

            # Strategy cycle button
            if self.strat_btn.is_clicked(mouse_pos):
                current_tower.cycle_strategy()
                return True

            # Stepper clicks
            weight_changed = False
            for s in self.steppers.values():
                if s.handle_click(mouse_pos):
                    weight_changed = True
            if weight_changed:
                self.sync_weights_to_tower(current_tower)
                return True

            # Absorb any clicks inside panel body so battlefield is not clicked
            if self.rect.collidepoint(mouse_pos):
                return True

        # Absorb hovers inside panel when dragging/resizing
        return self.is_dragging or self.is_resizing or self.rect.collidepoint(mouse_pos)

    def draw(
        self,
        surface: pygame.Surface,
        towers: List[Tower],
        font: pygame.font.Font,
        code_font: pygame.font.Font
    ):
        if not self.is_open or not towers:
            return

        current_tower = towers[self.selected_tower_index % len(towers)]
        drawn_h = self.retracted_h if self.is_retracted else self.panel_h

        # 1. Main Window Backdrop (Dark slate translucent panel)
        overlay = pygame.Surface((self.panel_w, drawn_h), pygame.SRCALPHA)
        overlay.fill((18, 20, 30, 248))
        surface.blit(overlay, (self.panel_x, self.panel_y))

        # Glowing border (brightened if dragging or resizing)
        border_col = CYAN if (self.is_dragging or self.is_resizing) else (65, 80, 115)
        border_w = 2 if (self.is_dragging or self.is_resizing) else 1
        pygame.draw.rect(surface, border_col, (self.panel_x, self.panel_y, self.panel_w, drawn_h), border_w, border_radius=10)

        # 2. Draggable Title Bar
        title_bg = pygame.Surface((self.panel_w, 40), pygame.SRCALPHA)
        title_bg.fill((28, 33, 48, 255))
        surface.blit(title_bg, (self.panel_x, self.panel_y))
        if not self.is_retracted:
            pygame.draw.line(surface, (50, 60, 85), (self.panel_x, self.panel_y + 40), (self.panel_x + self.panel_w, self.panel_y + 40), 1)

        # Title text with drag handle glyph
        drag_hint = " (DRAGGING)" if self.is_dragging else (" [RETRACTED ▾]" if self.is_retracted else "")
        title_surf = font.render(f"⠿ AI STATS & TARGET INSPECTOR{drag_hint}", True, CYAN)
        surface.blit(title_surf, (self.panel_x + 14, self.panel_y + 11))

        # Title buttons: FIT, RETRACT, and CLOSE
        self.fit_btn.draw(surface, code_font)
        self.retract_btn.draw(surface, font)
        self.close_btn.draw(surface, font)

        # If retracted, stop here (body is collapsed)
        if self.is_retracted:
            return

        # 3. Tower Selection Tabs
        tab_w = (self.panel_w - 32) // len(towers)
        for idx, tower in enumerate(towers):
            is_active = (idx == self.selected_tower_index)
            tab_rect = pygame.Rect(self.panel_x + 16 + (idx * tab_w), self.panel_y + 46, tab_w - 4, 28)
            col = tower.color if is_active else (35, 38, 50)
            pygame.draw.rect(surface, col, tab_rect, border_radius=5)
            pygame.draw.rect(surface, WHITE if is_active else (55, 60, 75), tab_rect, 2 if is_active else 1, border_radius=5)

            txt_col = BLACK if is_active else WHITE
            t_name = font.render(tower.name, True, txt_col)
            surface.blit(t_name, t_name.get_rect(center=tab_rect.center))

        # 4. Strategy Switcher Button
        self.strat_btn.text = f"STRATEGY: {current_tower.strategy.value}"
        self.strat_btn.draw(surface, font)

        # 5. Weight Adjustment Steppers
        stepper_label = code_font.render("AI Utility Weights (Adjust in real time to retarget):", True, YELLOW)
        surface.blit(stepper_label, (self.panel_x + 16, self.panel_y + 115))
        for s in self.steppers.values():
            s.draw(surface, code_font)

        # 6. Candidate Threat Evaluation Matrix
        table_y = self.panel_y + 160
        matrix_header = code_font.render("CANDIDATE THREAT EVALUATION MATRIX (D <= D_MAX):", True, WHITE)
        surface.blit(matrix_header, (self.panel_x + 16, table_y))

        # Column headers dynamically scaled
        col_y = table_y + 20
        usable_table_w = self.panel_w - 32
        
        # Fixed initial columns
        c_rank = 45
        c_id = 65
        c_type = 60
        c_ap = 45
        c_spd = 45
        c_dist = 55
        c_prox = 48
        c_hp = 55
        c_score = max(65, usable_table_w - (c_rank + c_id + c_type + c_ap + c_spd + c_dist + c_prox + c_hp))

        headers = [
            ("RANK", c_rank), ("ID", c_id), ("TYPE", c_type), ("AP", c_ap),
            ("SPD", c_spd), ("DIST", c_dist), ("PROX", c_prox), ("HP", c_hp), ("SCORE", c_score)
        ]

        hx = self.panel_x + 16
        pygame.draw.rect(surface, (30, 36, 52), (hx, col_y, usable_table_w, 20), border_radius=4)
        for h_text, width in headers:
            h_surf = code_font.render(h_text, True, CYAN)
            surface.blit(h_surf, (hx + 4, col_y + 2))
            hx += width

        records = current_tower.candidate_records
        row_y = col_y + 24

        # Calculate max rows that comfortably fit before the rationale box
        rationale_box_h = 80
        bottom_reserved = rationale_box_h + 30
        available_row_space = max(24, (self.panel_y + self.panel_h - bottom_reserved) - row_y)
        max_rows = max(1, available_row_space // 22)

        if not records:
            empty_msg = code_font.render("No enemy units currently inside sensor range.", True, (150, 155, 170))
            surface.blit(empty_msg, (self.panel_x + 24, row_y + 6))
            row_y += 28
        else:
            for rec in records[:max_rows]:
                is_winner = rec.is_selected
                row_bg = (38, 75, 48) if is_winner else (24, 27, 38)
                row_rect = pygame.Rect(self.panel_x + 16, row_y, usable_table_w, 20)
                pygame.draw.rect(surface, row_bg, row_rect, border_radius=4)
                if is_winner:
                    pygame.draw.rect(surface, GREEN, row_rect, 1, border_radius=4)

                rx = self.panel_x + 16
                row_data = [
                    (f"#{rec.rank}", c_rank, GREEN if is_winner else WHITE),
                    (rec.enemy_id, c_id, YELLOW if is_winner else WHITE),
                    (rec.enemy_name[:6], c_type, WHITE),
                    (f"{int(rec.ap)}", c_ap, ORANGE),
                    (f"{rec.spd:.1f}", c_spd, YELLOW),
                    (f"{int(rec.distance)}px", c_dist, WHITE),
                    (f"{rec.proximity:.2f}", c_prox, CYAN),
                    (f"{int(rec.hp)}", c_hp, RED),
                    (f"{rec.total_score:.1f}", c_score, GREEN if is_winner else WHITE)
                ]
                for val_str, w, val_color in row_data:
                    cell_surf = code_font.render(val_str, True, val_color)
                    surface.blit(cell_surf, (rx + 4, row_y + 2))
                    rx += w

                row_y += 22

        # 7. Agent Decision Rationale Box
        box_y = row_y + 8
        box_h = max(60, min(100, (self.panel_y + self.panel_h - 14) - box_y))
        box_rect = pygame.Rect(self.panel_x + 16, box_y, usable_table_w, box_h)
        
        pygame.draw.rect(surface, (24, 28, 42), box_rect, border_radius=6)
        pygame.draw.rect(surface, (50, 70, 110), box_rect, 1, border_radius=6)

        reason_title = font.render("AGENT DECISION RATIONALE:", True, GREEN)
        surface.blit(reason_title, (self.panel_x + 24, box_y + 6))

        # Word-wrapped explanation
        expl_text = current_tower.explanation
        words = expl_text.split()
        lines = []
        curr_line = ""
        for word in words:
            test_line = f"{curr_line} {word}".strip()
            if code_font.size(test_line)[0] < usable_table_w - 30:
                curr_line = test_line
            else:
                lines.append(curr_line)
                curr_line = word
        if curr_line:
            lines.append(curr_line)

        max_visible_lines = max(1, (box_h - 26) // 15)
        for l_idx, line in enumerate(lines[:max_visible_lines]):
            l_surf = code_font.render(line, True, WHITE)
            surface.blit(l_surf, (self.panel_x + 24, box_y + 26 + (l_idx * 15)))

        # 8. Bottom-Right Resize Grip Handle (◢)
        grip_x = self.panel_x + self.panel_w - 18
        grip_y = self.panel_y + self.panel_h - 18
        grip_col = CYAN if self.is_resizing else (130, 145, 175)

        # Draw 3 diagonal grip stripes
        for offset in [4, 8, 12]:
            pygame.draw.line(
                surface, grip_col,
                (grip_x + offset, grip_y + 14),
                (grip_x + 14, grip_y + offset),
                2
            )
