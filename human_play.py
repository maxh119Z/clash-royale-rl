from envs.clash import ClashGame
from utils.renderer import ArenaRenderer


game = ClashGame()
arena = game.reset()
renderer = ArenaRenderer(
    num_rows=arena.rows,
    num_columns=arena.columns,
    render_fps=30,
)

while True:
    renderer.draw()
    # if 1 second pass add 1 elixir
