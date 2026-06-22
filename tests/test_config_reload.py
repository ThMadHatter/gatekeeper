import pytest
import importlib
import os
import sys
from unittest.mock import patch

def test_config_validation_failure_exit(monkeypatch):
    # Ensure required env vars are missing
    monkeypatch.delenv("PROXMOX_HOST", raising=False)
    monkeypatch.delenv("PROXMOX_USER", raising=False)
    monkeypatch.delenv("PROXMOX_TOKEN_NAME", raising=False)
    monkeypatch.delenv("PROXMOX_TOKEN_VALUE", raising=False)
    monkeypatch.delenv("PROXMOX_NODE", raising=False)

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
