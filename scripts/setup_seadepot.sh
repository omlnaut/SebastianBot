#!/usr/bin/env bash
#
# Provision the host-level `seadepot` command.
#
# Installs the uv bootstrapper if missing, creates/refreshes one dedicated
# virtualenv from cli-requirements.txt, and writes a PATH shim that runs that
# environment's interpreter against this repo. Idempotent: re-run it after a
# code or dependency change. No container, no Azure login, no Key Vault.
#
# The credentials themselves are not handled here: export
# SEAMIETPLAN_CREDENTIALS with the credentials JSON content in the shell that
# calls `seadepot`.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${SEADEPOT_VENV_DIR:-$HOME/.local/share/seadepot/venv}"
BIN_DIR="${SEADEPOT_BIN_DIR:-$HOME/.local/bin}"
SHIM="$BIN_DIR/seadepot"
REQUIREMENTS="$REPO_ROOT/cli-requirements.txt"

if ! command -v uv >/dev/null 2>&1; then
  if [ -x "$HOME/.local/bin/uv" ]; then
    export PATH="$HOME/.local/bin:$PATH"
  else
    echo "==> Installing uv"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi

echo "==> Creating/refreshing the seadepot environment at $VENV_DIR"
uv venv --clear --python 3.12 "$VENV_DIR"
uv pip install --python "$VENV_DIR/bin/python" -r "$REQUIREMENTS"

echo "==> Writing the seadepot shim at $SHIM"
mkdir -p "$BIN_DIR"
cat >"$SHIM" <<SHIM_EOF
#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$REPO_ROOT\${PYTHONPATH:+:\$PYTHONPATH}"
exec "$VENV_DIR/bin/python" -m cli.mietplan "\$@"
SHIM_EOF
chmod +x "$SHIM"

echo "==> Done"
if ! printf '%s' ":$PATH:" | grep -q ":$BIN_DIR:"; then
  echo "Add $BIN_DIR to PATH to call \`seadepot\` from any shell."
fi
echo "Export SEAMIETPLAN_CREDENTIALS (credentials JSON content) before use."
