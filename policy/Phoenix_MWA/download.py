"""Download a selected benchmark's independently verified model release."""

import argparse
import sys
from pathlib import Path
from .benchmarks import POLICY_DIR, benchmark_name


def route(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--benchmark", default="RoboTwin", type=benchmark_name)
    args, remaining = parser.parse_known_args(argv)
    root_arg = Path(remaining.pop(0)) if remaining and not remaining[0].startswith("-") else None
    if args.benchmark == "RoboTwin":
        root = root_arg or POLICY_DIR / "checkpoints" / (
            "phoenix-pretrain-256013" if "--pretrain-only" in remaining else "phoenix-robotwin-35k"
        )
        return ".runtime.checkpoints", root, remaining
    if "--pretrain-only" in remaining or "--training-backbones" in remaining:
        parser.error("Pretraining and training backbones use --benchmark RoboTwin")
    root = root_arg or POLICY_DIR / "checkpoints/phoenix-robodojo-edge25-40k"
    modes = ("--verify-remote", "--preflight")
    if "--preflight" in remaining:
        remaining.remove("--preflight")
    elif not any(mode in remaining for mode in modes) and "--help" not in remaining:
        remaining.insert(0, "--download")
    return ".robodojo.joint96_assets", root, remaining


def main(argv=None):
    import runpy

    argv = list(sys.argv[1:] if argv is None else argv)
    if "--help" in argv or "-h" in argv:
        print("Usage: download_checkpoint.sh [ROOT] --benchmark {RoboTwin,RoboDojo} [OPTIONS]", flush=True)
        print("RoboTwin: --verify-only, --pretrain-only, --training-backbones", flush=True)
        print("RoboDojo: --robot-type {arx_x5,piper,piper_x}, --preflight, --verify-remote", flush=True)

    module, root, remaining = route(argv)
    sys.argv = [sys.argv[0], str(root), *remaining]
    runpy.run_module(__package__ + module, run_name="__main__")


if __name__ == "__main__":
    main()
