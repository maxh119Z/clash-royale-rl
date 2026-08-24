"""Pygame renderer for the Clash Royale arena."""

from collections.abc import Mapping
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

RED_TOP = (255,0,0)
BLUE_BOTTOM = (0,0,255)


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
        self.card_rects: list[tuple[pygame.Rect, Side, Card]] = []

    def init_pygame(self):
        if self.window is not None:
            return

        pygame.init()
        pygame.display.init()
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Clash Royale RL")
        self.clock = pygame.time.Clock()

    def draw(
        self,
        players: Mapping[Side, Player],
        hovered_tile: tuple[int, int] | None,
    ):
        """Repaint the game and limit human display to 30 FPS."""
        self.init_pygame()
        self._draw_arena()
        self._draw_troops(players[Side.TOP], Side.TOP)
        self._draw_troops(players[Side.BOTTOM], Side.BOTTOM)
        if hovered_tile is not None:
            self._draw_mouse(*hovered_tile)
        
        self.card_rects.clear()
        self._draw_panel(players[Side.TOP], Side.TOP)
        self._draw_panel(players[Side.BOTTOM], Side.BOTTOM)

        self._draw_elixir(players[Side.TOP], Side.TOP)
        self._draw_elixir(players[Side.BOTTOM], Side.BOTTOM)

        pygame.display.update()
        self.clock.tick(self.render_fps)

    def card_at_position(self, position: tuple[int, int]):
        for rect, side, card in self.card_rects:
            if rect.collidepoint(position):
                return side, card
        return None

    def tile_at_position(self, position: tuple[int, int]):
        mouse_x, mouse_y = position
        arena_mouse_y = mouse_y - OFFSET

        if not (
            0 <= mouse_x < self.arena_width
            and 0 <= arena_mouse_y < self.arena_height
        ):
            return None

        row = arena_mouse_y // TILE_SIZE
        column = mouse_x // TILE_SIZE
        return row, column

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

    def _draw_mouse(self, row: int, column: int):
        rect = pygame.Rect(
            column * TILE_SIZE,
            OFFSET + row * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(self.window, MOUSE_HIGHLIGHT, rect, width=2)

    def _draw_troops(self, player: Player, side: Side):
        for troop in player.troops.values():
            troop_image = (
                troop.card.top_troop_image
                if side is Side.TOP
                else troop.card.bottom_troop_image
            )
            image_key = (troop_image, TILE_SIZE, TILE_SIZE)
            if image_key not in self.card_images:
                image = pygame.image.load(
                    CARD_IMAGE_DIR / troop_image
                ).convert_alpha()
                self.card_images[image_key] = pygame.transform.smoothscale(
                    image,
                    (TILE_SIZE, TILE_SIZE),
                )

            image = self.card_images[image_key]
            rect = image.get_rect(
                center=(
                    int(troop.x * TILE_SIZE),
                    OFFSET + int(troop.y * TILE_SIZE),
                )
            )
            self.window.blit(image, rect)

            color = RED_TOP if side is Side.TOP else BLUE_BOTTOM
            hp_rect = pygame.Rect(
                rect.left,
                rect.top - TILE_SIZE // 2,
                int(TILE_SIZE * troop.hp / troop.card.hp),
                TILE_SIZE // 2,
            )
            pygame.draw.rect(self.window, color, hp_rect)




    def _draw_panel(self, player: Player, side: Side):
        cards = player.cards
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
            if card is player.selected_card:
                pygame.draw.rect(self.window, MOUSE_HIGHLIGHT, rect, width=3)

            self.card_rects.append((rect, side, card))
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

        
        
