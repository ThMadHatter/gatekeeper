# Proxmox Gatekeeper API

A clean, production-grade FastAPI application designed to run inside a secure Debian LXC to act as a gatekeeper for Proxmox API operations.

## Features
- **Modular Structure**: Easily extendable with new routers and services.
- **Secure Configuration**: Uses `.secrets` file for environment variables.
- **FastAPI**: Modern, high-performance web framework.
- **Proxmoxer**: Robust Python wrapper for Proxmox REST API.
- **Systemd Integration**: Runs as a background service with automated installation.
- **Structured Logging**: Logs to stdout/stderr (captured by journald) and optional log file.

## Repository Structure
- `app/`: Main application logic.
  - `config.py`: Configuration loading and validation.
  - `main.py`: App initialization and logging setup.
  - `routers/`: API endpoints.
  - `services/`: Business logic and API wrappers.
- `install.sh`: Automated installation and setup script.
- `requirements.txt`: Python dependencies.
- `tests/`: Test suite.

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ThMadHatter/gatekeeper.git
   cd gatekeeper
   ```

2. **Run the installer**:
   ```bash
   sudo ./install.sh
   ```

3. **Configure your secrets**:
   Edit the `.secrets` file created in the root directory:
   ```bash
   nano .secrets
   ```
   Fill in your Proxmox host, user, token name, token value, and node.

4. **Restart the service**:
   ```bash
   sudo systemctl restart gatekeeper
   ```

5. **Verify the installation**:
   Check the logs:
   ```bash
   journalctl -u gatekeeper -f
   ```
   Or visit `http://<lxc-ip>:8000/` in your browser.

## API Endpoints

- `GET /`: Health check.
- `POST /proxmox/create-lxc`: Create a new LXC container.
- `POST /proxmox/execute`: Execute a command inside an LXC.

## Security Note
Always run this application behind a firewall or within a secure network segment. Ensure `.secrets` file permissions are restricted (the installer sets them to 600).
