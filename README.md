# YT-Drone

Modular application for managing drones and surrounding systems.

## Version V1 - System Monitoring & Real-time Updates

This version includes:
- **Real System Monitoring** - Real-time system data collection (CPU, RAM, Storage, Temperature)
- **WebSocket Integration** - Real-time updates via WebSocket
- **Real-time Dashboard** - Automatically updated system data display
- **Advanced UI** - Responsive design with theme support

## Features

### System Monitoring
- **System Information**: Operating system, hardware, uptime
- **CPU Monitoring**: Temperature, usage, progress bars with visual indicators
- **RAM Monitoring**: Real-time memory usage
- **Storage Monitoring**: Tracking of Boot partition (MB) and Root partition (GB) with progress bars

### Real-time Updates
- **WebSocket Integration**: Automatic updates every 5 seconds (CPU, RAM, Temperature) and every 60 seconds (Storage, Uptime)
- **Monitor Manager**: Centralized management of all monitors with periodic updates
- **Live Dashboard**: Automatic update of all fields without page refresh

### UI/UX
- **Theme Support**: 3 themes (Light, Medium, Dark)
- **Responsive Design**: Full support for different screens (desktop, tablet, mobile)
- **Modern UI**: Clean and modern design with cards, progress bars, and icons
- **Sidebar Navigation**: Collapsible side menu with icons for each module

## Installation on Raspberry Pi

### Prerequisites

Before starting the installation, make sure you have:

- **Raspberry Pi** with **Raspberry Pi OS** installed (latest version recommended)
- **Active internet connection**
- **Root privileges** (access to `sudo`)
- **Clean operating system** or existing system you want to install on

### Automatic Installation (Recommended)

The easiest and fastest way to install the application is using the automatic installation script:

```bash
curl -fsSL https://raw.githubusercontent.com/yossits/yt-drone/main/install.sh | sudo bash
```

**What the script does:**

1. **Install system packages** - Python 3, Git, pip, venv, net-tools
2. **Clone/Update Repository** - Download code from GitHub repository
3. **Create virtual environment** - Python virtualenv and install all dependencies
4. **Configure UART** - Configure UART for hardware (enable_uart=1, disable-bt)
5. **Check port** - Verify that port 8001 is available
6. **Create launch file** - Create `run_app.sh` to run the application
7. **Create Systemd service** - Configure service for automatic startup
8. **Start service** - Automatically start the application

**After installation:**

- If UART was changed, **a system reboot will be required**
- The application will run automatically as a systemd service
- You can access the application at: `http://[Raspberry-Pi-IP]:8001`

**Useful commands:**

```bash
# Check service status
sudo systemctl status yt-drone.service

# View logs
sudo journalctl -u yt-drone.service -f

# Restart service
sudo systemctl restart yt-drone.service

# Stop service
sudo systemctl stop yt-drone.service
```

### Manual Installation

If you prefer to install manually, follow these steps:

#### 1. Update system and install basic packages

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip net-tools
```

#### 2. Clone repository

```bash
cd /home/pi
git clone https://github.com/yossits/yt-drone.git
cd yt-drone
```

#### 3. Create virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure UART

Edit the `/boot/config.txt` file:

```bash
sudo nano /boot/config.txt
```

Add or ensure the following lines exist:

```
enable_uart=1
dtoverlay=disable-bt
```

Save the file (Ctrl+O, Enter, Ctrl+X).

Edit the `/boot/cmdline.txt` file and remove any references to `console=serial0` or `console=ttyAMA0`:

```bash
sudo nano /boot/cmdline.txt
```

**Important:** After changing UART files, **reboot the system**:

```bash
sudo reboot
```

#### 5. Add user to dialout group

Add the user to the `dialout` group to allow access to serial ports:

```bash
sudo usermod -a -G dialout $USER
```

**Important:** After adding the user to the group, **logout and login again** (or run `newgrp dialout`) for the changes to take effect.

Verify the user is in the group:
```bash
groups
```
You should see `dialout` in the list.

#### 6. Create launch file

Create `run_app.sh` file:

```bash
nano /home/pi/yt-drone/run_app.sh
```

Add the following content:

```bash
#!/bin/bash
set -e
cd /home/pi/yt-drone
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Save the file and make it executable:

```bash
chmod +x /home/pi/yt-drone/run_app.sh
```

#### 7. Create Systemd service

Create service file:

