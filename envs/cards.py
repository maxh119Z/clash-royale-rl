"""Card definitions for the Clash Royale environment."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    """A card's rules-facing identity and cost."""

    name: str
    elixir_cost: int
    card_type: str
    image_filename: str


GOBLINS = Card(
    name="Goblins",
    elixir_cost=2,
    card_type="troop",
    image_filename="goblins.png",
)

SPEAR_GOBLINS = Card(
    name="Spear Goblins",
    elixir_cost=2,
    card_type="troop",
    image_filename="spear_goblins.png",
)

CARDS = (GOBLINS, SPEAR_GOBLINS)
