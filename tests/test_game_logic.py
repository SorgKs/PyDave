import unittest
from unittest.mock import patch

import anims
import anims.dave as dave
import levels
import tilemap
from engine import objects, physics


class ObjectFactoryTests(unittest.TestCase):
    def test_factory_applies_init_dimensions_before_center_offsets(self):
        object_type = {
            "init": lambda obj, params: obj.update(w=2.0, h=4.0),
            "behave": None,
            "transform": None,
            "sprites_map": None,
            "hitbox": (1.0, 1.0),
            "anchor_type": "center",
            "layer": anims.LAYER_NONE,
            "tags": [],
            "has_gravity": False,
            "has_friction": False,
        }
        with patch.dict(anims.OBJECT_TYPES, {"test_actor": object_type}):
            obj = anims.create_object("test_actor", 3, 5)

        self.assertEqual((obj["w"], obj["h"]), (2.0, 4.0))
        self.assertEqual((obj["hitbox_offset_x"], obj["hitbox_offset_y"]), (-1.0, -2.0))

    def test_factory_rejects_unknown_type(self):
        with self.assertRaisesRegex(ValueError, "missing_type"):
            anims.create_object("missing_type", 0, 0)


class LevelParsingTests(unittest.TestCase):
    def test_map_symbols_create_objects_and_decor_at_tile_coordinates(self):
        parsed = levels.parse_objects(["ASZG^THDdK"])

        self.assertEqual(parsed["spawn_pos"], (1.5, 1.0))
        self.assertEqual([obj["type"] for obj in parsed["objects"]], ["dave", "zombie", "goblin"])
        self.assertEqual(parsed["spikes"], [{"x": 4.0, "y": 0.0}])
        self.assertEqual(parsed["hearts"], [{"x": 6.0, "y": 0.0, "taken": False}])
        self.assertEqual(parsed["door"], {"x": 7.0, "y": -1.0, "open": 0.0})
        self.assertEqual(parsed["key_pos"], (9.0, 0.0))

    def test_tilemap_converts_wall_runs_and_stairs(self):
        with patch.object(tilemap.lvl, "MAP", ["....", "LLRR", "----XX"]):
            built = tilemap.TileMap()
            built.build()

        self.assertEqual(built.grid[1][:4], ["wall_left_a", "wall_left_b", "wall_right_a", "wall_right_b"])
        self.assertEqual(built.grid[2][:4], ["step_00", "step_01", "step_03", "step_04"])


class PhysicsTests(unittest.TestCase):
    @staticmethod
    def actor(x, layer=objects.LAYER_NONE, tags=None):
        return {
            "x": x, "y": 1.0, "vx": 0.0, "vy": 0.0,
            "w": 1.0, "h": 1.0, "hitbox_offset_x": 0.0,
            "hitbox_offset_y": 0.0, "onG": False, "drop": 0,
            "layer": layer, "tags": tags or [], "collisions": [],
            "has_gravity": True, "has_friction": False,
        }

    def test_actor_lands_on_solid_tile_and_records_floor(self):
        physics.init_physics([[0, 0, 0], [0, 0, 0], [1, 1, 1]], 3, 3)
        actor = self.actor(1.0)
        actor["y"] = 2.0
        actor["hitbox_offset_y"] = -1.0

        physics.update_physics([actor])

        self.assertTrue(actor["onG"])
        self.assertEqual(actor["vy"], 0.0)
        self.assertIn({"kind": "floor"}, actor["collisions"])

    def test_player_enemy_overlap_is_reported_to_both_objects(self):
        player = self.actor(1.0, objects.LAYER_PLAYER, ["player"])
        enemy = self.actor(1.75, objects.LAYER_ENEMY, ["enemy"])

        physics.resolve_object_collisions([player, enemy])

        self.assertTrue(any(c["kind"] == "object" and c["target"] is enemy for c in player["collisions"]))
        self.assertTrue(any(c["kind"] == "object" and c["target"] is player for c in enemy["collisions"]))


class WeaponTests(unittest.TestCase):
    def setUp(self):
        self.player = anims.create_object("dave", 2.0, 2.0)
        self.player["onG"] = True
        self.map_grid = [[0] * 20 for _ in range(10)]

    def test_shot_fires_after_animation_delay_and_spends_one_shell(self):
        dave.behave(self.player, {"s+"}, self.map_grid, [self.player])
        self.assertTrue(self.player["pending_shoot"])
        self.assertEqual(self.player["ammo"], 2)

        for _ in range(dave._weapon(self.player)["shoot_anim_speed"]):
            dave.behave(self.player, set(), self.map_grid, [self.player])
            dave.fire_shot_if_ready(self.player, self.map_grid, [self.player])

        self.assertFalse(self.player["pending_shoot"])
        self.assertEqual(self.player["ammo"], 1)
        self.assertLess(self.player["vx"], 0.0)

    def test_idle_reload_refills_empty_double_barrel(self):
        self.player["ammo"] = 0

        for _ in range(dave.IDLETIMEOUT_FRAMES):
            dave.behave(self.player, set(), self.map_grid, [self.player])
        self.assertTrue(self.player["reloading"])

        for _ in range(dave.RELOAD_ANIM_SPEED * self.player["reload_len"] + 1):
            dave.behave(self.player, set(), self.map_grid, [self.player])

        self.assertEqual(self.player["ammo"], self.player["max_ammo"])
        self.assertFalse(self.player["reloading"])


if __name__ == "__main__":
    unittest.main()
