#!/bin/bash
set -e

# ===== BASIC SETTINGS =====
APP_USER="pi"
APP_DIR="/home/pi/yt-drone"       # Change this if you want a different directory
REPO_URL="https://github.com/yossits/yt-drone.git"  # <- Update if needed!
SERVICE_NAME="drone-hub.service"
PYTHON="/usr/bin/python3"
APP_PORT=8001                      # HTTP port for your application

# ===== COLORS =====
RESET="\033[0m"
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
MAGENTA="\033[35m"

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

# ===== ENSURE ROOT =====
if [ "$(id -u)" -ne 0 ]; then
  err "This installer must be run as root. Use: sudo bash install.sh"
  exit 1
fi

c "=== Drone App Installation Wizard ===" "$BOLD"
info "This will configure UART, install dependencies, clone the app, and create a systemd service."

# ===== 1. APT PACKAGES =====
step "Installing system packages (Python, Git, etc)..."
apt-get update -y
apt-get install -y git python3 python3-venv python3-pip net-tools

ok "System packages installed."

# ===== 2. CLONE / UPDATE REPO =====
step "Preparing application directory..."

if [ ! -d "$APP_DIR" ]; then
  sudo -u "$APP_USER" mkdir -p "$APP_DIR"
  ok "Created directory: $APP_DIR"
fi

if [ ! -d "$APP_DIR/.git" ]; then
  step "Cloning repository..."
  if ! sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"; then
    err "Failed to clone repository. Please check the REPO_URL and network connection."
    exit 1
  fi
  ok "Repository cloned into $APP_DIR"
else
  step "Repository already exists, pulling latest changes..."
  if ! sudo -u "$APP_USER" bash -c "cd '$APP_DIR' && git fetch origin"; then
    warn "Failed to fetch from repository. Continuing with existing code..."
  else
    # Try to pull, if it fails due to local changes, reset to origin
    if ! sudo -u "$APP_USER" bash -c "cd '$APP_DIR' && git pull origin main 2>/dev/null || git pull origin master 2>/dev/null"; then
      warn "Git pull failed (possibly due to local changes). Attempting to reset to origin..."
      BRANCH=$(sudo -u "$APP_USER" bash -c "cd '$APP_DIR' && git branch --show-current 2>/dev/null || echo 'main'")
      if sudo -u "$APP_USER" bash -c "cd '$APP_DIR' && git reset --hard origin/$BRANCH 2>/dev/null || git reset --hard origin/main 2>/dev/null || git reset --hard origin/master 2>/dev/null"; then
        ok "Repository reset to match remote."
      else
        warn "Could not reset repository. Using existing code. Check manually: cd $APP_DIR && git status"
      fi
    else
      ok "Repository updated."
    fi
  fi
fi

# ===== 3. PYTHON VENV + REQUIREMENTS =====
step "Creating Python virtualenv and installing requirements..."

if [ ! -f "$APP_DIR/requirements.txt" ]; then
  warn "requirements.txt not found. Skipping Python dependencies installation."
else
  sudo -u "$APP_USER" bash -c "
    cd '$APP_DIR'
    if [ ! -d 'venv' ]; then
      $PYTHON -m venv venv
      if [ ! -d 'venv' ]; then
        echo 'ERROR: Failed to create virtualenv'
        exit 1
      fi
    fi
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
  "
  
  if [ $? -eq 0 ]; then
    ok "Virtualenv and Python dependencies ready."
  else
    err "Failed to install Python dependencies. Check the error messages above."
    exit 1
  fi
fi

# ===== 4. CONFIGURE UART (EMBED PYTHON) =====
step "Configuring UART for hardware serial (serial0 -> ttyAMA0)..."

$PYTHON << 'EOF'
from pathlib import Path
import sys

RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
RED = "\033[31m"

def c(text, color):
    print(f"{color}{text}{RESET}")

def find_boot_config():
    candidates = [
        Path("/boot/firmware/config.txt"),
        Path("/boot/config.txt"),
    ]
    for p in candidates:
        if p.exists():
            c(f"[INFO] Using boot config: {p}", CYAN)
            return p
    raise FileNotFoundError("No config.txt found")

