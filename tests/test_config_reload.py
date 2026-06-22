import pytest
import importlib
import os
import sys

def test_config_validation_failure_exit(monkeypatch):
    # Ensure required env vars are missing
    monkeypatch.delenv("PROXMOX_HOST", raising=False)
    monkeypatch.delenv("PROXMOX_USER", raising=False)
    monkeypatch.delenv("PROXMOX_TOKEN_NAME", raising=False)
    monkeypatch.delenv("PROXMOX_TOKEN_VALUE", raising=False)
    monkeypatch.delenv("PROXMOX_NODE", raising=False)

    # Temporarily hide .secrets file if it exists
    secrets_existed = os.path.exists(".secrets")
    if secrets_existed:
        os.rename(".secrets", ".secrets.bak")

    try:
        # Force reload of app.config
        if "app.config" in sys.modules:
            import app.config
            with pytest.raises(SystemExit) as exc:
                importlib.reload(app.config)
            assert "Error: Missing or invalid configuration variables" in str(exc.value)
        else:
            with pytest.raises(SystemExit) as exc:
                import app.config
            assert "Error: Missing or invalid configuration variables" in str(exc.value)
    finally:
        # Restore .secrets file
        if secrets_existed:
            os.rename(".secrets.bak", ".secrets")
