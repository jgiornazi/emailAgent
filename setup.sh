#!/usr/bin/env bash
# ============================================================================
# EmailAgent Setup Script
# Automates: venv creation, dependency install, config directory, and config file
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

EMAILAGENT_DIR="$HOME/.emailagent"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERR]${NC}  $1"; exit 1; }

echo ""
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}  EmailAgent Setup${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""

# ------------------------------------------------------------------
# 1. Check Python version
# ------------------------------------------------------------------
info "Checking Python version..."

if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    error "Python not found. Please install Python 3.11 or later."
fi

PY_VERSION=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$($PYTHON -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$($PYTHON -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    error "Python 3.11+ required (found $PY_VERSION)."
fi

success "Python $PY_VERSION"

# ------------------------------------------------------------------
# 2. Create virtual environment
# ------------------------------------------------------------------
VENV_DIR="$PROJECT_DIR/.venv"

if [ -d "$VENV_DIR" ]; then
    info "Virtual environment already exists at .venv"
else
    info "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
    success "Virtual environment created at .venv"
fi

# Activate venv
source "$VENV_DIR/bin/activate"
success "Virtual environment activated"

# ------------------------------------------------------------------
# 3. Upgrade pip and install dependencies
# ------------------------------------------------------------------
info "Upgrading pip..."
pip install --upgrade pip --quiet

info "Installing project dependencies..."
pip install -r "$PROJECT_DIR/requirements.txt" --quiet
success "Dependencies installed"

# ------------------------------------------------------------------
# 4. Install project in editable mode
# ------------------------------------------------------------------
info "Installing emailagent in editable mode..."
pip install -e "$PROJECT_DIR" --quiet
success "emailagent CLI installed (editable mode)"

# ------------------------------------------------------------------
# 5. Create config directory and subdirectories
# ------------------------------------------------------------------
info "Setting up config directory at $EMAILAGENT_DIR..."

mkdir -p "$EMAILAGENT_DIR"
mkdir -p "$EMAILAGENT_DIR/backups"
mkdir -p "$EMAILAGENT_DIR/logs"
mkdir -p "$EMAILAGENT_DIR/cache"

success "Config directories created"

# ------------------------------------------------------------------
# 6. Copy default config if not present
# ------------------------------------------------------------------
CONFIG_FILE="$EMAILAGENT_DIR/config.yaml"

if [ -f "$CONFIG_FILE" ]; then
    info "Config file already exists, skipping"
else
    cp "$PROJECT_DIR/config.yaml.example" "$CONFIG_FILE"
    success "Default config copied to $CONFIG_FILE"
fi

# ------------------------------------------------------------------
# 7. Set secure permissions on config directory
# ------------------------------------------------------------------
chmod 700 "$EMAILAGENT_DIR"

if [ -f "$EMAILAGENT_DIR/credentials.json" ]; then
    chmod 600 "$EMAILAGENT_DIR/credentials.json"
    success "Secured credentials.json permissions"
fi

if [ -f "$EMAILAGENT_DIR/token.json" ]; then
    chmod 600 "$EMAILAGENT_DIR/token.json"
    success "Secured token.json permissions"
fi

# ------------------------------------------------------------------
# 8. Check for Gmail credentials
# ------------------------------------------------------------------
echo ""
if [ -f "$EMAILAGENT_DIR/credentials.json" ]; then
    success "Gmail credentials found"
else
    warn "Gmail credentials not found at $EMAILAGENT_DIR/credentials.json"
    echo ""
    echo -e "  To complete setup, you need to:"
    echo -e "  1. Create a Google Cloud project and enable the Gmail API"
    echo -e "  2. Create OAuth credentials (Desktop app)"
    echo -e "  3. Download the credentials JSON file"
    echo -e "  4. Move it to: ${BOLD}$EMAILAGENT_DIR/credentials.json${NC}"
    echo ""
    echo -e "  See ${BOLD}SETUP.md${NC} for detailed instructions."
fi

# ------------------------------------------------------------------
# 9. Check for Ollama (optional)
# ------------------------------------------------------------------
if command -v ollama &>/dev/null; then
    success "Ollama found (AI extraction available with --use-ai)"
else
    info "Ollama not installed (optional - for AI-powered extraction)"
fi

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
echo ""
echo -e "${BOLD}========================================${NC}"
echo -e "${GREEN}${BOLD}  Setup complete!${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""
echo -e "  To activate the virtual environment:"
echo -e "    ${BOLD}source .venv/bin/activate${NC}"
echo ""
echo -e "  Quick start:"
echo -e "    ${BOLD}emailagent auth login${NC}        # Authenticate with Gmail"
echo -e "    ${BOLD}emailagent job scan --preview${NC} # Preview job emails"
echo -e "    ${BOLD}emailagent job scan${NC}           # Scan and track applications"
echo ""
