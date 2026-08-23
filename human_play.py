from envs.clash import ClashGame
from utils.renderer import ArenaRenderer


game = ClashGame()
arena = game.arena
renderer = ArenaRenderer(
    num_rows=arena.rows,
    num_columns=arena.columns,
    render_fps=30,
)

while True:
    game.tick()
    renderer.draw(game.players)