def update_config_txt():
    try:
        cfg_path = find_boot_config()
        original = cfg_path.read_text()
        lines = original.splitlines()

        new_lines = []
        has_enable_uart = False
        has_disable_bt = False
        uart_value_ok = False

        c("[STEP] Updating UART settings in config.txt...", MAGENTA)

        for line in lines:
            stripped = line.strip()
            # Check if enable_uart exists and is already set to 1
            if stripped.startswith("enable_uart"):
                if "=" in stripped:
                    value = stripped.split("=", 1)[1].strip()
                    if value == "1":
                        uart_value_ok = True
                        new_lines.append("enable_uart=1")
                    else:
                        new_lines.append("enable_uart=1")
                    has_enable_uart = True
                else:
                    new_lines.append("enable_uart=1")
                    has_enable_uart = True
            elif stripped.startswith("dtoverlay=disable-bt"):
                new_lines.append("dtoverlay=disable-bt")
                has_disable_bt = True
            else:
                new_lines.append(line)

        if not has_enable_uart:
            new_lines.append("enable_uart=1")
            c("[ADD] enable_uart=1 appended", YELLOW)
        elif not uart_value_ok:
            c("[UPD] enable_uart updated to 1", YELLOW)
        else:
            c("[OK ] enable_uart already present and set to 1", GREEN)

        if not has_disable_bt:
            new_lines.append("dtoverlay=disable-bt")
            c("[ADD] dtoverlay=disable-bt appended", YELLOW)
        else:
            c("[OK ] dtoverlay=disable-bt already present", GREEN)

        backup = cfg_path.with_suffix(".bak")
        backup.write_text(original)
        cfg_path.write_text("\n".join(new_lines) + "\n")

        c(f"[OK ] Config updated: {cfg_path}", GREEN)
        c(f"[OK ] Backup saved as: {backup}", GREEN)
        return True
    except Exception as e:
        c(f"[ERROR] Failed to update config.txt: {e}", RED)
        return False

def find_cmdline():
    candidates = [
        Path("/boot/firmware/cmdline.txt"),
        Path("/boot/cmdline.txt"),
    ]
    for p in candidates:
        if p.exists():
            c(f"[INFO] Using cmdline: {p}", CYAN)
            return p
    return None

def update_cmdline_txt():
    try:
        c("[STEP] Cleaning UART console from cmdline.txt...", MAGENTA)
        cmd_path = find_cmdline()
        if not cmd_path:
            c("[WARN] No cmdline.txt found, skipping.", YELLOW)
            return True

        original = cmd_path.read_text().strip()
        if not original:
            c("[WARN] cmdline.txt is empty, skipping.", YELLOW)
            return True

        parts = original.split()
        filtered = [
            p for p in parts
            if not p.startswith("console=serial0")
            and not p.startswith("console=ttyAMA0")
        ]

        if parts == filtered:
            c("[OK ] No UART console entries found, nothing to remove.", GREEN)
            return True

        backup = cmd_path.with_suffix(".bak")
        backup.write_text(original + "\n")
        cmd_path.write_text(" ".join(filtered) + "\n")

        c(f"[OK ] UART console entries removed from: {cmd_path}", GREEN)
        c(f"[OK ] Backup saved as: {backup}", GREEN)
        return True
    except Exception as e:
        c(f"[ERROR] Failed to update cmdline.txt: {e}", RED)
        return False

def main():
    success1 = update_config_txt()
    success2 = update_cmdline_txt()
    if not (success1 and success2):
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

if [ $? -eq 0 ]; then
  ok "UART configuration done (reboot required to fully apply)."
else
  err "UART configuration failed. Please check the error messages above."
  exit 1
fi

# ===== 5. CHECK PORT AVAILABILITY =====
step "Checking if port $APP_PORT is available..."

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
  ok "Port $APP_PORT is available."
else
  warn "Port $APP_PORT is already in use!"
  warn "The service may fail to start. Please free the port or change APP_PORT in this script."
  warn "To check what's using the port: sudo netstat -tulpn | grep :$APP_PORT"
fi

# ===== 6. CREATE run_app.sh =====
step "Creating run_app.sh launcher..."

RUN_SCRIPT="$APP_DIR/run_app.sh"

# Check if run_app.sh exists and if it needs updating
NEEDS_UPDATE=false
if [ -f "$RUN_SCRIPT" ]; then
  if ! grep -q "uvicorn.*app.main:app" "$RUN_SCRIPT" 2>/dev/null; then
    NEEDS_UPDATE=true
    warn "Existing run_app.sh found but doesn't use uvicorn. Will update it."
  else
    ok "run_app.sh already exists and looks correct."
  fi
fi

if [ ! -f "$RUN_SCRIPT" ] || [ "$NEEDS_UPDATE" = true ]; then
  cat > "$RUN_SCRIPT" << EOS
#!/bin/bash
set -e
cd "$APP_DIR"
source venv/bin/activate

# Run FastAPI application with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port $APP_PORT
EOS

  chown "$APP_USER:$APP_USER" "$RUN_SCRIPT"
  chmod +x "$RUN_SCRIPT"
  if [ "$NEEDS_UPDATE" = true ]; then
    ok "Updated run_app.sh to use uvicorn."
  else
    ok "Created run_app.sh (using: uvicorn app.main:app --host 0.0.0.0 --port $APP_PORT)."
  fi
fi

# ===== 7. CREATE SYSTEMD SERVICE =====
step "Creating systemd service: $SERVICE_NAME..."

SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

cat > "$SERVICE_PATH" << EOF
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

ok "Systemd service file created: $SERVICE_PATH"

