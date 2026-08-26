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

# To-do
Not sure, we should figure this sometime. There are some intentional features I have, like both sides of board can be masked I put it in comments next to where I coded the functionality, but not sure what needs to change.

Generally for RL we need a good game environment that's efficient and has all the necessary functionality before we can code the RL agent. Right now it is in a decent spot, could be more like CR i guess. There's also the question of what RL agent to use which I had some ideas but haven't looked deeply. Once we are sure the game env is perfect we can start with RL, but one of us can research the RL as well as someone finishes the Game Env

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
