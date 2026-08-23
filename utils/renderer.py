"""Pygame renderer for the Clash Royale arena."""

from collections.abc import Mapping, Sequence

import pygame

from envs.cards import Card
from envs.clash import Player, Side


GRASS_LIGHT = (182, 198, 79)
GRASS_DARK = (171, 190, 75)
GRID_LINE = (127, 142, 57)
TOP_PANEL = (126, 61, 61)
BOTTOM_PANEL = (57, 86, 132)
EMPTY_SLOT = (210, 205, 184)
CARD_SLOT = (238, 226, 187)
SLOT_BORDER = (56, 51, 43)

TILE_SIZE = 20
CARD_PANEL_HEIGHT = 6 * TILE_SIZE
CARD_GAP = 5


class ArenaRenderer:
    """Draw the arena and both players' card panels."""

    def __init__(self, num_rows: int, num_columns: int, render_fps: int = 30):
        self.num_rows = num_rows
        self.num_columns = num_columns
        self.render_fps = render_fps

        self.arena_width = num_columns * TILE_SIZE
        self.arena_height = num_rows * TILE_SIZE
        self.window_size = (
            self.arena_width,
            self.arena_height + 2 * CARD_PANEL_HEIGHT,
        )

        self.window = None
        self.clock = None

    def init_pygame(self):
        if self.window is not None:
            return

        pygame.init()
        pygame.display.init()
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Clash Royale RL")
        self.clock = pygame.time.Clock()

    def _draw_arena(self):
        for row in range(self.num_rows):
            for column in range(self.num_columns):
                color = GRASS_LIGHT if (row + column) % 2 == 0 else GRASS_DARK
                rect = pygame.Rect(
                    column * TILE_SIZE,
                    CARD_PANEL_HEIGHT + row * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(self.window, color, rect)
                pygame.draw.rect(self.window, GRID_LINE, rect, width=1)

    def _panel_y(self, side: Side) -> int:
        if side is Side.TOP:
            return 0
        return CARD_PANEL_HEIGHT + self.arena_height

    def _slot_rects(self, num_slots: int, panel_y: int) -> list[pygame.Rect]:
        if num_slots == 0:
            return []

        available_width = self.arena_width - CARD_GAP * (num_slots + 1)
        slot_width, extra_pixels = divmod(available_width, num_slots)
        slot_height = CARD_PANEL_HEIGHT - 2 * CARD_GAP

        rects = []
        slot_x = CARD_GAP
        for slot_index in range(num_slots):
            width = slot_width + (slot_index < extra_pixels)
            rects.append(
                pygame.Rect(
                    slot_x,
                    panel_y + CARD_GAP,
                    width,
                    slot_height,
                )
            )
            slot_x += width + CARD_GAP
        return rects

    def _draw_slots(self, cards: Sequence[Card | None], side: Side):
        panel_y = self._panel_y(side)
        panel_color = TOP_PANEL if side is Side.TOP else BOTTOM_PANEL
        pygame.draw.rect(
            self.window,
            panel_color,
            [0, panel_y, self.arena_width, CARD_PANEL_HEIGHT],
        )

        for card, rect in zip(cards, self._slot_rects(len(cards), panel_y)):
            color = EMPTY_SLOT if card is None else CARD_SLOT
            pygame.draw.rect(self.window, color, rect, border_radius=4)
            pygame.draw.rect(
                self.window,
                SLOT_BORDER,
                rect,
                width=2,
                border_radius=4,
            )

    def _draw_player_cards(self, players: Mapping[Side, Player] | None):
        for side in Side:
            cards = () if players is None else players[side].cards
            self._draw_slots(cards, side)

    def draw(self, players: Mapping[Side, Player] | None = None):
        """Repaint the game and limit human display to 30 FPS."""
        self.init_pygame()
        self._draw_player_cards(players)
        self._draw_arena()
        pygame.event.pump()
        pygame.display.update()
        self.clock.tick(self.render_fps)

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()
            self.window = None
            self.clock = None
