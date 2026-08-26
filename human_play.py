#human_play.py just defines what clash.py has and runs the game
#In-game actions like MOUSEDOWN are also handled here, which makes sense
#THe environment clash.py is game mechanics + rules, human_play.py is like interaction with env
import pygame

from envs.clash import ClashGame
from utils.renderer import ArenaRenderer

#setup game
game = ClashGame()
arena = game.arena
renderer = ArenaRenderer(
    num_rows=arena.rows,
    num_columns=arena.columns,
    river_y_top=arena.river_y_top,
    river_y_bottom=arena.river_y_bottom,
    bridge_y=arena.bridge_y,
    bridge_left_x=arena.bridge_left_x,
    bridge_right_x=arena.bridge_right_x,
    render_fps=30,
)
renderer.init_pygame()

while True:
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # select a card
            clicked_card = renderer.card_at_position(event.pos)
            if clicked_card is not None:
                side, card = clicked_card

                # game.players[side].selected_card = None
                game.players[side].selected_card = card
                continue

            # outline what tile mouse is at
            clicked_tile = renderer.tile_at_position(event.pos)
            if clicked_tile is not None:
                row, column = clicked_tile
                # try to placecard; if no card or any other issues, the function will return False anyways
                game.place_selected_card(row, column)

    # move troops + update elixir; backend calculations + update
    game.tick()

    hovered_tile = renderer.tile_at_position(pygame.mouse.get_pos())

    # update rest of frontend: draw.
    renderer.draw(game.players.values(), hovered_tile)