```bash
sudo nano /etc/systemd/system/yt-drone.service
```

Add the following content:

```ini
[Unit]
Description=YT-Drone Application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/yt-drone
ExecStart=/home/pi/yt-drone/run_app.sh
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Save the file.

#### 8. Start service

```bash
sudo systemctl daemon-reload
sudo systemctl enable yt-drone.service
sudo systemctl start yt-drone.service
```

Check that the service is running:

```bash
sudo systemctl status yt-drone.service
```

### Troubleshooting

#### Service won't start

1. Check the logs:
   ```bash
   sudo journalctl -u yt-drone.service -n 50
   ```

2. Check that the port is available:
   ```bash
   sudo netstat -tulpn | grep 8001
   ```

3. Check that the `run_app.sh` file exists and has execute permissions:
   ```bash
   ls -l /home/pi/yt-drone/run_app.sh
   ```

#### Dependency installation errors

1. Make sure you have an internet connection
2. Try updating pip:
   ```bash
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

#### UART not working

1. Make sure you rebooted after changing UART files
2. Check the `/boot/config.txt` file:
   ```bash
   cat /boot/config.txt | grep uart
   ```
3. Check the `/boot/cmdline.txt` file that it doesn't have console=serial0:
   ```bash
   cat /boot/cmdline.txt
   ```

#### Cannot access application from network

1. Check the Raspberry Pi IP address:
   ```bash
   hostname -I
   ```

2. Check that the service is running:
   ```bash
   sudo systemctl status yt-drone.service
   ```

3. Check the firewall (if present):
   ```bash
   sudo ufw status
   ```

## Installation (Other Platforms)

```bash
# Create virtual environment
python -m venv venv

# Activate environment (Windows)
venv\Scripts\activate

# Activate environment (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

### On Raspberry Pi (as service)

If you installed the application with `install.sh`, it will run automatically as a systemd service. The service will start automatically on every boot.

**Service management:**

```bash
# Check status
sudo systemctl status yt-drone.service

# Start
sudo systemctl start yt-drone.service

# Stop
sudo systemctl stop yt-drone.service

# Restart
sudo systemctl restart yt-drone.service

# View logs in real-time
sudo journalctl -u yt-drone.service -f
```

### Manual run

For manual run (for development or testing):

```bash
cd /home/pi/yt-drone
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Note:** If the systemd service is running, stop it first:

```bash
sudo systemctl stop yt-drone.service
```

The application will be available at: `http://[Raspberry-Pi-IP]:8001` or `http://localhost:8001`

## Project Structure

The project is built in a modular way, where each module contains:

- `router.py` - Module routes
- `services.py` - Logic and demo/real data
- `templates/` - HTML templates of the module

### Main directories

- `app/core/` - Shared services:
  - `system.py` - System data collection (CPU, RAM, Storage, Temperature)
  - `websocket.py` - WebSocket Manager for connection management
  - `websocket_router.py` - WebSocket endpoints
  - `monitor_manager.py` - Monitor management with periodic updates
  - `templates.py` - Jinja2 template support
  - `static.py` - Static file management

- `app/modules/` - Application modules
- `app/shared/` - Shared templates and resources
- `app/static/` - Static files (CSS, JS, Images)

## Modules

- **Dashboard** - Real-time system data display with system monitoring
- **Flight Controller** - Flight controller management (UI only)
- **Flight Map** - Flight tracking map (UI only)
- **Ground Control Station** - Ground control station (UI only)
- **Modem** - Modem management (UI only)
- **VPN** - VPN management (UI only)
- **Dynamic DNS** - Dynamic DNS management (UI only)
- **Camera** - Camera management (UI only)
- **Networks** - Network management (UI only)
- **Users** - User management (UI only)
- **Application** - Application settings (UI only)

## Technologies

- **Backend**:
  - FastAPI - Web framework
  - WebSocket - Real-time communication
  - psutil - System information gathering
  - Jinja2 - Template engine

- **Frontend**:
  - HTML5, CSS3 - Responsive design
  - JavaScript (ES6+) - WebSocket client, DOM manipulation
  - SVG Icons - Vector graphics

- **Infrastructure**:
  - Uvicorn - ASGI server
  - Monitor Manager - Periodic task scheduling

## Dependencies

Main dependencies:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `jinja2` - Template engine
- `psutil` - System information
- `python-multipart` - Form handling

See `requirements.txt` for the full list.
