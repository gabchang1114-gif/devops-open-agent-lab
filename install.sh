#!/usr/bin/env bash
#
# DevOps Open Agent — installer for macOS and Linux
#
# Usage:
#   ./install.sh                 # interactive install with defaults
#   ./install.sh --admin-pass secret123
#   ./install.sh --skip-build    # only configure env, do not start containers
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
SKIP_BUILD=0
COMPOSE=""

log() {
  printf '[devops-agent] %s\n' "$*"
}

warn() {
  printf '[devops-agent] WARNING: %s\n' "$*" >&2
}

fail() {
  printf '[devops-agent] ERROR: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
DevOps Open Agent installer

Options:
  --admin-pass PASSWORD   Default admin password (default: admin123)
  --skip-build            Configure environment only; do not build/start Docker
  -h, --help              Show this help message

Environment variables:
  ADMIN_PASSWORD          Same as --admin-pass

Examples:
  ./install.sh
  ./install.sh --admin-pass 'MySecurePass123'
  ADMIN_PASSWORD='MySecurePass123' ./install.sh
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --admin-pass)
        [[ $# -ge 2 ]] || fail "--admin-pass requires a value"
        ADMIN_PASSWORD="$2"
        shift 2
        ;;
      --skip-build)
        SKIP_BUILD=1
        shift
        ;;
      -h | --help)
        usage
        exit 0
        ;;
      *)
        fail "Unknown option: $1"
        ;;
    esac
  done
}

detect_os() {
  case "$(uname -s)" in
    Darwin)
      OS="macos"
      ;;
    Linux)
      OS="linux"
      ;;
    *)
      fail "Unsupported operating system: $(uname -s). Use macOS or Linux."
      ;;
  esac
  log "Detected OS: $OS ($(uname -m))"
}

require_command() {
  local cmd="$1"
  local install_hint="$2"
  command -v "$cmd" >/dev/null 2>&1 || fail "$cmd is not installed. $install_hint"
}

check_prerequisites() {
  require_command "curl" "Install curl using your system package manager."
  require_command "python3" "Install Python 3.12+ using your system package manager."

  if ! command -v docker >/dev/null 2>&1; then
    fail "Docker is not installed. Install Docker Desktop (macOS) or Docker Engine (Linux)."
  fi

  if ! docker info >/dev/null 2>&1; then
    fail "Docker daemon is not running. Start Docker and run this script again."
  fi

  if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
  else
    fail "Docker Compose is not available. Install Docker Compose v2 or docker-compose."
  fi

  log "Docker and Compose are available."
}

generate_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
  fi
}

update_env_var() {
  local key="$1"
  local value="$2"
  local file="$3"

  python3 - "$key" "$value" "$file" <<'PY'
import pathlib
import re
import sys

key, value, file_path = sys.argv[1:4]
path = pathlib.Path(file_path)
lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
pattern = re.compile(rf"^{re.escape(key)}=")
updated = False
new_lines = []

for line in lines:
    if pattern.match(line):
        new_lines.append(f"{key}={value}")
        updated = True
    else:
        new_lines.append(line)

if not updated:
    if new_lines and new_lines[-1] != "":
        new_lines.append("")
    new_lines.append(f"{key}={value}")

path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
PY
}

configure_environment() {
  local env_file="$ROOT_DIR/backend/.env"
  local env_example="$ROOT_DIR/backend/.env.example"

  [[ -f "$env_example" ]] || fail "Missing backend/.env.example"

  if [[ ! -f "$env_file" ]]; then
    cp "$env_example" "$env_file"
    log "Created backend/.env from backend/.env.example"
  else
    log "Using existing backend/.env"
  fi

  local jwt_secret
  jwt_secret="$(generate_secret)"

  update_env_var "LLM_PROVIDER" "ollama" "$env_file"
  update_env_var "OLLAMA_BASE_URL" "http://host.docker.internal:11434" "$env_file"
  update_env_var "OLLAMA_MODEL" "gemma4:e4b" "$env_file"
  update_env_var "SEED_DEFAULT_ADMIN" "true" "$env_file"
  update_env_var "DEFAULT_ADMIN_EMAIL" "admin" "$env_file"
  update_env_var "DEFAULT_ADMIN_PASSWORD" "$ADMIN_PASSWORD" "$env_file"
  update_env_var "JWT_SECRET" "$jwt_secret" "$env_file"
  update_env_var "POSTGRES_URL" "postgresql+asyncpg://kda:kda@postgres:5432/kda" "$env_file"
  update_env_var "DATABASE_PATH" "data/investigations.db" "$env_file"
  update_env_var "KUBE_API_HOST_REWRITE" "host.docker.internal" "$env_file"

  log "Configured backend/.env"
  log "Default login username: admin"
  log "Default login password: $ADMIN_PASSWORD"
}

check_optional_tools() {
  if command -v ollama >/dev/null 2>&1; then
    log "Ollama detected on host."
    if curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
      log "Ollama API is reachable at http://127.0.0.1:11434"
    else
      warn "Ollama is installed but not responding on port 11434. Start Ollama for AI features."
    fi
  else
    warn "Ollama not found on host. Install Ollama for local AI, or set LLM_PROVIDER=openai in backend/.env."
  fi

  if [[ -d "$HOME/.kube" ]]; then
    log "Found ~/.kube for Kubernetes investigations."
  else
    warn "~/.kube not found. Kubernetes investigations will need kubeconfig access."
  fi

  if [[ -d "$HOME/.aws" ]]; then
    log "Found ~/.aws for AWS and Cloud Cost modules."
  else
    warn "~/.aws not found. AWS modules will need credentials configured later."
  fi
}

wait_for_service() {
  local url="$1"
  local label="$2"
  local attempts="${3:-60}"
  local delay="${4:-5}"

  log "Waiting for $label..."
  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      log "$label is ready."
      return 0
    fi
    sleep "$delay"
  done

  fail "$label did not become ready in time. Check logs with: $COMPOSE logs"
}

start_stack() {
  log "Building and starting Docker services (first run may take several minutes)..."
  $COMPOSE up -d --build

  wait_for_service "http://127.0.0.1:8000/health" "Backend API"
  wait_for_service "http://127.0.0.1:3000" "Frontend UI"
}

print_summary() {
  cat <<EOF

DevOps Open Agent is installed.

URLs
  Frontend:  http://localhost:3000
  Backend:   http://localhost:8000
  API docs:  http://localhost:8000/docs

Default login
  Username: admin
  Password: $ADMIN_PASSWORD

Useful commands
  View logs:     $COMPOSE logs -f
  Stop stack:    $COMPOSE down
  Restart stack: $COMPOSE up -d
  Rebuild:       $COMPOSE up -d --build

Optional configuration (edit backend/.env)
  OPENAI_API_KEY / ANTHROPIC_API_KEY / OPENROUTER_API_KEY
  GITHUB_TOKEN / GITHUB_WEBHOOK_SECRET for PR Reviewer
  AWS credentials in ~/.aws for AWS and Cloud Cost modules

Security note
  Change DEFAULT_ADMIN_PASSWORD and JWT_SECRET before production use.

EOF
}

main() {
  parse_args "$@"
  detect_os
  check_prerequisites
  configure_environment
  check_optional_tools

  if [[ "$SKIP_BUILD" -eq 1 ]]; then
    log "Skipping Docker build/start (--skip-build)."
  else
    start_stack
  fi

  print_summary
}

main "$@"
