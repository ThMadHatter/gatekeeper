import pytest
from app.services.proxmox_service import ProxmoxService
from unittest.mock import patch, MagicMock

@pytest.fixture
def service():
    # Use dummy settings for init
    with patch("app.services.proxmox_service.ProxmoxAPI"):
        return ProxmoxService()

def test_service_create_lxc_error(service):
    with patch.object(service.proxmox.nodes("dummy").lxc, "create", side_effect=Exception("API Error")):
        with pytest.raises(Exception) as exc:
            service.create_lxc(100, "temp", "host")
        assert "API Error" in str(exc.value)

def test_service_execute_command_error(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100).exec, "post", side_effect=Exception("Exec Error")):
        with pytest.raises(Exception) as exc:
            service.execute_command(100, "ls")
        assert "Exec Error" in str(exc.value)

def test_service_list_lxcs_error(service):
    with patch.object(service.proxmox.nodes("dummy").lxc, "get", side_effect=Exception("List Error")):
        with pytest.raises(Exception) as exc:
            service.list_lxcs()
        assert "List Error" in str(exc.value)

def test_service_delete_lxc_error(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100), "delete", side_effect=Exception("Delete Error")):
        with pytest.raises(Exception) as exc:
            service.delete_lxc(100)
        assert "Delete Error" in str(exc.value)

def test_service_create_lxc_success(service):
    with patch.object(service.proxmox.nodes("dummy").lxc, "create", return_value="UPID:1"):
        res = service.create_lxc(100, "temp", "host")
        assert res == "UPID:1"

def test_service_list_lxcs_success(service):
    with patch.object(service.proxmox.nodes("dummy").lxc, "get", return_value=[]):
        res = service.list_lxcs()
        assert res == []

def test_service_execute_command_success(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100).exec, "post", return_value="UPID:2"):
        res = service.execute_command(100, "ls")
        assert res == "UPID:2"

def test_service_delete_lxc_success(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100), "delete", return_value="UPID:3"):
        res = service.delete_lxc(100)
        assert res == "UPID:3"
