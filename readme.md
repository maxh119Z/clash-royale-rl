Start of clash royale RL

# clash-royale-rl

Run this to activate the environment. Honestly, possibly we can just replace with python env I don't like conda and have a requirements.txt - copied from my 2048 project.

# Activate conda
```
conda env create -f environment.yml
conda activate clash-royale-rl
```

# Run game
```
python human_play.py
```

# structure
```
envs/
cards.py - defines card Object and game Cards (spear goblin, goblin)
clash.py - the Core game environemnt for all game mechanics and rules (most important)

utils/
renderer.py - draws the game with Pygame (renders Arena, troops, boards, etc.). The good part with RL is that we wouldn't need to render likely, it is only to view game if we want as humans.

human_play.py - handles in-game actions and calls renderer.py and clash.py for the game environment

card_images/ - my current collection of clash graphics.
```
