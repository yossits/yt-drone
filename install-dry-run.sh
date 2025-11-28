#!/bin/bash
# Dry-run script for install.sh - Shows what would be done without actually doing it
# This script does NOT make any changes to the system - it only simulates and displays

# ===== BASIC SETTINGS =====
APP_USER="pi"
APP_DIR="/home/pi/yt-drone"
REPO_URL="https://github.com/yossits/yt-drone.git"
SERVICE_NAME="drone-hub.service"
PYTHON="/usr/bin/python3"
APP_PORT=8001

# ===== COLORS =====
RESET="\033[0m"
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
MAGENTA="\033[35m"
BLUE="\033[34m"

c() {
  echo -e "${2}${1}${RESET}"
}

step() {
  c "\n[STEP] $1" "$MAGENTA"
}

info() {
  c "[INFO] $1" "$CYAN"
}

ok() {
  c "[OK ] $1" "$GREEN"
}

warn() {
  c "[WARN] $1" "$YELLOW"
}

err() {
  c "[ERROR] $1" "$RED"
}

dry_run() {
  c "[DRY-RUN] $1" "${BOLD}${BLUE}"
}

# ===== HEADER =====
c "\n" ""
c "═══════════════════════════════════════════════════════════" "${BOLD}${BLUE}"
c "        DRY-RUN MODE - NO CHANGES WILL BE MADE" "${BOLD}${BLUE}"
c "═══════════════════════════════════════════════════════════" "${BOLD}${BLUE}"
c "\n" ""
c "=== Drone App Installation Wizard (DRY-RUN) ===" "$BOLD"
info "This simulation shows what install.sh would do without making any changes."

# ===== 1. CHECK SYSTEM PACKAGES =====
step "Checking system packages..."

PACKAGES_TO_INSTALL=()
PACKAGES_INSTALLED=()

check_package() {
  local pkg=$1
  if command -v "$pkg" >/dev/null 2>&1; then
    PACKAGES_INSTALLED+=("$pkg")
    return 0
  else
    PACKAGES_TO_INSTALL+=("$pkg")
    return 1
  fi
}

check_package "python3"
check_package "git"
check_package "pip3" || check_package "pip"
if ! python3 -c "import venv" 2>/dev/null; then
  PACKAGES_TO_INSTALL+=("python3-venv")
else
  PACKAGES_INSTALLED+=("python3-venv")
fi
if ! command -v netstat >/dev/null 2>&1 && ! command -v ss >/dev/null 2>&1; then
  PACKAGES_TO_INSTALL+=("net-tools")
else
  PACKAGES_INSTALLED+=("net-tools")
fi

