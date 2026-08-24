import pygame

from envs.clash import ClashGame
from utils.renderer import ArenaRenderer


game = ClashGame()
arena = game.arena
renderer = ArenaRenderer(
    num_rows=arena.rows,
    num_columns=arena.columns,
    render_fps=30,
)
renderer.init_pygame()
active_side = None

while True:
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_card = renderer.card_at_position(event.pos)
            if clicked_card is not None:
                side, card = clicked_card
                for player in game.players.values():
                    player.selected_card = None
                game.players[side].selected_card = card
                active_side = side
                continue

            clicked_tile = renderer.tile_at_position(event.pos)
            if active_side is not None and clicked_tile is not None:
                row, column = clicked_tile
                if game.place_selected_card(active_side, row, column):
                    active_side = None

    hovered_tile = renderer.tile_at_position(pygame.mouse.get_pos())
    game.tick()
    renderer.draw(game.players, hovered_tile)
