#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  RoboDojo|robodojo) echo "RoboDojo is evaluation-only; training/data conversion are not released." >&2; exit 2 ;;
  robotwin) shift; set -- RoboTwin "$@" ;;
  RoboTwin|--help|-h) ;;
  *) echo "First argument must be RoboTwin (RoboDojo is evaluation-only)." >&2; exit 2 ;;
esac
P="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if (( $# >= 6 )); then
  ACTION_DIM=$(bash "$P/../../utils/get_action_dim.sh" "$(cd "$P/../../.." && pwd)" "$3")
  if [[ "$ACTION_DIM" != 14 ]]; then
    echo "Phoenix-MWA RoboTwin training requires the registered 14D joint action profile" >&2
    exit 1
  fi
fi
export PYTHONPATH="$P/../../..:${PYTHONPATH:-}"
exec "${PYTHON:-python}" -m XPolicyLab.policy.Phoenix_MWA.training.train "$@"