# ===== 8. ENABLE + START SERVICE =====
step "Enabling and starting systemd service..."

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# Try to start the service, or restart if it's already running
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
  info "Service is already running, restarting..."
  systemctl restart "$SERVICE_NAME"
else
  systemctl start "$SERVICE_NAME"
fi

# Wait a bit for the service to start
sleep 2

# Check service status
if systemctl is-active --quiet "$SERVICE_NAME"; then
  ok "Service is running successfully."
else
  err "Service failed to start!"
  err "Check the service status with: systemctl status $SERVICE_NAME"
  err "Check the logs with: journalctl -u $SERVICE_NAME -n 50"
  systemctl status "$SERVICE_NAME" --no-pager -l || true
  exit 1
fi

# ===== 9. CHECK IF UART WAS CONFIGURED =====
# Check if UART configuration was changed (backup file exists)
UART_WAS_CHANGED=false
if [ -f "/boot/config.txt.bak" ] || [ -f "/boot/firmware/config.txt.bak" ]; then
  UART_WAS_CHANGED=true
fi

# ===== 10. INSTALLATION SUMMARY =====
step "Installation Summary"

c "\n" ""
c "═══════════════════════════════════════════════════════════" "$BOLD"
c "           INSTALLATION SUMMARY" "$BOLD"
c "═══════════════════════════════════════════════════════════" "$BOLD"
c "" ""

info "✓ System Packages Installed:"
c "  • Python 3, pip, venv" "$GREEN"
c "  • Git" "$GREEN"
c "  • net-tools" "$GREEN"

info "✓ Application Installed:"
c "  • Location: $APP_DIR" "$GREEN"
c "  • Repository: $REPO_URL" "$GREEN"
if [ -d "$APP_DIR/venv" ]; then
  c "  • Python virtualenv: $APP_DIR/venv" "$GREEN"
fi

info "✓ Configuration Files:"
if [ "$UART_WAS_CHANGED" = true ]; then
  c "  • UART configured in /boot/config.txt" "$GREEN"
  c "  • UART console removed from cmdline.txt" "$GREEN"
else
  c "  • UART settings already configured" "$CYAN"
fi
c "  • Service file: $SERVICE_PATH" "$GREEN"
c "  • Launch script: $RUN_SCRIPT" "$GREEN"
c "  • Port: $APP_PORT" "$GREEN"

info "✓ Service Status:"
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
  c "  • Status: Running ✓" "$GREEN"
  c "  • Enabled: $(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || echo 'unknown')" "$GREEN"
else
  c "  • Status: Not running ✗" "$RED"
fi

c "" ""

# ===== 11. SHOW ACCESS INFO =====
step "Access Information"

# Get the first IP address
IP=$(hostname -I | awk '{print $1}' | head -1)

if [ -n "$IP" ] && [[ $IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  ok "Application is accessible at:"
  c "  • Network: http://$IP:$APP_PORT" "${BOLD}${CYAN}"
  c "  • Local:   http://localhost:$APP_PORT" "$CYAN"
else
  warn "Could not detect valid IP address."
  info "You can find your IP with: hostname -I"
  info "The app should be accessible on port $APP_PORT"
fi

c "" ""

# ===== 12. REBOOT REQUEST (if UART was changed) =====
if [ "$UART_WAS_CHANGED" = true ]; then
  c "" ""
  c "═══════════════════════════════════════════════════════════" "${BOLD}${RED}"
  c "⚠️  SYSTEM REBOOT REQUIRED FOR UART CONFIGURATION  ⚠️" "${BOLD}${RED}"
  c "═══════════════════════════════════════════════════════════" "${BOLD}${RED}"
  c "" ""
  c "The UART settings have been modified in /boot/config.txt" "${BOLD}${YELLOW}"
  c "These changes will ONLY take effect after a system reboot!" "${BOLD}${YELLOW}"
  c "" ""
  c "Please reboot the system now:" "$BOLD"
  c "  sudo reboot" "${BOLD}${CYAN}"
  c "" ""
  c "═══════════════════════════════════════════════════════════" "${BOLD}${RED}"
  c "" ""
fi

# ===== 13. USEFUL COMMANDS =====
c "Useful Commands:" "${BOLD}${CYAN}"
c "  • Check service status: sudo systemctl status $SERVICE_NAME" "$CYAN"
c "  • View service logs:     sudo journalctl -u $SERVICE_NAME -f" "$CYAN"
c "  • Restart service:       sudo systemctl restart $SERVICE_NAME" "$CYAN"
c "  • Stop service:          sudo systemctl stop $SERVICE_NAME" "$CYAN"
c "  • View all logs:         sudo journalctl -u $SERVICE_NAME -n 100" "$CYAN"

c "" ""
c "═══════════════════════════════════════════════════════════" "$BOLD"
c "                    INSTALLATION COMPLETE" "${BOLD}${GREEN}"
c "═══════════════════════════════════════════════════════════" "$BOLD"
c "" ""
