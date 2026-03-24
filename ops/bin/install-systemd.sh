#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: install-systemd.sh core|worker /opt/evoq" >&2
  exit 1
fi

ROLE="$1"
ROOT_DIR="$(cd -- "$2" && pwd)"
SYSTEMD_DIR="/etc/systemd/system"

if [[ ! -d "${ROOT_DIR}" ]]; then
  echo "Missing repo root: ${ROOT_DIR}" >&2
  exit 1
fi

if [[ "${ROLE}" != "core" && "${ROLE}" != "worker" ]]; then
  echo "Role must be core or worker." >&2
  exit 1
fi

chmod +x "${ROOT_DIR}/ops/bin/"*.sh

UNIT_NAME="quant-evo-${ROLE}.service"
TEMPLATE_PATH="${ROOT_DIR}/ops/systemd/${UNIT_NAME}"
RENDERED_UNIT="$(mktemp)"
trap 'rm -f "${RENDERED_UNIT}"' EXIT
sed "s|/opt/evoq|${ROOT_DIR}|g" "${TEMPLATE_PATH}" > "${RENDERED_UNIT}"
install -m 0644 "${RENDERED_UNIT}" "${SYSTEMD_DIR}/${UNIT_NAME}"
systemctl daemon-reload
systemctl enable --now "${UNIT_NAME}"

echo "Installed ${ROLE} systemd unit."
