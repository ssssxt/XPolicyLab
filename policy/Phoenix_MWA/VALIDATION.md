# Unified policy validation — 2026-10-26

Sources: official XPolicyLab main `c43a74653bec480ebe82c84770664e8035bc56c9` (merged RoboTwin PR #190), and RoboDojo PR #186 head `b36cc3abefa1d66ee6ab730af1fbc7766c5c26a4`.

## Completed checks

- 14 unified-entry/RoboTwin tests passed, including the actual released 35K checkpoint contract and normalization check.
- 43 RoboDojo tests passed, including the actual ARX X5, Piper and Piper X edge25 40K checkpoint metadata; download verification/corruption handling; no-crop pixels/view order; normalization/inverse; repeat-nine encoding; batch/session handling; and instruction caching.
- 15 historical z-score tests remain explicitly skipped by the original release. They do not apply to the current H5 q01/q99 policy.
- The RoboTwin adapter is byte-identical to its original implementation after moving to `robotwin.py`. All 131 files under the RoboDojo frozen `joint96_source/` and `phoenix_source/` match PR #186 byte-for-byte.
- Shell syntax, Python compilation, download CLI help/routing, and Git whitespace checks passed.

CPU tests ran in separate Python 3.10 processes in the existing fastwam-pretrain environment on the server. Logs are in `validation/robotwin-tests.log` and `validation/robodojo-tests.log`. Tests use real checkpoint metadata and small synthetic tensors; they do not constitute a new GPU inference or simulator-success measurement.

## Reproduce

Run from the parent of the XPolicyLab checkout with its dependencies installed:

```bash
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PHOENIX_ROBOTWIN_TEST_WEIGHT=/path/to/phoenix-robotwin-35k/policy.pt
python -m unittest -v XPolicyLab.policy.Phoenix_MWA.tests.test_unified XPolicyLab.policy.Phoenix_MWA.tests.test_policy

# Run in a separate process so each release activates its own wam runtime.
export PHOENIX_H5_TEST_WEIGHTS=/path/to/phoenix-robodojo-edge25-40k
python -m unittest -v \
  XPolicyLab.policy.Phoenix_MWA.robodojo.test_phoenix \
  XPolicyLab.policy.Phoenix_MWA.robodojo.test_resize_concat \
  XPolicyLab.policy.Phoenix_MWA.robodojo.test_joint96 \
  XPolicyLab.policy.Phoenix_MWA.robodojo.test_h5 \
  XPolicyLab.policy.Phoenix_MWA.robodojo.test_joint96_weights
```

## Not run for this merge

- Fresh Conda installation from scratch.
- Full-weight GPU inference, plain/encoded XPolicyLab debug episodes, real-robot or simulator evaluation. Historical release results are retained as historical evidence only.
- Retraining. The replacement 256013-step pretraining download is correctly pinned, but its CSVAE metadata requires a separate migration of the older RoboTwin training initializer. The published evaluation checkpoints do not use that initializer.
