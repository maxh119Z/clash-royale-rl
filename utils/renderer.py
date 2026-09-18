"""Pygame renderer for the Clash Royale arena."""

from collections.abc import Collection
from pathlib import Path

import pygame

from envs.cards import Card
from envs.clash import MAX_ELIXIR, TOWER_HEIGHT, TOWER_WIDTH, Player, Side


GRASS_LIGHT = (182, 198, 79)
GRASS_DARK = (171, 190, 75)
GRID_LINE = (127, 142, 57)
MOUSE_HIGHLIGHT = (255, 0, 0)
RIVER_LIGHT_BLUE = (102, 204, 255)
BRIDGE = (82, 112, 108)
MASK = (0, 0, 0, 128)
PANEL_COLOR = (135, 96, 64)

ELIXIR_PANEL_COLOR = (232, 45, 225)
RED_TOP = (255, 0, 0)
BLUE_BOTTOM = (0, 0, 255)

# more important parameters
TILE_SIZE = 20
CARD_PANEL_HEIGHT = 4 * TILE_SIZE
CARD_GAP_X = 65
CARD_GAP_Y = 2

ELIXIR_PANEL_HEIGHT = TILE_SIZE

OFFSET = CARD_PANEL_HEIGHT + ELIXIR_PANEL_HEIGHT
CARD_IMAGE_DIR = Path(__file__).resolve().parent.parent / "card_images"


