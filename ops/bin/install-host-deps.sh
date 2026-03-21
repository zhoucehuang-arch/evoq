#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run install-host-deps.sh with sudo or as root." >&2
  exit 1
fi

TARGET_USER="${1:-${SUDO_USER:-root}}"

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer currently supports Debian or Ubuntu hosts with apt-get only." >&2
  exit 1
fi

if [[ ! -f /etc/os-release ]]; then
  echo "Could not detect the host OS because /etc/os-release is missing." >&2
  exit 1
fi

# shellcheck disable=SC1091
. /etc/os-release

if [[ "${ID:-}" != "ubuntu" && "${ID:-}" != "debian" ]]; then
  echo "Unsupported host OS id: ${ID:-unknown}. Expected ubuntu or debian." >&2
  exit 1
fi

if [[ -z "${VERSION_CODENAME:-}" ]]; then
  echo "Could not detect VERSION_CODENAME from /etc/os-release." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl gnupg bash sed tar coreutils git python3 python3-venv python3-pip

install -m 0755 -d /etc/apt/keyrings
DOCKER_KEYRING="/etc/apt/keyrings/docker.gpg"
TMP_DOCKER_KEYRING="$(mktemp)"
trap 'rm -f "${TMP_DOCKER_KEYRING}"' EXIT
curl -fsSL "https://download.docker.com/linux/${ID}/gpg" | gpg --dearmor > "${TMP_DOCKER_KEYRING}"
install -m 0644 "${TMP_DOCKER_KEYRING}" "${DOCKER_KEYRING}"
chmod a+r "${DOCKER_KEYRING}"

ARCH="$(dpkg --print-architecture)"
cat > /etc/apt/sources.list.d/docker.list <<EOF
deb [arch=${ARCH} signed-by=${DOCKER_KEYRING}] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable
EOF

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

if id -u "${TARGET_USER}" >/dev/null 2>&1; then
  usermod -aG docker "${TARGET_USER}"
  echo "Added ${TARGET_USER} to the docker group."
else
  echo "Warning: user ${TARGET_USER} was not found, so no docker group membership was changed." >&2
fi

echo "Host dependencies installed."
echo "If docker group membership changed, log out and back in before running deploy scripts without sudo."
