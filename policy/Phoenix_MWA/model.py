"""One XPolicyLab entry point for the two independently released policies."""

from importlib import import_module
from threading import Lock

from XPolicyLab.model_template import ModelTemplate
from .benchmarks import resolve_config

_active_benchmark = None
_runtime_lock = Lock()
_implementations = {"RoboTwin": ".robotwin", "RoboDojo": ".robodojo.model"}


class Model(ModelTemplate):
    """Route observations to the original benchmark-specific implementation.

    Each benchmark runs in its own policy-server process because both releases
    vendor a Python package called ``wam`` with different inference contracts.
    """

    def __init__(self, model_cfg):
        global _active_benchmark
        self.cfg = resolve_config(model_cfg)
        name = self.cfg["bench_name"]
        with _runtime_lock:
            if _active_benchmark not in (None, name):
                raise RuntimeError("Use separate policy-server processes for RoboTwin and RoboDojo")
            # Retain this claim after a failed load: imported runtime modules may remain.
            _active_benchmark = name
        backend = import_module(_implementations[name], __package__)
        self.backend = backend.Model(self.cfg)

    def update_obs(self, obs):
        return self.backend.update_obs(obs)

    def update_obs_batch(self, obs_list):
        return self.backend.update_obs_batch(obs_list)

    def get_action(self):
        return self.backend.get_action()

    def get_action_batch(self, env_idx_list=None):
        return self.backend.get_action_batch(env_idx_list)

    def reset(self):
        return self.backend.reset()

    def prepare_case(self, case_meta=None):
        return self.backend.prepare_case(case_meta)

    def on_trial_end(self, result=None):
        return self.backend.on_trial_end(result)

    def get_timing_rollout(self):
        method = getattr(self.backend, "get_timing_rollout", None)
        return method() if method else {}
