# I decided to separate this from the core game environment because we may add a lot more cards

from dataclasses import dataclass

@dataclass(frozen=True)
class Card:
    # set up card object
    name: str
    elixir_cost: int
    hp: int
    attack: int
    card_type: str
    image_filename: str
    top_troop_image: str
    bottom_troop_image: str
    radius: int
    sightradius: int
    attack_cooldown: int # number of ticks


GOBLINS = Card(
    name="Goblins",
    elixir_cost=2,
    hp= 100,
    attack = 25,
    card_type="troop",
    image_filename="goblins.png",
    top_troop_image = "troops/top_goblin.png",
    bottom_troop_image = "troops/bottom_goblin.png",
    radius = 0.5,
    sightradius = 5.5,
    attack_cooldown=29,
)

SPEAR_GOBLINS = Card(
    name="Spear Goblins",
    elixir_cost=3,
    attack = 34,
    hp= 50,
    card_type="troop",
    image_filename="spear_goblins.png",
    top_troop_image = "troops/top_speargoblin.png",
    bottom_troop_image = "troops/bottom_speargoblin.png",
    radius = 4,
    sightradius = 5.5,
    attack_cooldown=29,
)

CARDS = (GOBLINS, SPEAR_GOBLINS)
