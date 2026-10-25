"""Core state for the Clash Royale environment."""
# This file lowkey is all the core functionality for Player, Arena object, etc.
# and also core functions. Just think anything GAME MECHANIC is in this file. 
# CORE GAME ENVIRONMENT.

# choices
"""
1. game winner decided by who has more HP if time runs out
2. towers cannot shoot: it is like heist

"""

from dataclasses import dataclass, field
from enum import Enum
from math import hypot

from envs.cards import CARDS, Card

FPS = 30
ROWS = 32
COLUMNS = 18

MAX_ELIXIR = 10.0
STARTING_ELIXIR = 4.0
ELIXIR_PER_SECOND = 0.714 # to match CR real game set to: 0.357; double elixir = 0.714
MOVEMENT_PER_TICK = 1 / FPS
STARTING_TOWER_HP = 1000
GAME_TIME = 3000 # 100 seconds
TOWER_WIDTH = 4
TOWER_HEIGHT = 4
GAME_ENDED = False
WINNER = None


class Side(Enum):
    """The two fixed sides of the arena."""

    TOP = "top"
    BOTTOM = "bottom"


@dataclass(frozen=True)
class Arena:
    """Arena dimensions"""
    # Pygame is weird where top screen is y = 0 lower you go y increases.

    rows: int = ROWS
    columns: int = COLUMNS
    tower_x: float = COLUMNS / 2
    top_tower_y: float = 0.0
    bottom_tower_y: float = float(ROWS)

    # river is 4 tiles wide
    river_y_top = ROWS / 2 - 2
    river_y_bottom = ROWS / 2 + 2

    bridge_y = ROWS / 2
    bridge_left_x = COLUMNS / 2 - 6
    bridge_right_x = COLUMNS / 2 + 6



@dataclass
class Troop:
    """A troop positioned in continuous tile coordinates."""

    id: int
    card: Card
    hp: int
    x: float
    y: float
    radius: int
    sightradius: int
    attack: int
    targettroop: int | None # id of object targetting;
    target_is_tower: bool # yes = is_tower
    cooldown: int
    attack_cooldown: int


@dataclass
class Player:
    """The cards, elixir, and tower state belonging to one side."""

    side: Side
    cards: list[Card]
    selected_card: Card | None = None
    elixir: float = STARTING_ELIXIR
    tower_hp: int = STARTING_TOWER_HP
    troops: dict[int, Troop] = field(default_factory=dict)


