"""
Interactive UI Controls (Buttons, Steppers, Toggles) for Simulation GUI.
"""

from typing import Tuple, Optional, Callable
import pygame

WHITE = (245, 245, 250)
BLACK = (0, 0, 0)
GRAY_DEFAULT = (45, 45, 55)
GRAY_HOVER = (70, 70, 85)
GRAY_ACTIVE = (95, 95, 115)
ACCENT_GREEN = (60, 200, 100)
ACCENT_BLUE = (60, 160, 240)
ACCENT_ORANGE = (240, 140, 40)
BORDER_COLOR = (140, 140, 160)


class Button:
    """Clickable UI button with hover animations and custom callbacks."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        default_color: Tuple[int, int, int] = GRAY_DEFAULT,
        hover_color: Tuple[int, int, int] = GRAY_HOVER,
        text_color: Tuple[int, int, int] = WHITE,
        border_radius: int = 8,
        tooltip: str = ""
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.default_color = default_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.tooltip = tooltip
        self.is_hovered = False
        self.is_active = False

    def check_hover(self, mouse_pos: Tuple[int, int]) -> bool:
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(mouse_pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        color = GRAY_ACTIVE if self.is_active else (self.hover_color if self.is_hovered else self.default_color)
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        
        border_col = WHITE if (self.is_hovered or self.is_active) else BORDER_COLOR
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=self.border_radius)

        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class NumberStepper:
    """Increment / decrement stepper for real-time weight adjustment."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        value: float,
        min_val: float = 0.0,
        max_val: float = 20.0,
        step: float = 0.5,
        format_spec: str = "{:.1f}"
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.format_spec = format_spec

        btn_size = height
        self.minus_btn = Button(x, y, btn_size, height, "-", default_color=GRAY_DEFAULT, hover_color=ACCENT_ORANGE)
        self.plus_btn = Button(x + width - btn_size, y, btn_size, height, "+", default_color=GRAY_DEFAULT, hover_color=ACCENT_GREEN)
        self.val_rect = pygame.Rect(x + btn_size, y, width - (2 * btn_size), height)

    def reposition(self, x: int, y: int, width: int, height: int):
        """Updates stepper position and dimensions dynamically."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        btn_size = height
        self.minus_btn.rect.x = x
        self.minus_btn.rect.y = y
        self.minus_btn.rect.width = btn_size
        self.minus_btn.rect.height = height
        self.plus_btn.rect.x = x + width - btn_size
        self.plus_btn.rect.y = y
        self.plus_btn.rect.width = btn_size
        self.plus_btn.rect.height = height
        self.val_rect.x = x + btn_size
        self.val_rect.y = y
        self.val_rect.width = max(10, width - (2 * btn_size))
        self.val_rect.height = height

    def check_hover(self, mouse_pos: Tuple[int, int]):
        self.minus_btn.check_hover(mouse_pos)
        self.plus_btn.check_hover(mouse_pos)

    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Returns True if value changed."""
        if self.minus_btn.is_clicked(mouse_pos):
            self.value = max(self.min_val, round(self.value - self.step, 2))
            return True
        elif self.plus_btn.is_clicked(mouse_pos):
            self.value = min(self.max_val, round(self.value + self.step, 2))
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        # Draw minus and plus buttons
        self.minus_btn.draw(surface, font)
        self.plus_btn.draw(surface, font)

        # Draw center value box
        pygame.draw.rect(surface, (30, 30, 40), self.val_rect)
        pygame.draw.rect(surface, BORDER_COLOR, self.val_rect, 1)

        val_str = self.format_spec.format(self.value)
        disp_text = f"{self.label}: {val_str}"
        val_surf = font.render(disp_text, True, WHITE)
        val_rect = val_surf.get_rect(center=self.val_rect.center)
        surface.blit(val_surf, val_rect)
