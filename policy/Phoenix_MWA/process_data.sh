#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  RoboDojo|robodojo) echo "RoboDojo is evaluation-only; training/data conversion are not released." >&2; exit 2 ;;
  robotwin) shift; set -- RoboTwin "$@" ;;
  RoboTwin|--help|-h) ;;
  *) echo "First argument must be RoboTwin (RoboDojo is evaluation-only)." >&2; exit 2 ;;
esac
P="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$P/../../..:${PYTHONPATH:-}"
exec "${PYTHON:-python}" -m XPolicyLab.policy.Phoenix_MWA.training.data "$@"
