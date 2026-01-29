#!/usr/bin/env bash
# ============================================================================
# EmailAgent Exit Script
# Deactivates venv and cleans up temp/cache files
# ============================================================================

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}  EmailAgent Cleanup${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""

# ------------------------------------------------------------------
# 1. Deactivate virtual environment
# ------------------------------------------------------------------
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate 2>/dev/null
    success "Virtual environment deactivated"
else
    info "No virtual environment active"
fi

# ------------------------------------------------------------------
# 2. Clean up Python cache files
# ------------------------------------------------------------------
info "Cleaning Python cache files..."
find "$PROJECT_DIR" -type d -name "__pycache__" -not -path "*/.venv/*" -exec rm -rf {} + 2>/dev/null
find "$PROJECT_DIR" -type f -name "*.pyc" -not -path "*/.venv/*" -delete 2>/dev/null
success "Python cache files removed"

# ------------------------------------------------------------------
# 3. Clean up pytest cache
# ------------------------------------------------------------------
if [ -d "$PROJECT_DIR/.pytest_cache" ]; then
    rm -rf "$PROJECT_DIR/.pytest_cache"
    success "Pytest cache removed"
fi

# ------------------------------------------------------------------
# 4. Clean up coverage artifacts
# ------------------------------------------------------------------
if [ -d "$PROJECT_DIR/htmlcov" ]; then
    rm -rf "$PROJECT_DIR/htmlcov"
    success "Coverage HTML report removed"
fi

if [ -f "$PROJECT_DIR/.coverage" ]; then
    rm -f "$PROJECT_DIR/.coverage"
    success "Coverage data file removed"
fi

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
echo ""
echo -e "${BOLD}========================================${NC}"
echo -e "${GREEN}${BOLD}  Cleanup complete!${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""
