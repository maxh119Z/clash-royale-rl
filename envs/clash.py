"""Core state for the Clash Royale environment."""

from dataclasses import dataclass, field
from enum import Enum
from math import hypot

from envs.cards import CARDS, Card

FPS = 30
ROWS = 32
COLUMNS = 18

MAX_ELIXIR = 10.0
STARTING_ELIXIR = 2.0
ELIXIR_PER_SECOND = 1.0
MOVEMENT_PER_TICK = 1 / FPS


class Side(Enum):
    """The two fixed sides of the arena."""

    TOP = "top"
    BOTTOM = "bottom"


@dataclass(frozen=True)
class Arena:
    """The arena's logical dimensions, measured in tiles."""

    rows: int = ROWS
    columns: int = COLUMNS
    tower_x: float = COLUMNS / 2
    top_tower_y: float = 0.0
    bottom_tower_y: float = float(ROWS)


@dataclass
class Troop:
    """A troop positioned in continuous tile coordinates."""

    id: int
    card: Card
    hp: int
    x: float
    y: float
    radius: int


@dataclass
class Player:
    """The cards, elixir, and tower state belonging to one side."""

    cards: list[Card]
    selected_card: Card | None = None
    elixir: float = STARTING_ELIXIR
    tower_hp: int | None = None
    troops: dict[int, Troop] = field(default_factory=dict)


class ClashGame:
    """Headless state for a two-player game."""

    def __init__(self):
        self.arena = Arena()
        self.next_troop_id = 0
        self.players: dict[Side, Player] = {
            Side.TOP: Player(cards=list(CARDS)),
            Side.BOTTOM: Player(cards=list(CARDS)),
        }

    def place_selected_card(self, side: Side, row: int, column: int) -> bool:
        player = self.players[side]
        card = player.selected_card

        if card is None:
            return False
        if not (0 <= row < self.arena.rows and 0 <= column < self.arena.columns):
            return False
        if player.elixir < card.elixir_cost:
            return False

        troop = Troop(
            id=self.next_troop_id,
            card=card,
            hp=card.hp,
            x=column + 0.5,
            y=row + 0.5,
            radius = card.radius
        )
        player.troops[troop.id] = troop
        self.next_troop_id += 1
        player.elixir -= card.elixir_cost
        player.selected_card = None
        return True

    def tick(self):
        for side, player in self.players.items():
            player.elixir = min(
                MAX_ELIXIR,
                player.elixir + ELIXIR_PER_SECOND / FPS,
            )

        next_positions: dict[int, tuple[float, float]] = {}

        for side, player in self.players.items():
            if side is Side.TOP:
                opponent = self.players[Side.BOTTOM]
                tower_y = self.arena.bottom_tower_y
            else:
                opponent = self.players[Side.TOP]
                tower_y = self.arena.top_tower_y

            for troop in player.troops.values():
                target_x = self.arena.tower_x
                target_y = tower_y
                closest_distance_squared = (
                    (target_x - troop.x) ** 2 + (target_y - troop.y) ** 2
                )

                for enemy in opponent.troops.values():
                    distance_squared = (
                        (enemy.x - troop.x) ** 2 + (enemy.y - troop.y) ** 2
                    )
                    if distance_squared < closest_distance_squared:
                        target_x = enemy.x
                        target_y = enemy.y
                        closest_distance_squared = distance_squared

                dx = target_x - troop.x
                dy = target_y - troop.y
                distance = hypot(dx, dy)

                print(troop.radius)

                if distance == 0 or distance <= troop.radius:
                    next_positions[troop.id] = (troop.x, troop.y)
                elif distance <= MOVEMENT_PER_TICK and distance >= troop.radius:
                    next_positions[troop.id] = (target_x, target_y)
                else:
                    movement_scale = MOVEMENT_PER_TICK / distance
                    next_positions[troop.id] = (
                        troop.x + dx * movement_scale,
                        troop.y + dy * movement_scale,
                    )

        for player in self.players.values():
            for troop in player.troops.values():
                troop.x, troop.y = next_positions[troop.id]
