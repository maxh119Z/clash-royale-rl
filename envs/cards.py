"""Card definitions for the Clash Royale environment."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    """A card's rules-facing identity and cost."""

    name: str
    elixir_cost: int
    card_type: str
