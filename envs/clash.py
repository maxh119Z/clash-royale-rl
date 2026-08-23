"""Core state for the Clash Royale environment."""

from dataclasses import dataclass
from enum import Enum

from envs.cards import CARDS, Card

FPS = 30
ROWS = 32
COLUMNS = 18

MAX_ELIXIR = 10.0
STARTING_ELIXIR = 2.0
ELIXIR_PER_SECOND = 1.0


class Side(Enum):
    """The two fixed sides of the arena."""

    TOP = "top"
    BOTTOM = "bottom"


@dataclass(frozen=True)
class Arena:
    """The arena's logical dimensions, measured in tiles."""

    rows: int = ROWS
    columns: int = COLUMNS


@dataclass
class Player:
    """The cards, elixir, and tower state belonging to one side."""

    cards: list[Card]
    elixir: float = STARTING_ELIXIR
    tower_hp: int | None = None


class ClashGame:
    """Headless state for a two-player game."""

    def __init__(self):
        self.arena = Arena()
        self.players: dict[Side, Player] = {
            Side.TOP: Player(cards=list(CARDS)),
            Side.BOTTOM: Player(cards=list(CARDS)),
        }

    def tick(self):
        for side, player in self.players.items():
            player.elixir = min(
                MAX_ELIXIR,
                player.elixir + ELIXIR_PER_SECOND / FPS,
            )
            print(f"{side.value}: {player.elixir:.2f}")
