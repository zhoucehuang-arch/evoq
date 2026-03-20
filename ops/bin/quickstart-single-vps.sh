#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: quickstart-single-vps.sh [--target-user USER] [forwarded onboard-single-vps flags...]" >&2
}

TARGET_USER="${SUDO_USER:-${USER:-root}}"
FORWARD_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-user)
      if [[ $# -lt 2 ]]; then
        usage
        exit 1
      fi
      TARGET_USER="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      FORWARD_ARGS+=("$1")
      shift
      ;;
  esac
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
INSTALL_HOST_DEPS_SH="${ROOT_DIR}/ops/bin/install-host-deps.sh"
ONBOARD_SINGLE_VPS_SH="${ROOT_DIR}/ops/bin/onboard-single-vps.sh"

docker_ready() {
  command -v docker >/dev/null 2>&1 \
    && docker compose version >/dev/null 2>&1 \
    && docker info >/dev/null 2>&1
}

run_install_host_deps() {
  echo "Installing host dependencies for the single-VPS product path..."
  if [[ "${EUID}" -eq 0 ]]; then
    "${INSTALL_HOST_DEPS_SH}" "${TARGET_USER}"
    return
  fi
  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo is required to install host dependencies automatically." >&2
    echo "Run sudo ./ops/bin/install-host-deps.sh ${TARGET_USER} first, then rerun quickstart-single-vps.sh." >&2
    exit 1
  fi
  sudo "${INSTALL_HOST_DEPS_SH}" "${TARGET_USER}"
}

run_onboard_with_docker_group() {
  local onboard_command
  local root_dir_quoted
  printf -v onboard_command '%q ' "${ONBOARD_SINGLE_VPS_SH}" "${FORWARD_ARGS[@]}"
  printf -v root_dir_quoted '%q' "${ROOT_DIR}"
  if command -v sg >/dev/null 2>&1; then
    exec sg docker -c "cd ${root_dir_quoted} && ${onboard_command}"
  fi
  echo "Docker access is installed, but this shell has not picked up docker group membership yet." >&2
  echo "Log out and back in, then rerun ./ops/bin/onboard-single-vps.sh." >&2
  exit 1
}

if docker_ready; then
  exec "${ONBOARD_SINGLE_VPS_SH}" "${FORWARD_ARGS[@]}"
fi

run_install_host_deps

if docker_ready; then
  exec "${ONBOARD_SINGLE_VPS_SH}" "${FORWARD_ARGS[@]}"
fi

run_onboard_with_docker_group
