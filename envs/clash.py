"""Core state for the Clash Royale environment."""

from dataclasses import dataclass
from enum import Enum

from envs.cards import Card


MAX_ELIXIR = 10.0
STARTING_ELIXIR = 5.0
DEFAULT_CARD_SLOTS = 2


class Side(Enum):
    """The two fixed sides of the arena."""

    TOP = "top"
    BOTTOM = "bottom"


@dataclass(frozen=True)
class Arena:
    """The arena's logical dimensions, measured in tiles."""

    rows: int = 32
    columns: int = 18


@dataclass
class Player:
    """The cards, elixir, and tower state belonging to one side."""

    cards: list[Card | None]
    elixir: float = STARTING_ELIXIR
    tower_hp: int | None = None


class ClashGame:
    """Headless state for a two-player game."""

    def __init__(self, num_card_slots: int = DEFAULT_CARD_SLOTS):
        if num_card_slots < 1:
            raise ValueError("Each player must have at least one card slot")

        self.arena = Arena()
        self.num_card_slots = num_card_slots
        self.players: dict[Side, Player] = {}
        self.reset()

    def reset(self) -> Arena:
        """Reset both players and return the empty arena."""
        self.players = {
            side: Player(cards=[None] * self.num_card_slots) for side in Side
        }
        return self.arena
