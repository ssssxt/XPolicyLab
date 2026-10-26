"""Select an explicit benchmark before importing either model runtime."""

from pathlib import Path

POLICY_DIR = Path(__file__).resolve().parent
ROBOTS = {"RoboTwin": ("arx_x5",), "RoboDojo": ("arx_x5", "piper", "piper_x")}


def benchmark_name(value):
    names = {name.lower(): name for name in ROBOTS}
    name = names.get(str(value or "").strip().lower())
    if name is None:
        raise ValueError("bench_name must explicitly be RoboTwin or RoboDojo")
    return name


def resolve_config(config):
    import yaml

    name = benchmark_name(config.get("bench_name"))
    defaults = yaml.safe_load((POLICY_DIR / "configs" / (name.lower() + ".yml")).read_text())
    defaults.update({k: v for k, v in config.items() if v is not None})
    defaults["bench_name"] = name
    if defaults.get("env_cfg_type") not in ROBOTS[name]:
        raise ValueError(f"{name} supports env_cfg_type={ROBOTS[name]}")
    if defaults.get("action_type") != "joint":
        raise ValueError("Phoenix-MWA supports action_type=joint")
    if not 1 <= int(defaults["replan_steps"]) <= 32:
        raise ValueError("replan_steps must be between 1 and 32")
    if int(defaults["num_inference_steps"]) < 1:
        raise ValueError("num_inference_steps must be positive")
    return defaults
