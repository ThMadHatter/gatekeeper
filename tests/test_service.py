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

def test_service_execute_command_501_error(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100).exec, "post", side_effect=Exception("501 Not Implemented")):
        with pytest.raises(Exception) as exc:
            service.execute_command(100, "ls")
        assert "501 Not Implemented" in str(exc.value)

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

def test_service_start_lxc_error(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100).status.start, "post", side_effect=Exception("Start Error")):
        with pytest.raises(Exception) as exc:
            service.start_lxc(100)
        assert "Start Error" in str(exc.value)

def test_service_stop_lxc_error(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100).status.stop, "post", side_effect=Exception("Stop Error")):
        with pytest.raises(Exception) as exc:
            service.stop_lxc(100)
        assert "Stop Error" in str(exc.value)

def test_service_get_status_error(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100).status.current, "get", side_effect=Exception("Status Error")):
        with pytest.raises(Exception) as exc:
            service.get_lxc_status(100)
        assert "Status Error" in str(exc.value)

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

def test_service_start_lxc_success(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100).status.start, "post", return_value="UPID:4"):
        res = service.start_lxc(100)
        assert res == "UPID:4"

def test_service_stop_lxc_success(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100).status.stop, "post", return_value="UPID:5"):
        res = service.stop_lxc(100)
        assert res == "UPID:5"

def test_service_get_status_success(service):
    with patch.object(service.proxmox.nodes("dummy").lxc(100).status.current, "get", return_value={"status": "running"}):
        res = service.get_lxc_status(100)
        assert res == {"status": "running"}
