# python tests.py

import unittest

import numpy as np

from envs.cards import CARDS
from envs.clash_gym import (
    ClashGymEnv,
    MAX_TROOPS_PER_SIDE,
    TICKS_PER_ACTION,
    TROOP_FEATURES,
)
from envs.clash import GAME_TIME, Side


class DecodeActionTests(unittest.TestCase):
    def setUp(self):
        self.env = ClashGymEnv()

    def action_for(self, card_index, row, column):
        return 1 + card_index * self.env.num_tiles + row * self.env.game.arena.columns + column

    def test_action_space_size(self):
        self.assertEqual(self.env.num_tiles, 252)
        self.assertEqual(self.env.num_actions, 505)
        self.assertEqual(self.env.action_space.n, 505)

    def test_no_op(self):
        self.assertIsNone(self.env._decode_action(0))

    def test_decode_action_boundaries(self):
        expected = {
            1: (CARDS[0], 0, 0),
            18: (CARDS[0], 0, 17),
            19: (CARDS[0], 1, 0),
            252: (CARDS[0], 13, 17),
            253: (CARDS[1], 0, 0),
            504: (CARDS[1], 13, 17),
        }

        for action, decoded_expected in expected.items():
            with self.subTest(action=action):
                decoded = self.env._decode_action(action)
                print(f"\nAction {action}: {decoded[0].name}, row {decoded[1]}, column {decoded[2]}")
                self.assertEqual(decoded, decoded_expected)

    def test_apply_no_op(self):
        player = self.env.game.players[Side.BOTTOM]
        starting_elixir = player.elixir

        print("\nApplying no-op for bottom player.")
        placed = self.env._apply_action(Side.BOTTOM, 0)
        print(f"Placed card: {placed}")
        print(f"Troops: {len(player.troops)}")
        print(f"Elixir: {player.elixir}")

        self.assertFalse(placed)
        self.assertEqual(len(player.troops), 0)
        self.assertEqual(player.elixir, starting_elixir)

    def test_apply_bottom_goblins(self):
        bottom = self.env.game.players[Side.BOTTOM]
        top = self.env.game.players[Side.TOP]
        player = self.env.game.players[Side.BOTTOM]
        starting_elixir = player.elixir

        print("\nApplying Goblins at local row 0, column 0 for bottom player.")
        placed = self.env._apply_action(Side.BOTTOM, 1)
        print(f"Placed card: {placed}")
        print(f"Bottom troops: {len(bottom.troops)}")
        print(f"Bottom elixir: {bottom.elixir}")

        self.assertTrue(placed)
        self.assertEqual(len(bottom.troops), 4)
        self.assertEqual(len(top.troops), 0)
        self.assertEqual(bottom.elixir, starting_elixir-2) # 2 is goblins elixir
        self.assertTrue(all(troop.y >= 30 for troop in bottom.troops.values()))

    def test_apply_top_spear_goblins(self):
        top = self.env.game.players[Side.TOP]
        bottom = self.env.game.players[Side.BOTTOM]
        starting_elixir = top.elixir

        print("\nApplying Spear Goblins at local row 0, column 0 for top player.")
        placed = self.env._apply_action(Side.TOP, 253)
        print(f"Placed card: {placed}")
        print(f"Top troops: {len(top.troops)}")
        print(f"Top elixir: {top.elixir}")

        self.assertTrue(placed)
        self.assertEqual(len(top.troops), 3)
        self.assertEqual(len(bottom.troops), 0)
        self.assertEqual(top.elixir, starting_elixir-3) # 3 is spear goblins elixir
        self.assertTrue(all(troop.y <= 2 for troop in top.troops.values()))

    def test_initial_observation(self):
        observation = self.env._get_observation()
        print(f"\nInitial observation: {observation}")

        expected = np.array([1.0, 1.0, 1.0, 0.4, 0.4], dtype=np.float32)
        np.testing.assert_allclose(observation["global"], expected)
        self.assertEqual(observation["global"].dtype, np.float32)
        self.assertEqual(
            observation["own_troops"].shape,
            (MAX_TROOPS_PER_SIDE, TROOP_FEATURES),
        )
        self.assertEqual(
            observation["enemy_troops"].shape,
            (MAX_TROOPS_PER_SIDE, TROOP_FEATURES),
        )
        self.assertFalse(observation["own_troops"].any())
        self.assertFalse(observation["enemy_troops"].any())
        self.assertTrue(self.env.observation_space.contains(observation))

    def test_observation_uses_learning_player_perspective(self):
        bottom = self.env.game.players[Side.BOTTOM]
        top = self.env.game.players[Side.TOP]
        self.env.game.timer = 1500
        bottom.tower_hp = 500
        top.tower_hp = 250
        bottom.elixir = 8.0
        top.elixir = 3.0

        observation = self.env._get_observation()
        print(f"\nChanged observation: {observation}")

        expected = np.array([0.5, 0.5, 0.25, 0.8, 0.3], dtype=np.float32)
        np.testing.assert_allclose(observation["global"], expected)

    def test_observation_can_use_top_learning_player(self):
        env = ClashGymEnv(learning_side=Side.TOP)
        top = env.game.players[Side.TOP]
        bottom = env.game.players[Side.BOTTOM]
        top.tower_hp = 750
        bottom.tower_hp = 500
        top.elixir = 2.0
        bottom.elixir = 6.0

        observation = env._get_observation()

        expected = np.array([1.0, 0.75, 0.5, 0.2, 0.6], dtype=np.float32)
        np.testing.assert_allclose(observation["global"], expected)

    def test_own_goblins_are_encoded_sorted_and_padded(self):
        self.assertTrue(self.env._apply_action(Side.BOTTOM, 1))
        observation = self.env._get_observation()
        troops = observation["own_troops"]
        expected_order = sorted(
            self.env.game.players[Side.BOTTOM].troops.values(),
            key=lambda troop: (troop.y, troop.x, troop.id),
        )
        print(f"\nFirst encoded own Goblin row: {troops[0]}")

        np.testing.assert_array_equal(troops[:4, 0], np.ones(4))
        np.testing.assert_array_equal(troops[:4, 1], np.ones(4))
        np.testing.assert_array_equal(troops[:4, 2], np.zeros(4))
        self.assertFalse(troops[4:].any())

        for slot, troop in enumerate(expected_order):
            self.assertAlmostEqual(troops[slot, 3], troop.x / self.env.game.arena.columns)
            self.assertAlmostEqual(troops[slot, 4], troop.y / self.env.game.arena.rows)
            self.assertEqual(troops[slot, 5], 1.0)
            self.assertEqual(troops[slot, 6], 1.0)

        self.assertTrue(self.env.observation_space.contains(observation))

    def test_enemy_spear_goblins_use_enemy_array_and_reverse_y_sort(self):
        self.assertTrue(self.env._apply_action(Side.TOP, 253))
        observation = self.env._get_observation()
        own_troops = observation["own_troops"]
        enemy_troops = observation["enemy_troops"]
        expected_order = sorted(
            self.env.game.players[Side.TOP].troops.values(),
            key=lambda troop: (-troop.y, troop.x, troop.id),
        )
        print(f"\nFirst encoded enemy Spear Goblin row: {enemy_troops[0]}")

        self.assertFalse(own_troops.any())
        np.testing.assert_array_equal(enemy_troops[:3, 0], np.ones(3))
        np.testing.assert_array_equal(enemy_troops[:3, 1], np.zeros(3))
        np.testing.assert_array_equal(enemy_troops[:3, 2], np.ones(3))
        self.assertFalse(enemy_troops[3:].any())

        for slot, troop in enumerate(expected_order):
            self.assertAlmostEqual(enemy_troops[slot, 3], troop.x / self.env.game.arena.columns)
            self.assertAlmostEqual(enemy_troops[slot, 4], troop.y / self.env.game.arena.rows)

    def test_troop_hp_and_cooldown_are_normalized(self):
        self.assertTrue(self.env._apply_action(Side.BOTTOM, 1))
        ordered_troops = sorted(
            self.env.game.players[Side.BOTTOM].troops.values(),
            key=lambda troop: (troop.y, troop.x, troop.id),
        )
        ordered_troops[0].hp = ordered_troops[0].card.hp / 2
        ordered_troops[0].cooldown = ordered_troops[0].attack_cooldown / 2

        troop_row = self.env._get_observation()["own_troops"][0]
        print(f"\nDamaged troop row: {troop_row}")

        self.assertEqual(troop_row[5], 0.5)
        self.assertEqual(troop_row[6], 0.5)
        self.assertFalse(troop_row[7:].any())

    def test_living_troop_target_is_encoded_with_coordinates(self):
        self.assertTrue(self.env._apply_action(Side.BOTTOM, 1))
        self.assertTrue(self.env._apply_action(Side.TOP, 253))
        bottom = self.env.game.players[Side.BOTTOM]
        top = self.env.game.players[Side.TOP]
        attacker = sorted(
            bottom.troops.values(),
            key=lambda troop: (troop.y, troop.x, troop.id),
        )[0]
        target = next(iter(top.troops.values()))
        attacker.targettroop = target.id
        attacker.target_is_tower = False

        troop_row = self.env._get_observation()["own_troops"][0]
        print(f"\nTroop-target row: {troop_row}")

        self.assertEqual(troop_row[7], 1.0)
        self.assertEqual(troop_row[8], 0.0)
        self.assertAlmostEqual(troop_row[9], target.x / self.env.game.arena.columns)
        self.assertAlmostEqual(troop_row[10], target.y / self.env.game.arena.rows)

    def test_tower_target_sets_only_tower_feature(self):
        self.assertTrue(self.env._apply_action(Side.BOTTOM, 1))
        bottom = self.env.game.players[Side.BOTTOM]
        attacker = sorted(
            bottom.troops.values(),
            key=lambda troop: (troop.y, troop.x, troop.id),
        )[0]
        attacker.targettroop = None
        attacker.target_is_tower = True

        troop_row = self.env._get_observation()["own_troops"][0]
        print(f"\nTower-target row: {troop_row}")

        self.assertEqual(troop_row[7], 0.0)
        self.assertEqual(troop_row[8], 1.0)
        self.assertEqual(troop_row[9], 0.0)
        self.assertEqual(troop_row[10], 0.0)

    def test_missing_target_id_is_encoded_as_no_living_target(self):
        self.assertTrue(self.env._apply_action(Side.BOTTOM, 1))
        self.assertTrue(self.env._apply_action(Side.TOP, 253))
        bottom = self.env.game.players[Side.BOTTOM]
        top = self.env.game.players[Side.TOP]
        attacker = sorted(
            bottom.troops.values(),
            key=lambda troop: (troop.y, troop.x, troop.id),
        )[0]
        dead_target = next(iter(top.troops.values()))
        attacker.targettroop = dead_target.id
        del top.troops[dead_target.id]

        troop_row = self.env._get_observation()["own_troops"][0]
        print(f"\nMissing-target row: {troop_row}")

        self.assertEqual(troop_row[7], 0.0)
        self.assertEqual(troop_row[9], 0.0)
        self.assertEqual(troop_row[10], 0.0)

    def test_initial_action_mask(self):
        mask = self.env._get_action_mask()
        print(f"\nInitial legal actions: {int(mask.sum())} / {len(mask)}")

        self.assertEqual(mask.shape, (505,))
        self.assertEqual(mask.dtype, np.int8)
        self.assertEqual(mask[0], 1)
        self.assertEqual(int(mask.sum()), 473)

        bottom_tower_action = self.action_for(0, 0, 8)
        bridge_action = self.action_for(0, 13, 8)
        self.assertEqual(mask[bottom_tower_action], 0)
        self.assertEqual(mask[bridge_action], 1)

    def test_top_learning_player_masks_top_tower(self):
        env = ClashGymEnv(learning_side=Side.TOP)
        mask = env._get_action_mask()
        top_tower_action = 1 + 0 * env.num_tiles + 0 * env.game.arena.columns + 8
        bridge_action = 1 + 0 * env.num_tiles + 13 * env.game.arena.columns + 8

        self.assertEqual(int(mask.sum()), 473)
        self.assertEqual(mask[top_tower_action], 0)
        self.assertEqual(mask[bridge_action], 1)

    def test_action_mask_respects_elixir(self):
        bottom = self.env.game.players[Side.BOTTOM]
        bottom.elixir = 2.0
        mask = self.env._get_action_mask()
        print(f"\nLegal actions with 2 elixir: {int(mask.sum())} / {len(mask)}")

        legal_goblin_action = self.action_for(0, 13, 0)
        spear_goblin_action = self.action_for(1, 13, 0)
        self.assertEqual(mask[legal_goblin_action], 1)
        self.assertEqual(mask[spear_goblin_action], 0)
        self.assertEqual(int(mask.sum()), 237)

        bottom.elixir = 1.0
        mask = self.env._get_action_mask()
        self.assertEqual(int(mask.sum()), 1)

    def test_action_mask_after_game_ends(self):
        self.env.game.game_ended = True
        mask = self.env._get_action_mask()

        self.assertEqual(mask[0], 1)
        self.assertEqual(int(mask.sum()), 1)

    def test_reset_returns_fresh_game_observation_and_mask(self):
        old_game = self.env.game
        self.env.game.timer = 100
        self.env.game.players[Side.BOTTOM].elixir = 0.0
        self.env.scripted_opponent_next_card_index = 1

        observation, info = self.env.reset()
        print(f"\nReset observation: {observation}")
        print(f"Reset legal actions: {int(info['action_mask'].sum())}")

        self.assertIsNot(self.env.game, old_game)
        np.testing.assert_allclose(
            observation["global"],
            np.array([1.0, 1.0, 1.0, 0.4, 0.4], dtype=np.float32),
        )
        self.assertEqual(self.env.scripted_opponent_next_card_index, 0)
        np.testing.assert_array_equal(info["action_mask"], self.env._get_action_mask())

    def test_scripted_opponent_alternates_only_after_placement(self):
        top = self.env.game.players[Side.TOP]

        print("\nScripted opponent attempts Goblins.")
        self.assertTrue(self.env.place_scripted_action())
        self.assertEqual(len(top.troops), 4)
        self.assertEqual(top.elixir, 2.0)
        self.assertEqual(self.env.scripted_opponent_next_card_index, 1)

        print("Scripted opponent cannot yet afford Spear Goblins.")
        self.assertFalse(self.env.place_scripted_action())
        self.assertEqual(len(top.troops), 4)
        self.assertEqual(self.env.scripted_opponent_next_card_index, 1)

        top.elixir = 3.0
        print("Scripted opponent now places Spear Goblins.")
        self.assertTrue(self.env.place_scripted_action())
        self.assertEqual(len(top.troops), 7)
        self.assertEqual(top.elixir, 0.0)
        self.assertEqual(self.env.scripted_opponent_next_card_index, 0)

    def test_scripted_opponent_placement_mirrors_for_bottom(self):
        env = ClashGymEnv(learning_side=Side.TOP)
        bottom = env.game.players[Side.BOTTOM]

        self.assertTrue(env.place_scripted_action())

        self.assertEqual(len(bottom.troops), 4)
        self.assertTrue(all(troop.y >= 19 for troop in bottom.troops.values()))

    def test_step_applies_both_actions_and_advances_five_ticks(self):
        bottom = self.env.game.players[Side.BOTTOM]
        top = self.env.game.players[Side.TOP]

        observation, reward, terminated, truncated, info = self.env.step(1)
        print(f"\nTimer after one environment step: {self.env.game.timer}")
        print(f"Bottom troops: {len(bottom.troops)}, top troops: {len(top.troops)}")

        self.assertEqual(self.env.game.timer, GAME_TIME - 5)
        self.assertEqual(len(bottom.troops), 4)
        self.assertEqual(len(top.troops), 4)
        self.assertEqual(reward, 0.0)
        self.assertFalse(terminated)
        self.assertFalse(truncated)
        self.assertTrue(self.env.observation_space.contains(observation))
        np.testing.assert_array_equal(info["action_mask"], self.env._get_action_mask())

    def test_step_stops_ticking_when_game_terminates(self):
        self.env.game.timer = 2

        observation, reward, terminated, truncated, info = self.env.step(0)
        print(f"\nTerminal timer: {self.env.game.timer}")

        self.assertEqual(self.env.game.timer, 0)
        self.assertEqual(observation["global"][0], 0.0)
        self.assertEqual(reward, 0.0)
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertEqual(int(info["action_mask"].sum()), 1)

    def test_random_legal_actions_complete_a_match(self):
        rng = np.random.default_rng(0)
        observation, info = self.env.reset(seed=0)
        terminated = False
        truncated = False
        decisions = 0

        while not (terminated or truncated):
            legal_actions = np.flatnonzero(info["action_mask"])
            action = int(rng.choice(legal_actions))
            observation, reward, terminated, truncated, info = self.env.step(action)
            decisions += 1

        print(f"\nRandom legal-action match ended after {decisions} decisions.")

        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertLessEqual(decisions, GAME_TIME // TICKS_PER_ACTION)
        self.assertTrue(self.env.observation_space.contains(observation))



if __name__ == "__main__":
    unittest.main()
