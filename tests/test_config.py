import os
import pytest
from app.config import Settings

def test_config_loading_from_env(monkeypatch):
    monkeypatch.setenv("PROXMOX_HOST", "test-host")
    monkeypatch.setenv("PROXMOX_USER", "test-user")
    monkeypatch.setenv("PROXMOX_TOKEN_NAME", "test-token-name")
    monkeypatch.setenv("PROXMOX_TOKEN_VALUE", "test-token-value")
    monkeypatch.setenv("PROXMOX_NODE", "test-node")

    # Pass _env_file=None to ignore any real .secrets file during testing
    settings = Settings(_env_file=None)

    assert settings.PROXMOX_HOST == "test-host"
    assert settings.PROXMOX_USER == "test-user"
    assert settings.LOG_LEVEL == "INFO"

def test_config_missing_variable(monkeypatch):
    monkeypatch.delenv("PROXMOX_HOST", raising=False)
    # We expect pydantic to raise a ValidationError if we try to instantiate Settings without required env vars
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