if [ ${#PACKAGES_INSTALLED[@]} -gt 0 ]; then
  info "Already installed packages:"
  for pkg in "${PACKAGES_INSTALLED[@]}"; do
    c "  ✓ $pkg" "$GREEN"
  done
fi

if [ ${#PACKAGES_TO_INSTALL[@]} -gt 0 ]; then
  dry_run "Would install: ${PACKAGES_TO_INSTALL[*]}"
  c "  Command: apt-get install -y ${PACKAGES_TO_INSTALL[*]}" "$CYAN"
else
  ok "All required packages are already installed."
fi

# ===== 2. CHECK REPOSITORY =====
step "Checking repository status..."

if [ ! -d "$APP_DIR" ]; then
  dry_run "Would create directory: $APP_DIR"
  dry_run "Would clone repository: $REPO_URL"
  c "  Command: git clone $REPO_URL $APP_DIR" "$CYAN"
else
  ok "Directory exists: $APP_DIR"
  if [ ! -d "$APP_DIR/.git" ]; then
    warn "Directory exists but is not a git repository."
    dry_run "Would clone repository into existing directory"
  else
    ok "Git repository found."
    dry_run "Would run: git fetch origin"
    dry_run "Would run: git pull origin main (or master)"
    c "  Note: May reset to origin if local changes exist" "$YELLOW"
  fi
fi

# ===== 3. CHECK PYTHON VENV =====
step "Checking Python virtualenv..."

if [ ! -d "$APP_DIR/venv" ]; then
  dry_run "Would create virtualenv: $APP_DIR/venv"
  c "  Command: $PYTHON -m venv $APP_DIR/venv" "$CYAN"
else
  ok "Virtualenv already exists: $APP_DIR/venv"
fi

if [ ! -f "$APP_DIR/requirements.txt" ]; then
  warn "requirements.txt not found in $APP_DIR"
  dry_run "Would skip Python dependencies installation"
else
  ok "requirements.txt found"
  dry_run "Would activate venv and run: pip install -r requirements.txt"
  c "  Command: source venv/bin/activate && pip install -r requirements.txt" "$CYAN"
fi

# ===== 4. SIMULATE UART CONFIGURATION =====
step "Simulating UART configuration..."

UART_CONFIG_CHANGES=false

# Find config.txt
CONFIG_PATH=""
if [ -f "/boot/firmware/config.txt" ]; then
  CONFIG_PATH="/boot/firmware/config.txt"
elif [ -f "/boot/config.txt" ]; then
  CONFIG_PATH="/boot/config.txt"
fi

if [ -n "$CONFIG_PATH" ]; then
  info "Found config file: $CONFIG_PATH"
  
  # Check current UART settings
  if grep -q "^enable_uart" "$CONFIG_PATH" 2>/dev/null; then
    UART_VALUE=$(grep "^enable_uart" "$CONFIG_PATH" | head -1 | cut -d'=' -f2 | tr -d ' ')
    if [ "$UART_VALUE" = "1" ]; then
      ok "enable_uart is already set to 1"
    else
      dry_run "Would change enable_uart from $UART_VALUE to 1"
      UART_CONFIG_CHANGES=true
    fi
  else
    dry_run "Would add: enable_uart=1"
    UART_CONFIG_CHANGES=true
  fi
  
  if grep -q "^dtoverlay=disable-bt" "$CONFIG_PATH" 2>/dev/null; then
    ok "dtoverlay=disable-bt is already present"
  else
    dry_run "Would add: dtoverlay=disable-bt"
    UART_CONFIG_CHANGES=true
  fi
  
  if [ "$UART_CONFIG_CHANGES" = true ]; then
    c "  Would create backup: ${CONFIG_PATH}.bak" "$CYAN"
  fi
else
  warn "Could not find config.txt (this is normal if not running on Raspberry Pi)"
  dry_run "Would search for /boot/firmware/config.txt or /boot/config.txt"
fi

# Check cmdline.txt
CMDLINE_PATH=""
if [ -f "/boot/firmware/cmdline.txt" ]; then
  CMDLINE_PATH="/boot/firmware/cmdline.txt"
elif [ -f "/boot/cmdline.txt" ]; then
  CMDLINE_PATH="/boot/cmdline.txt"
fi

if [ -n "$CMDLINE_PATH" ]; then
  info "Found cmdline file: $CMDLINE_PATH"
  if grep -q "console=serial0\|console=ttyAMA0" "$CMDLINE_PATH" 2>/dev/null; then
    dry_run "Would remove UART console entries from cmdline.txt"
    c "  Would create backup: ${CMDLINE_PATH}.bak" "$CYAN"
    UART_CONFIG_CHANGES=true
  else
    ok "No UART console entries found in cmdline.txt"
  fi
else
  warn "Could not find cmdline.txt"
fi

if [ "$UART_CONFIG_CHANGES" = true ]; then
  warn "UART configuration changes detected - reboot would be required"
fi

# ===== 5. CHECK PORT AVAILABILITY =====
step "Checking port availability..."

check_port() {
  local port=$1
  if command -v netstat >/dev/null 2>&1; then
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
      return 1
    fi
  elif command -v ss >/dev/null 2>&1; then
    if ss -tuln 2>/dev/null | grep -q ":$port "; then
      return 1
    fi
  fi
  return 0
}

if check_port "$APP_PORT"; then
  ok "Port $APP_PORT is available"
else
  warn "Port $APP_PORT is already in use!"
  c "  Check with: sudo netstat -tulpn | grep :$APP_PORT" "$CYAN"
fi

# ===== 6. CHECK run_app.sh =====
step "Checking run_app.sh launcher..."

RUN_SCRIPT="$APP_DIR/run_app.sh"

if [ -f "$RUN_SCRIPT" ]; then
  ok "run_app.sh exists: $RUN_SCRIPT"
  if grep -q "uvicorn.*app.main:app" "$RUN_SCRIPT" 2>/dev/null; then
    ok "run_app.sh already uses uvicorn"
  else
    dry_run "Would update run_app.sh to use uvicorn"
    c "  Current content would be replaced" "$YELLOW"
  fi
else
  dry_run "Would create run_app.sh"
fi

dry_run "Content of run_app.sh would be:"
cat << EOS | sed 's/^/  /'
#!/bin/bash
set -e
cd "$APP_DIR"
source venv/bin/activate

# Run FastAPI application with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port $APP_PORT
EOS

# ===== 7. CHECK SYSTEMD SERVICE =====
step "Checking systemd service..."

SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

if [ -f "$SERVICE_PATH" ]; then
  ok "Service file exists: $SERVICE_PATH"
  if systemctl is-enabled "$SERVICE_NAME" >/dev/null 2>&1; then
    c "  Service is enabled" "$GREEN"
  else
    dry_run "Would enable service"
  fi
  if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    c "  Service is currently running" "$GREEN"
    dry_run "Would restart service"
  else
    dry_run "Would start service"
  fi
else
  dry_run "Would create systemd service file: $SERVICE_PATH"
fi

dry_run "Service file content would be:"
cat << EOF | sed 's/^/  /'
[Unit]
Description=Drone Hub Application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$RUN_SCRIPT
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# ===== 8. SUMMARY =====
step "Dry-Run Summary"

c "\n" ""
c "═══════════════════════════════════════════════════════════" "$BOLD"
c "           DRY-RUN SUMMARY" "$BOLD"
c "═══════════════════════════════════════════════════════════" "$BOLD"
c "" ""

info "What would be installed/configured:"

# Packages
if [ ${#PACKAGES_TO_INSTALL[@]} -gt 0 ]; then
  c "  📦 Packages to install: ${PACKAGES_TO_INSTALL[*]}" "$YELLOW"
fi

# Repository
if [ ! -d "$APP_DIR" ] || [ ! -d "$APP_DIR/.git" ]; then
  c "  📥 Repository: Would clone/update from $REPO_URL" "$YELLOW"
else
  c "  📥 Repository: Would update existing repository" "$CYAN"
fi

# Virtualenv
if [ ! -d "$APP_DIR/venv" ]; then
  c "  🐍 Python venv: Would create $APP_DIR/venv" "$YELLOW"
fi
if [ -f "$APP_DIR/requirements.txt" ]; then
  c "  📚 Dependencies: Would install from requirements.txt" "$YELLOW"
fi

# UART
if [ "$UART_CONFIG_CHANGES" = true ]; then
  c "  ⚙️  UART: Would modify /boot/config.txt (REBOOT REQUIRED)" "${BOLD}${RED}"
else
  c "  ⚙️  UART: No changes needed" "$GREEN"
fi

# Files
if [ ! -f "$RUN_SCRIPT" ] || ! grep -q "uvicorn" "$RUN_SCRIPT" 2>/dev/null; then
  c "  📝 run_app.sh: Would create/update" "$YELLOW"
fi

if [ ! -f "$SERVICE_PATH" ]; then
  c "  🔧 Systemd service: Would create $SERVICE_PATH" "$YELLOW"
fi

# Service status
if [ -f "$SERVICE_PATH" ]; then
  if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    c "  ▶️  Service: Would restart" "$YELLOW"
  else
    c "  ▶️  Service: Would start and enable" "$YELLOW"
  fi
else
  c "  ▶️  Service: Would create, enable and start" "$YELLOW"
fi

c "" ""
c "═══════════════════════════════════════════════════════════" "$BOLD"
c "Current System State:" "$BOLD"
c "═══════════════════════════════════════════════════════════" "$BOLD"
c "" ""

# Current IP
IP=$(hostname -I | awk '{print $1}' | head -1)
if [ -n "$IP" ] && [[ $IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  info "Application would be accessible at:"
  c "  • Network: http://$IP:$APP_PORT" "${BOLD}${CYAN}"
  c "  • Local:   http://localhost:$APP_PORT" "$CYAN"
fi

# Current service status
if [ -f "$SERVICE_PATH" ]; then
  if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    c "  ✓ Service is currently running" "$GREEN"
  else
    c "  ✗ Service is not running" "$RED"
  fi
  if systemctl is-enabled "$SERVICE_NAME" >/dev/null 2>&1; then
    c "  ✓ Service is enabled" "$GREEN"
  else
    c "  ✗ Service is not enabled" "$YELLOW"
  fi
fi

c "" ""
c "═══════════════════════════════════════════════════════════" "${BOLD}${BLUE}"
c "  This was a DRY-RUN - No changes were made to the system" "${BOLD}${BLUE}"
c "═══════════════════════════════════════════════════════════" "${BOLD}${BLUE}"
c "" ""
c "To actually install, run: sudo bash install.sh" "$CYAN"
c "" ""

