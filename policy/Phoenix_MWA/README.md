# Phoenix-MWA · RoboTwin and RoboDojo

One XPolicyLab policy directory supports both benchmarks. `bench_name` selects the original benchmark-specific runtime, configuration and weights.

| Benchmark | Robots | Released policy | Image preprocessing | Normalization |
| --- | --- | --- | --- | --- |
| RoboTwin 2.0 | `arx_x5` | 35K posttraining | Source aspect resize and center crop | z-score |
| RoboDojo real | `arx_x5`, `piper`, `piper_x` | H5 online no-crop edge25, 40K per robot | Bicubic resize each complete view to 256×256 | Per-robot q01/q99, forward clip to ±5 |

Both use joint actions, **32 executed actions per replan and 10 denoising steps** by default. The single-frame image passes through the original repeat-nine/full-encoder path. Each benchmark keeps its own action mapping, statistics and text conditioning.

## Installation

```bash
cd XPolicyLab/policy/Phoenix_MWA
bash install.sh phoenix-mwa
conda activate phoenix-mwa
```

Use the benchmark's separate simulator/client environment. Run each benchmark in a separate policy-server process: the bundled runtimes contain different versions of the `wam` package. Both servers may use the same Conda environment.

### Checkpoints

RoboTwin downloads the pinned [35K release](https://huggingface.co/AnyverseDynamics/Phoenix-RoboTwin) and its encoder, VAE and text dependencies:

```bash
bash download_checkpoint.sh checkpoints/phoenix-robotwin-35k --benchmark RoboTwin
# Verify the existing download:
bash download_checkpoint.sh checkpoints/phoenix-robotwin-35k --benchmark RoboTwin --verify-only
```

RoboDojo downloads the three robot policies and shared dependencies from [ssuuuuu/phoenix-mwa](https://www.modelscope.cn/models/ssuuuuu/phoenix-mwa/files):

```bash
bash download_checkpoint.sh checkpoints/phoenix-robodojo-edge25-40k --benchmark RoboDojo
# Download/preflight one robot only:
bash download_checkpoint.sh checkpoints/phoenix-robodojo-edge25-40k --benchmark RoboDojo --robot-type piper
bash download_checkpoint.sh checkpoints/phoenix-robodojo-edge25-40k --benchmark RoboDojo --robot-type piper --preflight
```

Download filenames, sizes and SHA256 values are recorded in `runtime/weights_manifest.json` and `robodojo/phoenix_release.json`. The latter retains the original local asset names required by its inference configuration; remote repository and filenames use `phoenix-mwa`. Do not mix the two checkpoint directories or substitute weights across robots.

The [Joint96 pretraining checkpoint (256013 steps)](https://www.modelscope.cn/api/v1/models/ssuuuuu/phoenix-mwa/repo?Revision=master&FilePath=phoenix-mwa-pretrain-joint96-step_256013.pt) has a separate download:

```bash
bash download_checkpoint.sh checkpoints/phoenix-pretrain-256013 --benchmark RoboTwin --pretrain-only
```

This downloads the replacement checkpoint with SHA256 `5ed256c1d34650d689639b55560f243ffd90209640a201c76b13094087e2464f`. Its CSVAE metadata is not yet supported by the retained RoboTwin training initializer; downloading it successfully does not imply that `train.sh --init` can load it. Evaluation uses the released posttraining weights and is independent of this limitation.

## Data Processing

The retained RoboTwin preparation entry uses the upstream LeRobot v2.1 export: 50 Hz, native 14D action/state and `cam_high`, `cam_left_wrist`, `cam_right_wrist`. The reader selects the first 50 episodes in each 550-episode task block. Preserve that prepared export's `meta/`, `data/` and `videos/` layout.

```bash
bash process_data.sh RoboTwin cotrain arx_x5 joint \
  --data /path/to/robotwin-v21 --text-cache /path/to/robotwin-text
```

Add `--build-text-cache --weights "$PWD/checkpoints/phoenix-robotwin-35k" --device cuda:0` to build an instruction cache in a new directory. The RoboDojo release is inference-only; its original training statistics and cached task text are bundled under `robodojo/phoenix_source/`.

## Training

RoboTwin's existing training entry is retained. Install training dependencies with `bash install.sh phoenix-mwa-train train`. Supply an initialization checkpoint compatible with that training loader (see the pretraining metadata limitation above).

```bash
bash download_checkpoint.sh checkpoints/phoenix-robotwin-35k --benchmark RoboTwin --training-backbones
bash train.sh RoboTwin cotrain arx_x5 joint 42 0,1,2,3,4,5,6,7 \
  --init /path/to/compatible-initialization.pt \
  --weights "$PWD/checkpoints/phoenix-robotwin-35k" \
  --data /path/to/robotwin-v21 --text-cache /path/to/robotwin-text \
  --nnodes 1 --nproc 8 --batch-size 8 --max-steps 35000
```

Use `--dry-run` to validate resources and configuration. `train.sh` and `process_data.sh` reject RoboDojo rather than starting RoboTwin training with real-robot data.

## Evaluation

The standard ten-argument XPolicyLab command is shared:

```bash
# RoboTwin: policy env phoenix-mwa; simulator env robotwin
bash eval.sh RoboTwin adjust_bottle phoenix-robotwin-35k arx_x5 joint 0 0 0 phoenix-mwa robotwin

# RoboDojo: replace robodojo-client with your configured benchmark client environment
bash eval.sh RoboDojo stack_bowls phoenix-robodojo-edge25-40k piper joint 0 0 0 phoenix-mwa robodojo-client
bash eval.sh RoboDojo cover_blocks phoenix-robodojo-edge25-40k arx_x5 joint 0 0 0 phoenix-mwa robodojo-client
bash eval.sh RoboDojo sweep_blocks phoenix-robodojo-edge25-40k piper_x joint 0 0 0 phoenix-mwa robodojo-client
```

`setup_eval_policy_server.sh` and `setup_eval_env_client.sh` select `configs/robotwin.yml` or `configs/robodojo.yml` automatically. RoboTwin uses single-environment evaluation; RoboDojo retains batch evaluation. Python callers must provide `bench_name`, `env_cfg_type` and `action_type: joint`; remaining runtime defaults come from the matching profile.

RoboDojo defaults to exact cached training instructions. Set `WAM_TEXT_MODE=online_t5` for arbitrary instructions; this loads the pinned T5 encoder. `WAM_CHECKPOINT_PATH` may override the RoboDojo checkpoint directory. Its checkpoint contract still validates robot family, geometry, statistics and step.

## Code and verification

```text
model.py                       shared XPolicyLab entry and benchmark dispatch
configs/                       benchmark-specific server/client profiles
robotwin.py, runtime/           original RoboTwin adapter and model implementation
training/                      RoboTwin data and training entry points
robodojo/                      original RoboDojo adapter, model source and manifests
download.py                    shared checkpoint download entry
tests/                         shared-interface and RoboTwin regression tests
```

The merge sources are recorded in `integration_sources.json`: RoboTwin PR #190 on official main and RoboDojo PR #186. Inference backends and frozen model source are retained; checkpoints are not combined into one model. See [validation](VALIDATION.md) for checks performed on this merged version. Historical result files under `runtime/` and `robodojo/` describe their original releases, not a new evaluation of the merged entry.