class ClashGame:
    """Headless state for a two-player game."""


    def __init__(self):
        # define arena, players, and start troop ID, which is incremented as troops are played
        self.arena = Arena()
        self.next_troop_id = 0
        self.players: dict[Side, Player] = {
            Side.TOP: Player(side=Side.TOP, cards=list(CARDS)),
            Side.BOTTOM: Player(side=Side.BOTTOM, cards=list(CARDS)),
        }
        self.game_ended = False
        self.winner: Side | None = None
        self.timer: int = GAME_TIME

    def place_selected_card(self, row: int, column: int) -> bool:
        #player = self.players[side]

        if self.game_ended:
            return False

         # so technically you are allowed to play your opponent's card, but when we train the RL, we can probably
        # just mask that ourselves so it is not an issue the RL learns to play opponent cards.

        # if you click bottom half, it will try to place troop as BOTTOM player, else place as TOP player
        if row >= self.arena.river_y_bottom:
            player = self.players[Side.BOTTOM]
        elif row < self.arena.river_y_top:
            player = self.players[Side.TOP]
        else: return False # need elif + else because river space doesn't count as any player
        card = player.selected_card

        if card is None: # no selected card
            return False
        if not (0 <= row < self.arena.rows and 0 <= column < self.arena.columns): # card place outside Arena
            return False

        
        # old reference: mask river and other player's side
        # if player.side is Side.TOP and row >= self.arena.river_y_top:
        #     return False
        # if player.side is Side.BOTTOM and row < self.arena.river_y_bottom:
        #     return False

        # mask tower part; no allow place on tower
        tower_left = self.arena.tower_x - TOWER_WIDTH / 2
        tower_right = self.arena.tower_x + TOWER_WIDTH / 2
        
        #booleans to check
        in_tower_column = tower_left <= column < tower_right
        in_top_tower = row < self.arena.top_tower_y + TOWER_HEIGHT
        in_bottom_tower = row >= self.arena.bottom_tower_y - TOWER_HEIGHT
        if in_tower_column and (in_top_tower or in_bottom_tower):
            return False

        if player.elixir < card.elixir_cost:
            return False

        # if you place tile on border, we must have system to not have troop go off the map
        left = 0.5 if column == 0 else 0
        right = -0.6 if column == self.arena.columns - 1 else 0
        top = 0.5 if row == 0 or row == self.arena.river_y_bottom else 0
        bottom = -0.5 if row == self.arena.rows - 1 or row == self.arena.river_y_top - 1 else 0

        # if pass all checks, define Troop
        #spawn 4 goblins
        if card.name == "Goblins":
            troop1 = Troop(
                id=self.next_troop_id,
                card=card,
                hp=card.hp,
                x=column + 0 + left + right,
                y=row + 1 + top + bottom,
                radius=card.radius,
                sightradius = card.sightradius,
                attack=card.attack,
                targettroop=None,
                target_is_tower=False,
                cooldown=card.attack_cooldown,
                attack_cooldown=card.attack_cooldown
            )
            troop2 = Troop(
                id=self.next_troop_id+1,
                card=card,
                hp=card.hp,
                x=column + 1.1 + left + right, # without the 1.1 instead of 1, the mobs do not split lanes when placed in the middle
                y=row + 1 + top + bottom,
                radius=card.radius,
                sightradius = card.sightradius,
                attack=card.attack,
                targettroop=None,
                target_is_tower=False,
                cooldown=card.attack_cooldown,
                attack_cooldown=card.attack_cooldown
            )
            troop3 = Troop(
                id=self.next_troop_id+2,
                card=card,
                hp=card.hp,
                x=column + 0 + left + right,
                y=row + 0 + top + bottom,
                radius=card.radius,
                sightradius = card.sightradius,
                attack=card.attack,
                targettroop=None,
                target_is_tower=False,
                cooldown=card.attack_cooldown,
                attack_cooldown=card.attack_cooldown
            )
            troop4 = Troop(
                id=self.next_troop_id+3,
                card=card,
                hp=card.hp,
                x=column + 1.1 + left + right,
                y=row + 0 + top + bottom,
                radius=card.radius,
                sightradius = card.sightradius,
                attack=card.attack,
                targettroop=None,
                target_is_tower=False,
                cooldown=card.attack_cooldown,
                attack_cooldown=card.attack_cooldown
            )
            player.troops[troop1.id] = troop1 # player.troops is a mutable dict
            player.troops[troop2.id] = troop2
            player.troops[troop3.id] = troop3
            player.troops[troop4.id] = troop4
            self.next_troop_id += 4

        # spawn 3 spear goblins
        elif card.name == "Spear Goblins":
            troop1 = Troop(
                id=self.next_troop_id,
                card=card,
                hp=card.hp,
                x=column + 0 + left + right,
                y=row + (1 if player.side is Side.TOP else 0) + top + bottom,
                radius=card.radius,
                sightradius = card.sightradius,
                attack=card.attack,
                targettroop=None,
                target_is_tower=False,
                cooldown=card.attack_cooldown,
                attack_cooldown=card.attack_cooldown
            )
            troop2 = Troop(
                id=self.next_troop_id+1,
                card=card,
                hp=card.hp,
                x=column + 1.1 + left + right,
                y=row + (1 if player.side is Side.TOP else 0) + top + bottom,
                radius=card.radius,
                sightradius = card.sightradius,
                attack=card.attack,
                targettroop=None,
                target_is_tower=False,
                cooldown=card.attack_cooldown,
                attack_cooldown=card.attack_cooldown
            )
            troop3 = Troop(
                id=self.next_troop_id+2,
                card=card,
                hp=card.hp,
                x=column + 0.55 + left + right,
                y=row + (0 if player.side is Side.TOP else 1) + top + bottom,
                radius=card.radius,
                sightradius = card.sightradius,
                attack=card.attack,
                targettroop=None,
                target_is_tower=False,
                cooldown=card.attack_cooldown,
                attack_cooldown=card.attack_cooldown
            )
    
            player.troops[troop1.id] = troop1 # player.troops is a mutable dict
            player.troops[troop2.id] = troop2
            player.troops[troop3.id] = troop3
            self.next_troop_id += 3

        
        player.elixir -= card.elixir_cost
        player.selected_card = None
        return True

    # 1 game tick
    # 1. core idea. Update elixir (easy), MOVE troops toward each other (complex)
    def tick(self):
        if self.game_ended:
            return

        self.timer -= 1

        # a. elixir
        for player in self.players.values():
            player.elixir = min(
                MAX_ELIXIR,
                player.elixir + ELIXIR_PER_SECOND / FPS,
            )

        # b. i. get closest targets for each card; this is used twice, once for moving and once for attacking
        # ----------------------------------------------------
        closest_targets: dict[int, tuple[float, float, float, int | None]] = {}
        tower_left = self.arena.tower_x - TOWER_WIDTH / 2
        tower_right = self.arena.tower_x + TOWER_WIDTH / 2

        # for each player
        for player in self.players.values():
            opponent_side = (
                Side.BOTTOM if player.side is Side.TOP else Side.TOP
            )
            opponent = self.players[opponent_side]
            if player.side is Side.TOP:
                tower_top = self.arena.bottom_tower_y - TOWER_HEIGHT
                tower_bottom = self.arena.bottom_tower_y
            else:
                tower_top = self.arena.top_tower_y
                tower_bottom = self.arena.top_tower_y + TOWER_HEIGHT

            # for each troop of that player and enemy O(N^2)
            for troop in player.troops.values():
                target_x = min(max(troop.x, tower_left), tower_right)
                target_y = min(max(troop.y, tower_top), tower_bottom)

                target_id = None
                closest_distance_squared = (
                    (target_x - troop.x) ** 2 + (target_y - troop.y) ** 2
                )

                for enemy in opponent.troops.values():
                    distance_squared = (
                        (enemy.x - troop.x) ** 2 + (enemy.y - troop.y) ** 2
                    )
                    if distance_squared < closest_distance_squared and distance_squared < troop.sightradius*troop.sightradius:
                        target_x = enemy.x
                        target_y = enemy.y
                        target_id = enemy.id
                        closest_distance_squared = distance_squared

                # save closest targets for each troop per tick
                closest_targets[troop.id] = (
                    hypot(target_x - troop.x, target_y - troop.y),
                    target_x,
                    target_y,
                    target_id,
                )

        # ----------------------------------------------------

        # probably most messy part of my code.
        # b. ii. next positions of each troop move to; we save dict of next positions then move all at once, so that no weird changes ykwim.
        next_positions: dict[int, tuple[float, float]] = {}
        # damage dealt
        troop_damage: dict[int, int] = {}
        tower_damage = {
            player.side: 0 for player in self.players.values()
        }

        for player in self.players.values():
            opponent_side = (
                Side.BOTTOM if player.side is Side.TOP else Side.TOP
            )
            opponent = self.players[opponent_side]

            for troop in player.troops.values():
                


                distance, target_x, target_y, target_id = closest_targets[troop.id]

                # If a troop locks onto an enemy, it keeps attacking it even if another enemy gets closer

                # if the enemy a troop is targetting dies
                
                if troop.targettroop is not None and troop.targettroop not in opponent.troops:
                    # troop is no longer locked onto a target, reset
                    troop.targettroop = None
                    troop.target_is_tower = False

                # if the enemy a troop is targetting is still alive check if still in range
                if troop.targettroop is not None:
                    locked_target = opponent.troops[troop.targettroop]
                    locked_distance = hypot(
                        locked_target.x - troop.x,
                        locked_target.y - troop.y,
                    )
                    if locked_distance > troop.radius:
                        # troop is no longer locked onto a target, reset
                        troop.targettroop = None
                        troop.target_is_tower = False

                # 1. if enemy (targetted or just closest) in range, attack!
                if (troop.targettroop != None or troop.target_is_tower == True) or (distance <= troop.radius):
                    next_positions[troop.id] = (troop.x, troop.y)

                    if troop.cooldown > 0:
                        troop.cooldown-=1 # card starts cooldown once it's ready to attack
                        continue
                        

                    troop.cooldown = troop.attack_cooldown

                    # if a target is already locked on, do not delock it from current target
                    if troop.targettroop != None or troop.target_is_tower == True:
                        # if targetting troop
                        if troop.target_is_tower != True:
                            troop_damage[troop.targettroop] = (
                                troop_damage.get(troop.targettroop, 0) + troop.attack
                            )
                        
                        # if targetting tower
                        else:
                            target_tower = (
                                Side.BOTTOM
                                if player.side is Side.TOP
                                else Side.TOP
                            )
                            tower_damage[target_tower] += troop.attack
                        continue
                    # target general closest enemy 
                    else:
                        # if targetting troop
                        if target_id is not None:
                            troop.targettroop = target_id
                            troop.target_is_tower = False
                            troop_damage[target_id] = (
                                troop_damage.get(target_id, 0) + troop.attack
                            )
                        # if targetting tower
                        else:
                            troop.target_is_tower = True
                            target_tower = (
                                Side.BOTTOM
                                if player.side is Side.TOP
                                else Side.TOP
                            )
                            tower_damage[target_tower] += troop.attack
                        continue

                # b. iii. Also a bit weird, MOVEMENT now after all ATTACK calculations.
                move_x = target_x
                move_y = target_y

                # if need move toward bridge, which bridge is closer
                troop_bridge_y = min(max(troop.y, self.arena.river_y_top), self.arena.river_y_bottom)
                target_bridge_y = min(max(target_y, self.arena.river_y_top), self.arena.river_y_bottom)
                left_bridge_distance = hypot(troop.x - self.arena.bridge_left_x, troop.y - troop_bridge_y) + hypot(target_x - self.arena.bridge_left_x, target_y - target_bridge_y)
                right_bridge_distance = hypot(troop.x - self.arena.bridge_right_x, troop.y - troop_bridge_y) + hypot(target_x - self.arena.bridge_right_x, target_y - target_bridge_y)
                closer_bridge = self.arena.bridge_left_x if left_bridge_distance <= right_bridge_distance else self.arena.bridge_right_x

                # if troop below bridge and enemy is above bridge, then move toward bridge.
                if troop.y > self.arena.river_y_bottom and target_y <= self.arena.river_y_bottom:
                    move_x = closer_bridge
                    move_y = self.arena.river_y_bottom
                # if troop above bridge and enemy is below bridge, then move toward bridge
                elif troop.y < self.arena.river_y_top and target_y >= self.arena.river_y_top:
                    move_x = closer_bridge
                    move_y = self.arena.river_y_top

                # if in bridge and target is outside bridge on a side go to end bridge
                elif (troop.y >= self.arena.river_y_top and troop.y <= self.arena.river_y_bottom) and ((target_y < self.arena.river_y_top and troop.y > self.arena.river_y_top) or (target_y > self.arena.river_y_bottom and troop.y < self.arena.river_y_bottom)):
                    target_side = self.arena.river_y_top if target_y < self.arena.river_y_top else self.arena.river_y_bottom
                    move_x = closer_bridge
                    move_y = target_side
                # if in bridge and target is also in bridge
                elif (troop.y >= self.arena.river_y_top and troop.y <= self.arena.river_y_bottom) and (target_y >= self.arena.river_y_top and target_y <= self.arena.river_y_bottom):
                    if distance <= 6: # they are on the same bridge
                        move_x = target_x
                        move_y = target_y
                    else:
                        # just move to end of bridge depending on what side the troop is from
                        if (player.side is Side.BOTTOM):
                            move_x = closer_bridge
                            move_y = self.arena.river_y_top
                        else:
                            move_x = closer_bridge
                            move_y = self.arena.river_y_bottom
                # just move as usual
                else:
                    move_x = target_x
                    move_y = target_y

                move_distance = hypot(move_x - troop.x, move_y - troop.y)
                if move_distance == 0:
                    next_positions[troop.id] = (troop.x, troop.y)
                    continue
                movement = min(MOVEMENT_PER_TICK, move_distance)
                movement_scale = movement / move_distance
                next_positions[troop.id] = (
                    troop.x + (move_x - troop.x) * movement_scale,
                    troop.y + (move_y - troop.y) * movement_scale,
                )

        # b. iv. UPDATE ALL HP and DAMAGE
        for player in self.players.values():
            for troop in player.troops.values():
                troop.x, troop.y = next_positions[troop.id]

                # damage if existing
                damage_taken = troop_damage.get(troop.id, 0)
                troop.hp -= damage_taken
            player.tower_hp -= tower_damage[player.side]


        # b. iv. ii. END GAME IF DEAD
        top_hp = self.players[Side.TOP].tower_hp
        bottom_hp = self.players[Side.BOTTOM].tower_hp
        if top_hp <= 0 and bottom_hp <= 0:
            self.game_ended = True
            self.winner = None
        elif top_hp <= 0:
            self.game_ended = True
            self.winner = Side.BOTTOM
        elif bottom_hp <= 0:
            self.game_ended = True
            self.winner = Side.TOP
        elif self.timer <= 0:
            self.game_ended = True
            if top_hp == bottom_hp:
                self.winner = None
            else:
                self.winner = Side.TOP if top_hp > bottom_hp else Side.BOTTOM

        # b. v. if any troops are dead then delete them from the game environment.
        for player in self.players.values():
            dead_troop_ids = [
                troop.id for troop in player.troops.values() if troop.hp <= 0
            ]
            for troop_id in dead_troop_ids:
                del player.troops[troop_id]
