#!/bin/bash
set -euo pipefail

bench_name=${1}
task_name=${2}
ckpt_name=${3}
env_cfg_type=${4}
action_type=${5}
seed=${6}
policy_gpu_id=${7}
policy_conda_env=${8}
policy_server_port=${9}
policy_server_host=${10:-"localhost"}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
XPL_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
UTILS_DIR="${XPL_ROOT}/utils"

policy_name="$(basename "${SCRIPT_DIR}")"
case "${bench_name}" in
    RoboTwin|robotwin) bench_name=RoboTwin; profile=robotwin ;;
    RoboDojo|robodojo) bench_name=RoboDojo; profile=robodojo ;;
    *) echo "Phoenix-MWA supports RoboTwin or RoboDojo" >&2; exit 2 ;;
esac
yaml_file="${SCRIPT_DIR}/configs/${profile}.yml"

echo "[SERVER] policy=${policy_name}, task=${task_name}, policy_server_port=${policy_server_port}"

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${policy_conda_env}"

extra_overrides=()
[[ -z "${WAM_TEXT_MODE:-}" ]] || extra_overrides+=("text_mode=${WAM_TEXT_MODE}")
[[ -z "${WAM_CHECKPOINT_PATH:-}" ]] || extra_overrides+=("checkpoint_path=${WAM_CHECKPOINT_PATH}")
[[ -z "${WAM_AUDIT_DIR:-}" ]] || extra_overrides+=("audit_dir=${WAM_AUDIT_DIR}")
[[ -z "${WAM_EXPECTED_STEP:-}" ]] || extra_overrides+=("expected_step=${WAM_EXPECTED_STEP}")

exec env \
    PYTHONPATH="${XPL_ROOT}/..:${PYTHONPATH:-}" \
    PYTHONUNBUFFERED=1 \
    PYTHONWARNINGS=ignore::UserWarning \
    CUDA_VISIBLE_DEVICES="${policy_gpu_id}" \
    python "${XPL_ROOT}/setup_policy_server.py" \
        --config_path "${yaml_file}" \
        --overrides \
            port="${policy_server_port}" \
            host="${policy_server_host}" \
            bench_name="${bench_name}" \
            task_name="${task_name}" \
            ckpt_name="${ckpt_name}" \
            env_cfg_type="${env_cfg_type}" \
            seed="${seed}" \
            policy_name="${policy_name}" \
            action_type="${action_type}" \
            "${extra_overrides[@]}"
