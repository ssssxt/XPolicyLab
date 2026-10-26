"""Benchmark isolation, public API forwarding and download-selection checks."""
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from .. import model
from ..benchmarks import POLICY_DIR, resolve_config
from ..download import route


def config(bench="RoboTwin", robot="arx_x5", **kwargs):
    return dict(bench_name=bench, env_cfg_type=robot, action_type="joint", **kwargs)


class UnifiedTests(unittest.TestCase):
    def test_profiles_and_overrides(self):
        twin = resolve_config(config())
        for robot in ("arx_x5", "piper", "piper_x"):
            dojo = resolve_config(config("RoboDojo", robot))
            self.assertEqual(dojo["expected_step"], 40000)
            self.assertEqual(dojo["runtime_mode"], "joint96_real_phoenix")
            self.assertTrue(dojo["eval_batch"])
            self.assertEqual((dojo["replan_steps"], dojo["num_inference_steps"]), (32, 10))
        self.assertFalse(twin["eval_batch"])
        self.assertNotIn("runtime_mode", twin)
        custom = resolve_config(config("robotwin", replan_steps=16, num_inference_steps=7))
        self.assertEqual((custom["replan_steps"], custom["num_inference_steps"]), (16, 7))
        self.assertEqual(resolve_config(config())["replan_steps"], 32)

    def test_reject_wrong_family_and_missing_benchmark(self):
        bad = [config("RoboTwin", "piper"), config("other"), config(None),
               config(replan_steps=33), config(num_inference_steps=0),
               {**config(), "action_type": "ee"}]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_config(value)

    def test_forwarding_and_runtime_isolation(self):
        for bench in ("RoboTwin", "RoboDojo"):
            backend = Mock()
            factory = Mock(return_value=backend)
            with patch.object(model, "_active_benchmark", None), patch.object(
                model, "import_module", return_value=SimpleNamespace(Model=factory)
            ) as importer:
                wrapper = model.Model(config(bench))
                importer.assert_called_once_with(model._implementations[bench], model.__package__)
                for name, args in (("update_obs", ({"env_idx": 4},)),
                                   ("update_obs_batch", ([{"env_idx": 9}],)),
                                   ("get_action", ()), ("get_action_batch", ([9, 4],)),
                                   ("reset", ()), ("prepare_case", ({"case": 1},)),
                                   ("on_trial_end", ({"success": True},)),
                                   ("get_timing_rollout", ())):
                    result = getattr(wrapper, name)(*args)
                    getattr(backend, name).assert_called_once_with(*args)
                    self.assertIs(result, getattr(backend, name).return_value)
                other = "RoboDojo" if bench == "RoboTwin" else "RoboTwin"
                with self.assertRaisesRegex(RuntimeError, "separate policy-server"):
                    model.Model(config(other))

    def test_download_selection(self):
        self.assertEqual(route([])[0], ".runtime.checkpoints")
        self.assertEqual(route(["--pretrain-only"])[1].name, "phoenix-pretrain-256013")
        for args in (["weights", "--benchmark", "RoboDojo"],
                     ["--benchmark", "RoboDojo", "weights"]):
            module, root, flags = route(args)
            self.assertEqual((module, root, flags),
                             (".robodojo.joint96_assets", Path("weights"), ["--download"]))
        module, root, flags = route(["--benchmark", "RoboDojo", "--robot-type", "piper_x"])
        self.assertEqual(root, POLICY_DIR / "checkpoints/phoenix-robodojo-edge25-40k")
        self.assertEqual(flags, ["--download", "--robot-type", "piper_x"])
        self.assertNotIn("--download", route(["--benchmark", "RoboDojo", "--preflight"])[2])
        self.assertNotIn("--download", route(["--benchmark", "RoboDojo", "--verify-remote"])[2])

    def test_robodojo_checkpoint_root_is_shared(self):
        from ..robodojo.checkpoint_paths import POLICY_DIR as dojo_root
        self.assertEqual(dojo_root, POLICY_DIR)


if __name__ == "__main__":
    unittest.main()
