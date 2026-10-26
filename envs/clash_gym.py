"""Gymnasium wrapper around the headless ClashGame simulation."""

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from envs.cards import CARDS
from envs.clash import ClashGame, Side, MAX_ELIXIR, TOWER_HEIGHT, TOWER_WIDTH, GAME_TIME, STARTING_TOWER_HP


TICKS_PER_ACTION = 5
MAX_TROOPS_PER_SIDE = 256
TROOP_FEATURES = 11


class ClashGymEnv(gym.Env):
    """Single learning agent playing against a scripted opponent."""

    metadata = {"render_modes": []}

    def __init__(self, learning_side: Side = Side.BOTTOM):
        super().__init__()

        self.learning_side = learning_side
        self.game = ClashGame()
        self.num_tiles = (
            self.game.arena.rows // 2 - 2
        ) * self.game.arena.columns # -2 for river
        self.num_actions = 1 + len(CARDS) * self.num_tiles
        self.action_space = spaces.Discrete(self.num_actions)
        self.observation_space = spaces.Dict(
            {
                "global": spaces.Box(
                    low=0.0,
                    high=1.0,
                    shape=(5,),
                    dtype=np.float32,
                ),
                "own_troops": spaces.Box(
                    low=0.0,
                    high=1.0,
                    shape=(MAX_TROOPS_PER_SIDE, TROOP_FEATURES),
                    dtype=np.float32,
                ),
                "enemy_troops": spaces.Box(
                    low=0.0,
                    high=1.0,
                    shape=(MAX_TROOPS_PER_SIDE, TROOP_FEATURES),
                    dtype=np.float32,
                ),
            }
        )
        
        # the core intuition is that the Environemnt will have 5 values for now
        # Remaining time (0), Own tower HP (1), Opponent tower HP (2), Own elixir (3), Opponent elixir (4)
        # Correct me if wrong, but this means it is currently blinded by what troops are on the board.

        self.scripted_opponent_next_card_index = 0 # 0 for Goblins, 1 for Spear Goblins

    def reset(self, *, seed=None, options=None):
        """Start a new match and return its first observation and action mask."""
        super().reset(seed=seed)

        self.game = ClashGame()
        
        self.scripted_opponent_next_card_index = 0
        info = {
            "action_mask": self._get_action_mask()
        }
        return self._get_observation(), info

    def step(self, action: int):
        """Apply one agent decision and advance several internal game ticks."""
        player = self.game.players[self.learning_side]
        
        # apply learning side action
        self._apply_action(player.side, action)
        
        # apply simple scripted opponent.
        self.place_scripted_action()

        for _ in range(TICKS_PER_ACTION):
            self.game.tick()
            if self.game.game_ended:
                break
        observation = self._get_observation()
        reward = 0.0 # for now
        terminated = self.game.game_ended
        truncated = False

        info = {
            "action_mask": self._get_action_mask()
        }
        return observation, reward, terminated, truncated, info

    def _get_observation(self) -> dict[str, np.ndarray]: # only implemented for learning RL; Idea: Scripted player doesn't need observations.
        """Convert ClashGame's Python objects into fixed-size float32 data."""
        player = self.game.players[self.learning_side]
        opponent_side = Side.BOTTOM if player.side is Side.TOP else Side.TOP
        opponent = self.game.players[opponent_side] 

        global_observation = np.array([
            self.game.timer / GAME_TIME,
            max(0, player.tower_hp) / STARTING_TOWER_HP,
            max(0, opponent.tower_hp) / STARTING_TOWER_HP,
            player.elixir / MAX_ELIXIR,
            opponent.elixir / MAX_ELIXIR
        ], dtype=np.float32)

        return {
            "global": global_observation,
            "own_troops": self._get_troop_array(self.learning_side),
            "enemy_troops": self._get_troop_array(opponent_side),
        }

    def _get_troop_array(self, side: Side) -> np.ndarray:
        """Convert one player's troops into fixed-size float32 rows."""
        troop_array = np.zeros(
            (MAX_TROOPS_PER_SIDE, TROOP_FEATURES),
            dtype=np.float32,
        )
        

        player = self.game.players[side]
        opponent_side = Side.BOTTOM if side is Side.TOP else Side.TOP
        opponent = self.game.players[opponent_side] 

        troops = list(player.troops.values())
        if side is self.learning_side:
    #        Own troops: lower Y means closer to the enemy tower.
            troops.sort(
                key=lambda troop: (troop.y, troop.x, troop.id)
            )
        else:
            # Enemy troops: higher Y means closer to our tower.
            troops.sort(
                key=lambda troop: (-troop.y, troop.x, troop.id)
            )
        
        
        for i, troop in enumerate(troops[:MAX_TROOPS_PER_SIDE]):
            troop_array[i, 0] = 1.0

            if troop.card.name == "Goblins":
                troop_array[i, 1] = 1.0
            elif troop.card.name == "Spear Goblins":
                troop_array[i, 2] = 1.0

            troop_array[i, 3] = troop.x / self.game.arena.columns
            troop_array[i, 4] = troop.y / self.game.arena.rows
            troop_array[i, 5] = max(0, troop.hp) / troop.card.hp
            troop_array[i, 6] = (
                troop.cooldown / troop.attack_cooldown
            )

            troop_array[i, 8] = float(troop.target_is_tower)

            locked_target = None

            if troop.targettroop is not None:
                locked_target = opponent.troops.get(troop.targettroop)

            if locked_target is not None:
                troop_array[i, 7] = 1.0
                troop_array[i, 9] = (
                    locked_target.x / self.game.arena.columns
                )
                troop_array[i, 10] = (
                    locked_target.y / self.game.arena.rows
                )


        # 4. Loop through at most MAX_TROOPS_PER_SIDE sorted troops.
        # 5. Find the opponent Player so a locked target id can be looked up with .get().
        # 6. Fill each troop row using these feature indexes:
        #    0  = present (always 1 for a real troop)
        #    1  = is Goblin
        #    2  = is Spear Goblin
        #    3  = troop.x / arena.columns
        #    4  = troop.y / arena.rows
        #    5  = max(0, troop.hp) / troop.card.hp
        #    6  = troop.cooldown / troop.attack_cooldown
        #    7  = has a living troop target
        #    8  = troop.target_is_tower
        #    9  = living target.x / arena.columns, otherwise 0
        #    10 = living target.y / arena.rows, otherwise 0
        # 7. Leave every unused row as the zeroes created above.
        # 8. Top-side coordinate mirroring is future work; encode current arena coordinates for now.

        return troop_array


    def _get_action_mask(self) -> np.ndarray: # only implemented for learning RL; Idea: Scripted player doesn't need observations.
        """Return 1 for legal actions and 0 for illegal actions."""
        # 1 = legal; 0 = illegal
        mask = np.zeros(self.num_actions, dtype=np.int8)
        mask[0] = 1 # doing nothing is always legal
        
        if self.game.game_ended:
            return mask
        
        player = self.game.players[self.learning_side]
        for i in range(1, self.num_actions):
            card, row, column = self._decode_action(i)
            if (player.elixir < card.elixir_cost):
                continue
            
            if self.learning_side is Side.TOP:
                arena_row = row
            else:
                arena_row = self.game.arena.rows - 1 - row

            tower_left = self.game.arena.columns/2 - TOWER_WIDTH / 2
            tower_right = self.game.arena.columns/2 + TOWER_WIDTH / 2

            in_tower_column = tower_left <= column < tower_right

            if self.learning_side is Side.TOP:
                in_own_tower_row = arena_row < self.game.arena.top_tower_y + TOWER_HEIGHT
            else:
                in_own_tower_row = arena_row >= self.game.arena.rows - TOWER_HEIGHT

            if in_tower_column and in_own_tower_row:
                continue

            mask[i] = 1


        return mask

    def _decode_action(self, action: int):
        """Translate an action number into no-op or (card, local row, column)."""

        # Return None for action 0.
        if action == 0:
            return None
        
        # 0–17    → row 0
        # 18–35   → row 1
        # 36–53   → row 2
        # 54–71   → row 3
        # 72–89   → row 4
        index = action - 1 # since it starts with 0

        if index < self.num_tiles:
            card = CARDS[0] # GOBLINS
        else:
            card = CARDS[1] # SPEAR GOBLINS
            index -= self.num_tiles
        
        row = index // self.game.arena.columns # local rows 0-13
        column = index % self.game.arena.columns

        
        return card, row, column

    def _apply_action(self, side: Side, action: int) -> bool:
        """Decode and attempt one card placement for the requested side."""

        
        decoded = self._decode_action(action)
        if decoded is None:
            return False
        
        card, row, column = decoded
        if side is Side.TOP:
            arena_row = row
        else:
            arena_row = self.game.arena.rows - 1 - row

        self.game.players[side].selected_card = card
        return self.game.place_selected_card(arena_row, column)
        

    def place_scripted_action(self) -> bool:
        """Place the opponent's alternating Goblins/Spear Goblins action."""

        player = self.game.players[self.learning_side]
        opponent_side = Side.BOTTOM if player.side is Side.TOP else Side.TOP
        opponent = self.game.players[opponent_side] 

        current_card = CARDS[self.scripted_opponent_next_card_index]
        if opponent.elixir < current_card.elixir_cost:
            return False
        
        opponent.selected_card = current_card
        local_row = self.game.arena.rows // 2 - 4
        arena_row = local_row if opponent_side is Side.TOP else self.game.arena.rows - 1 - local_row
        placed = self.game.place_selected_card(arena_row, self.game.arena.columns // 2) # hard coded
        if placed:
            self.scripted_opponent_next_card_index = 0 if self.scripted_opponent_next_card_index == 1 else 1
        return placed
