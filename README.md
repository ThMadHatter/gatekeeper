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
   git clone <repository-url>
   cd proxmox-gatekeeper
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
- `GET /proxmox/list-lxcs`: List all LXC containers on the node.
- `POST /proxmox/create-lxc`: Create a new LXC container.
- `POST /proxmox/execute`: Execute a command inside an LXC (Container must be running).
- `POST /proxmox/start-lxc/{vmid}`: Start an LXC container.
- `POST /proxmox/stop-lxc/{vmid}`: Stop an LXC container.
- `GET /proxmox/status-lxc/{vmid}`: Get the current status of an LXC container.
- `GET /proxmox/tasks/{upid}`: Get the status of a Proxmox task.
- `GET /proxmox/templates?storage=local`: List templates currently on a storage.
- `GET /proxmox/available-templates`: List official templates available for download.
- `POST /proxmox/download-official-template`: Download an official template to storage.
- `POST /proxmox/download-template`: Download an LXC template from a custom URL to storage.
- `POST /proxmox/upload-template`: Upload a local LXC template file to storage.
- `DELETE /proxmox/delete-template/{storage}/{volume:path}`: Delete a template volume.
- `DELETE /proxmox/delete-lxc/{vmid}`: Delete an LXC container.

> **Note on .tar.zst support**: Proxmox 8.x supports `.tar.zst` templates. If you are on an older version of Proxmox, ensure you use `.tar.gz` templates.

### Template Repository Management

- `GET /repos`: List registered online template repositories.
- `POST /repos`: Register a new template repository URL (validates URL on add).
- `DELETE /repos/{name}`: Remove a registered repository.

### Documentation & Help

- `GET /help`: Show a detailed guide of all available API endpoints and their usage.

## Testing

The repository includes a comprehensive test suite using `pytest`.

### Running Mocked Tests
To run the tests without a real Proxmox server (using mocks):
```bash
# Provide dummy credentials for config validation
export PROXMOX_HOST=dummy
export PROXMOX_USER=dummy
export PROXMOX_TOKEN_NAME=dummy
export PROXMOX_TOKEN_VALUE=dummy
export PROXMOX_NODE=dummy

pytest
```

### Real Environment Integration Testing
The integration test verifies the full lifecycle: **Download Template locally -> Upload to Proxmox -> Create LXC -> Start -> Execute -> Stop -> Delete LXC -> Delete Template**.

To run it:
1. Ensure your `.secrets` file or environment variables are correctly set.
2. Set `RUN_REAL_TESTS=true`.

```bash
export RUN_REAL_TESTS=true
export TEST_VMID=999
export TEST_TEMPLATE_STORAGE="local"
export TEST_ROOTFS_STORAGE="local-lvm"
# Note: Use a valid, reachable template URL and filename for integration tests.
# If TEST_TEMPLATE_URL ends in '/', TEST_TEMPLATE_NAME will be appended.
export TEST_TEMPLATE_URL="http://download.proxmox.com/images/system/"
export TEST_TEMPLATE_NAME="debian-13-standard_13.1-2_amd64.tar.zst"

# Troubleshooting Uploads:
# If uploads fail with "RemoteDisconnected", check your Proxmox host's firewall
# or ensure the local storage has enough space for the template.
export TEST_PASSWORD="your-test-password"
export TEST_NET0="name=eth0,bridge=vmbr0,ip=dhcp"
export TEST_FEATURES="nesting=1" # Recommended for Debian 13 / Systemd 257
# Note: Features other than 'nesting' (like keyctl) may require root@pam permissions.
# Plus all required PROXMOX_* variables if not in .secrets
pytest -s tests/test_integration.py
```

### Coverage
To check test coverage:
```bash
pytest --cov=app tests/
```

## Security Note
Always run this application behind a firewall or within a secure network segment. Ensure `.secrets` file permissions are restricted (the installer sets them to 600).
