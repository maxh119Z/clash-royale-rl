"""Card definitions for the Clash Royale environment."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    """A card's rules-facing identity and cost."""

    name: str
    elixir_cost: int
    hp: int
    card_type: str
    image_filename: str
    top_troop_image: str
    bottom_troop_image: str
    radius: int


GOBLINS = Card(
    name="Goblins",
    elixir_cost=4,
    hp= 100,
    card_type="troop",
    image_filename="goblins.png",
    top_troop_image = "troops/top_goblin.png",
    bottom_troop_image = "troops/bottom_goblin.png",
    radius = 1
)

SPEAR_GOBLINS = Card(
    name="Spear Goblins",
    elixir_cost=4,
    hp= 50,
    card_type="troop",
    image_filename="spear_goblins.png",
    top_troop_image = "troops/top_speargoblin.png",
    bottom_troop_image = "troops/bottom_speargoblin.png",
    radius = 4
)

CARDS = (GOBLINS, SPEAR_GOBLINS)
