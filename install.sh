#!/bin/bash

# Proxmox Gatekeeper API Installer Script
# Highly robust, idempotent bash script for Debian LXC

set -e

# 1. Verify script is running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/venv"
DATA_DIR="$APP_DIR/data"
SECRETS_FILE="$APP_DIR/.secrets"
SERVICE_NAME="gatekeeper"
USER_NAME=$(logname || echo "root")

echo "Installing Proxmox Gatekeeper API in $APP_DIR..."

# 2. Update and Install Dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3-venv python3-pip

# 3. Create Python virtual environment and data directory
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

if [ ! -d "$DATA_DIR" ]; then
    echo "Creating data directory..."
    mkdir -p "$DATA_DIR"
    chown "$USER_NAME":"$USER_NAME" "$DATA_DIR"
fi

# 4. Install requirements
echo "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

# 5. Create template .secrets file if it doesn't exist
if [ ! -f "$SECRETS_FILE" ]; then
    echo "Creating template .secrets file..."
    cat <<EOF > "$SECRETS_FILE"
PROXMOX_HOST=your-proxmox-host
PROXMOX_USER=root@pam
PROXMOX_TOKEN_NAME=gatekeeper
PROXMOX_TOKEN_VALUE=your-token-value
PROXMOX_NODE=pve
LOG_LEVEL=INFO
EOF
    chown "$USER_NAME":"$USER_NAME" "$SECRETS_FILE"
    chmod 600 "$SECRETS_FILE"
    echo "!!! IMPORTANT: Please edit $SECRETS_FILE with your Proxmox credentials !!!"
fi

# 6. Create the systemd service unit file
echo "Creating systemd service..."
cat <<EOF > "/etc/systemd/system/$SERVICE_NAME.service"
[Unit]
Description=Proxmox Gatekeeper API Service
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$SECRETS_FILE
ExecStart=$VENV_DIR/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 7. Reload systemd, enable and start service
echo "Reloading systemd and starting service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo "--------------------------------------------------------"
echo "Installation Complete!"
echo "--------------------------------------------------------"
echo "The service is now running (or trying to, check logs)."
echo "Edit your configuration at: $SECRETS_FILE"
echo "View logs: journalctl -u $SERVICE_NAME -f"
echo "Restart service: systemctl restart $SERVICE_NAME"
echo "--------------------------------------------------------"
