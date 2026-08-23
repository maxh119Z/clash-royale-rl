"""Pygame renderer for the Clash Royale arena."""

from collections.abc import Mapping, Sequence
from pathlib import Path

import pygame

from envs.cards import Card
from envs.clash import MAX_ELIXIR, Player, Side


GRASS_LIGHT = (182, 198, 79)
GRASS_DARK = (171, 190, 75)
GRID_LINE = (127, 142, 57)
MOUSE_HIGHLIGHT = (255, 0, 0)

PANEL_COLOR = (135, 96, 64)

TILE_SIZE = 20
CARD_PANEL_HEIGHT = 4 * TILE_SIZE
CARD_GAP_X = 65
CARD_GAP_Y = 2

ELIXIR_PANEL_HEIGHT = TILE_SIZE
ELIXIR_PANEL_COLOR = (232, 45, 225)


OFFSET = CARD_PANEL_HEIGHT + ELIXIR_PANEL_HEIGHT
CARD_IMAGE_DIR = Path(__file__).resolve().parent.parent / "card_images"


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
            self.arena_height + 2 * OFFSET,
        )

        self.window = None
        self.clock = None
        self.card_images: dict[tuple[str, int, int], pygame.Surface] = {}

    def init_pygame(self):
        if self.window is not None:
            return

        pygame.init()
        pygame.display.init()
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Clash Royale RL")
        self.clock = pygame.time.Clock()

    def draw(self, players: Mapping[Side, Player]):
        """Repaint the game and limit human display to 30 FPS."""
        self.init_pygame()
        pygame.event.pump()
        self._draw_arena()
        self._draw_mouse()
        
        top_cards = players[Side.TOP].cards
        bottom_cards = players[Side.BOTTOM].cards
        self._draw_panel(top_cards, Side.TOP)
        self._draw_panel(bottom_cards, Side.BOTTOM)

        self._draw_elixir(players[Side.TOP], Side.TOP)
        self._draw_elixir(players[Side.BOTTOM], Side.BOTTOM)

        pygame.display.update()
        self.clock.tick(self.render_fps)

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()
            self.window = None
            self.clock = None
        
    
    def _draw_arena(self):
        for row in range(self.num_rows):
            for column in range(self.num_columns):
                color = GRASS_LIGHT if (row + column) % 2 == 0 else GRASS_DARK
                rect = pygame.Rect(
                    column * TILE_SIZE,
                    OFFSET + row * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(self.window, color, rect)
                pygame.draw.rect(self.window, GRID_LINE, rect, width=1)

    def _draw_mouse(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        arena_mouse_y = mouse_y - OFFSET

        if not (
            0 <= mouse_x < self.arena_width
            and 0 <= arena_mouse_y < self.arena_height
        ):
            return

        column = mouse_x // TILE_SIZE
        row = arena_mouse_y // TILE_SIZE
        rect = pygame.Rect(
            column * TILE_SIZE,
            OFFSET + row * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(self.window, MOUSE_HIGHLIGHT, rect, width=2)


    def _draw_panel(self, cards: Sequence[Card], side: Side):
        panel_y = (
            0
            if side is Side.TOP
            else OFFSET + self.arena_height + ELIXIR_PANEL_HEIGHT
        )
        pygame.draw.rect(
            self.window,
            PANEL_COLOR,
            [0, panel_y, self.arena_width, CARD_PANEL_HEIGHT],
        )

        num_slots = len(cards)
        available_width = self.arena_width - CARD_GAP_X * (num_slots + 1)
        slot_width, extra_pixels = divmod(available_width, num_slots) # determines width of each slot
        slot_height = CARD_PANEL_HEIGHT - 2 * CARD_GAP_Y
        slot_x = CARD_GAP_X

        for slot_index, card in enumerate(cards):
            width = slot_width + (slot_index < extra_pixels)
            rect = pygame.Rect(
                slot_x,
                panel_y + CARD_GAP_Y,
                width,
                slot_height,
            )

            image_key = (card.image_filename, width, slot_height)
            if image_key not in self.card_images:
                image = pygame.image.load(
                    CARD_IMAGE_DIR / card.image_filename
                ).convert_alpha()
                self.card_images[image_key] = pygame.transform.smoothscale(
                    image,
                    (width, slot_height),
                )

            self.window.blit(self.card_images[image_key], rect)
            slot_x += width + CARD_GAP_X


    def _draw_elixir(self, player: Player, side: Side):
        panel_y = CARD_PANEL_HEIGHT if side is Side.TOP else OFFSET + self.arena_height

        pygame.draw.rect(
            self.window,
            PANEL_COLOR,
            [0, panel_y, self.arena_width, ELIXIR_PANEL_HEIGHT],
        )

        width = (player.elixir / MAX_ELIXIR) * self.arena_width
        height = ELIXIR_PANEL_HEIGHT - 2 * CARD_GAP_Y


        rect = pygame.Rect(
            0,
            panel_y + CARD_GAP_Y,
            width,
            height,
        )

        pygame.draw.rect(self.window, ELIXIR_PANEL_COLOR, rect)

        # draw lines marking each elixir
        width_1_elixir = self.arena_width / 10
        grid_offset = width_1_elixir
        for i in range(0,9):
            rect = pygame.Rect(
                grid_offset - 5,
                panel_y + CARD_GAP_Y,
                5,
                height,
            )
            pygame.draw.rect(self.window, GRID_LINE, rect)
            grid_offset += width_1_elixir

        
        
