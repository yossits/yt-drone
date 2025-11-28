#!/bin/bash
set -e

# ===== BASIC SETTINGS =====
APP_USER="pi"
APP_DIR="/home/pi/yt-drone"       # תשנה את השם אם אתה רוצה
REPO_URL="https://github.com/YOUR_USER/YOUR_REPO.git"  # <- לעדכן!
SERVICE_NAME="drone-hub.service"
PYTHON="/usr/bin/python3"
APP_PORT=8001                      # פורט ה-HTTP של האפליקציה שלך

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
apt-get install -y git python3 python3-venv python3-pip

ok "System packages installed."

# ===== 2. CLONE / UPDATE REPO =====
step "Preparing application directory..."

if [ ! -d "$APP_DIR" ]; then
  sudo -u "$APP_USER" mkdir -p "$APP_DIR"
  ok "Created directory: $APP_DIR"
fi

if [ ! -d "$APP_DIR/.git" ]; then
  step "Cloning repository..."
  sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
  ok "Repository cloned into $APP_DIR"
else
  step "Repository already exists, pulling latest changes..."
  sudo -u "$APP_USER" bash -c "cd '$APP_DIR' && git pull"
  ok "Repository updated."
fi

# ===== 3. PYTHON VENV + REQUIREMENTS =====
step "Creating Python virtualenv and installing requirements..."

sudo -u "$APP_USER" bash -c "
  cd '$APP_DIR'
  if [ ! -d 'venv' ]; then
    $PYTHON -m venv venv
  fi
  source venv/bin/activate
  if [ -f 'requirements.txt' ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
  else
    echo 'No requirements.txt found, skipping pip install.'
  fi
"

ok "Virtualenv and Python dependencies ready."

# ===== 4. CONFIGURE UART (EMBED PYTHON) =====
step "Configuring UART for hardware serial (serial0 -> ttyAMA0)..."

$PYTHON << 'EOF'
from pathlib import Path

RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"

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
    cfg_path = find_boot_config()
    original = cfg_path.read_text()
    lines = original.splitlines()

    new_lines = []
    has_enable_uart = False
    has_disable_bt = False

    c("[STEP] Updating UART settings in config.txt...", MAGENTA)

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("enable_uart"):
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
    else:
        c("[OK ] enable_uart already present - set to 1", GREEN)

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
    c("[STEP] Cleaning UART console from cmdline.txt...", MAGENTA)
    cmd_path = find_cmdline()
    if not cmd_path:
        c("[WARN] No cmdline.txt found, skipping.", YELLOW)
        return

    original = cmd_path.read_text().strip()
    if not original:
        c("[WARN] cmdline.txt is empty, skipping.", YELLOW)
        return

    parts = original.split()
    filtered = [
        p for p in parts
        if not p.startswith("console=serial0")
        and not p.startswith("console=ttyAMA0")
    ]

    if parts == filtered:
        c("[OK ] No UART console entries found, nothing to remove.", GREEN)
        return

    backup = cmd_path.with_suffix(".bak")
    backup.write_text(original + "\n")
    cmd_path.write_text(" ".join(filtered) + "\n")

    c(f"[OK ] UART console entries removed from: {cmd_path}", GREEN)
    c(f"[OK ] Backup saved as: {backup}", GREEN)

def main():
    update_config_txt()
    update_cmdline_txt()

if __name__ == "__main__":
    main()
EOF

ok "UART configuration done (reboot required to fully apply)."

# ===== 5. CREATE run_app.sh =====
step "Creating run_app.sh launcher..."

RUN_SCRIPT="$APP_DIR/run_app.sh"

if [ ! -f "$RUN_SCRIPT" ]; then
  cat > "$RUN_SCRIPT" << EOS
#!/bin/bash
set -e
cd "$APP_DIR"
source venv/bin/activate

# TODO: adjust this line to your actual app entrypoint
# Example for FastAPI with Uvicorn:
# uvicorn app.main:app --host 0.0.0.0 --port $APP_PORT

python -m app.main
EOS

  chown "$APP_USER:$APP_USER" "$RUN_SCRIPT"
  chmod +x "$RUN_SCRIPT"
  ok "Created run_app.sh (using: python -m app.main)."
else
  ok "run_app.sh already exists, not overwriting."
fi

# ===== 6. CREATE SYSTEMD SERVICE =====
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

# ===== 7. ENABLE + START SERVICE =====
step "Enabling and starting systemd service..."

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

ok "Service enabled and started."

# ===== 8. SHOW ACCESS INFO =====
step "Installation finished."

IP=$(hostname -I | awk '{print $1}')
if [ -n "$IP" ]; then
  ok "You can now open the app in your browser on the local network:"
  c "  http://$IP:$APP_PORT" "$CYAN"
else
  warn "Could not detect IP address. Use: hostname -I"
fi

c "\n=== ALL DONE ===" "$BOLD"
c "If UART settings were changed, consider rebooting:" "$YELLOW"
c "  sudo reboot" "$YELLOW"