class ArenaRenderer:
    """Draw the arena and both players' card panels."""

    def __init__(
        self,
        num_rows: int,
        num_columns: int,
        river_y_top: float,
        river_y_bottom: float,
        bridge_y: float,
        bridge_left_x: float,
        bridge_right_x: float,
        render_fps: int = 30,
    ):
        # same as clash.py. I don't know if redefine like this is necessary but chatGPT setup the skeleton for me to fill, so...
        self.num_rows = num_rows
        self.num_columns = num_columns
        self.river_y_top = river_y_top
        self.river_y_bottom = river_y_bottom

        self.bridge_y = bridge_y
        self. bridge_left_x = bridge_left_x
        self. bridge_right_x = bridge_right_x
        self.render_fps = render_fps

        self.arena_width = num_columns * TILE_SIZE
        self.arena_height = num_rows * TILE_SIZE
        self.window_size = (
            self.arena_width,
            self.arena_height + 2 * OFFSET,
        )

        self.window = None
        self.clock = None
        self.tower_font = None
        self.card_images: dict[tuple[str, int, int], pygame.Surface] = {}
        self.card_rects: list[tuple[pygame.Rect, Side, Card]] = []

    # start pygame
    def init_pygame(self):
        if self.window is not None:
            return

        pygame.init()
        pygame.display.init()
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Clash Royale RL")
        self.clock = pygame.time.Clock()
        self.tower_font = pygame.font.Font(None, 32)

    # end pygame
    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()
            self.window = None
            self.clock = None
            self.tower_font = None

    # MASTER DRAW EACH TICK OF EVERYTHING
    def draw(
        self,
        players: Collection[Player],
        hovered_tile: tuple[int, int] | None,
    ):
        """Repaint the game and limit human display to 30 FPS."""
        self.init_pygame()
        self._draw_arena()
        self._draw_river()
        self._draw_towers(players)
        for player in players:
            self._draw_troops(player)
        self._draw_mask(players)

        # draw a small outline around what tile is selected for simplicity
        if hovered_tile is not None:
            row, column = hovered_tile
            rect = pygame.Rect(
                column * TILE_SIZE,
                OFFSET + row * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            )
            pygame.draw.rect(self.window, MOUSE_HIGHLIGHT, rect, width=2)

        self.card_rects.clear()
        for player in players:
            self._draw_panel(player)
            self._draw_elixir(player)

        pygame.display.update()
        self.clock.tick(self.render_fps)


    # returns what card the Player is currently touching with their mouse (in case they select it)
    def card_at_position(self, position: tuple[int, int]):
        for rect, side, card in self.card_rects:
            if rect.collidepoint(position):
                return side, card
        return None

    # returns the tile the player is currently touching (in case they place a Card)
    # used in human_play.py
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
    
    # the 32x18 rectangle. O(32*18); Nested for loop for tile colors
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

    # draw the river and bridges
    def _draw_river(self):
        rect = pygame.Rect(
            0,
            OFFSET + self.river_y_top * TILE_SIZE,
            self.arena_width,
            (self.river_y_bottom - self.river_y_top) * TILE_SIZE,
        )
        pygame.draw.rect(self.window, RIVER_LIGHT_BLUE, rect)

        # draw bridges

        #draw left bridge
        left_rect = pygame.Rect(
            (self.bridge_left_x - 1.5)* TILE_SIZE, #1.5 tiles
            OFFSET + self.river_y_top * TILE_SIZE,
            3 * TILE_SIZE,
            (self.river_y_bottom - self.river_y_top) * TILE_SIZE,
        )

        #draw right bridge
        right_rect = pygame.Rect(
            (self.bridge_right_x - 1.5)* TILE_SIZE,
            OFFSET + self.river_y_top * TILE_SIZE,
            3 * TILE_SIZE,
            (self.river_y_bottom - self.river_y_top) * TILE_SIZE,
        )

        pygame.draw.rect(self.window, BRIDGE, left_rect)
        pygame.draw.rect(self.window, BRIDGE, right_rect)

    # draw the two towers and their HP text
    # note that hp is a property of the player from clash.py, no game mechanics here
    def _draw_towers(self, players: Collection[Player]):
        tower_width = TOWER_WIDTH * TILE_SIZE
        tower_height = TOWER_HEIGHT * TILE_SIZE
        tower_x = (self.arena_width - tower_width) // 2

        for player in players:
            tower_y = (
                OFFSET
                if player.side is Side.TOP
                else OFFSET + self.arena_height - tower_height
            )
            color = RED_TOP if player.side is Side.TOP else BLUE_BOTTOM
            rect = pygame.Rect(
                tower_x,
                tower_y,
                tower_width,
                tower_height,
            )
            pygame.draw.rect(self.window, color, rect)

            hp_text = self.tower_font.render(
                str(player.tower_hp),
                True,
                (255, 255, 255),
            )
            self.window.blit(hp_text, hp_text.get_rect(center=rect.center))

    # if Bottom player placing card, shade Topside and Towers to indicate can't place there
    def _draw_mask(self, players: Collection[Player]):
        mask = pygame.Surface(
            (self.arena_width, self.arena_height),
            pygame.SRCALPHA,
        )
        selected_card = False

        for player in players:
            if player.selected_card is None:
                continue

            selected_card = True
            if player.side is Side.TOP:
                rect = pygame.Rect(
                    0,
                    self.river_y_top * TILE_SIZE,
                    self.arena_width,
                    self.arena_height - self.river_y_top * TILE_SIZE,
                )
            else:
                rect = pygame.Rect(
                    0,
                    0,
                    self.arena_width,
                    self.river_y_bottom * TILE_SIZE,
                )
            pygame.draw.rect(mask, MASK, rect)

        if not selected_card:
            return

        # mask tower part
        tower_width = TOWER_WIDTH * TILE_SIZE
        tower_height = TOWER_HEIGHT * TILE_SIZE
        tower_x = (self.arena_width - tower_width) // 2
        top_tower = pygame.Rect(
            tower_x,
            0,
            tower_width,
            tower_height,
        )
        bottom_tower = pygame.Rect(
            tower_x,
            self.arena_height - tower_height,
            tower_width,
            tower_height,
        )
        pygame.draw.rect(mask, MASK, top_tower)
        pygame.draw.rect(mask, MASK, bottom_tower)
        self.window.blit(mask, (0, OFFSET))

    

    def _draw_troops(self, player: Player):
        for troop in player.troops.values():
            troop_image = (
                troop.card.top_troop_image
                if player.side is Side.TOP
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

            color = RED_TOP if player.side is Side.TOP else BLUE_BOTTOM
            hp_rect = pygame.Rect(
                rect.left,
                rect.top - TILE_SIZE // 4,
                int(TILE_SIZE * troop.hp / troop.card.hp),
                TILE_SIZE // 4,
            )
            pygame.draw.rect(self.window, color, hp_rect)

    # draw the cards panel for top and bottom player
    def _draw_panel(self, player: Player):
        cards = player.cards
        panel_y = (
            0
            if player.side is Side.TOP
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

        # ADD the cards!
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

            self.card_rects.append((rect, player.side, card))
            slot_x += width + CARD_GAP_X

    # draw the elixir
    def _draw_elixir(self, player: Player):
        panel_y = (
            CARD_PANEL_HEIGHT
            if player.side is Side.TOP
            else OFFSET + self.arena_height
        )

        pygame.draw.rect(
            self.window,
            PANEL_COLOR,
            [0, panel_y, self.arena_width, ELIXIR_PANEL_HEIGHT],
        )

        # depends on how much elixir the player has (from clash.py)
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
        for _ in range(9):
            rect = pygame.Rect(
                grid_offset - 5,
                panel_y + CARD_GAP_Y,
                5,
                height,
            )
            pygame.draw.rect(self.window, GRID_LINE, rect)
            grid_offset += width_1_elixir
