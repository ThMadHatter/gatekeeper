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

def test_service_get_task_status_success(service):
    with patch.object(service.proxmox.nodes("dummy").tasks("upid").status, "get", return_value={"status": "stopped"}):
        res = service.get_task_status("upid")
        assert res == {"status": "stopped"}

def test_service_list_templates_success(service):
    with patch.object(service.proxmox.nodes("dummy").storage("local").content, "get", return_value=[]):
        res = service.list_templates("local")
        assert res == []

def test_service_get_task_status_error(service):
    with patch.object(service.proxmox.nodes("dummy").tasks("upid").status, "get", side_effect=Exception("Task Error")):
        with pytest.raises(Exception) as exc:
            service.get_task_status("upid")
        assert "Task Error" in str(exc.value)

def test_service_list_templates_error(service):
    with patch.object(service.proxmox.nodes("dummy").storage("local").content, "get", side_effect=Exception("Template Error")):
        with pytest.raises(Exception) as exc:
            service.list_templates("local")
        assert "Template Error" in str(exc.value)

def test_service_download_template_success(service):
    with patch.object(service.proxmox.nodes("dummy").storage("local").download_url, "post", return_value="UPID:download"):
        res = service.download_template("local", "url", "file")
        assert res == "UPID:download"

def test_service_delete_template_success(service):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": "UPID:delete"}
    with patch("requests.Session.delete", return_value=mock_resp):
        res = service.delete_template("local", "vol")
        assert res == "UPID:delete"

def test_service_delete_template_not_found(service):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    with patch("requests.Session.delete", return_value=mock_resp):
        res = service.delete_template("local", "vol")
        assert res == {"message": "Not found"}

def test_service_download_template_error(service):
    with patch.object(service.proxmox.nodes("dummy").storage("local").download_url, "post", side_effect=Exception("Download Error")):
        with pytest.raises(Exception) as exc:
            service.download_template("local", "url", "file")
        assert "Download Error" in str(exc.value)

def test_service_delete_template_error(service):
    with patch("requests.Session.delete", side_effect=Exception("Delete Error")):
        with pytest.raises(Exception) as exc:
            service.delete_template("local", "vol")
        assert "Delete Error" in str(exc.value)

def test_service_get_available_templates_success(service):
    with patch.object(service.proxmox.nodes("dummy").aplinfo, "get", return_value=[]):
        res = service.get_available_templates()
        assert res == []

def test_service_download_official_template_success(service):
    with patch.object(service.proxmox.nodes("dummy").vztmpl, "post", return_value="UPID:down_off"):
        res = service.download_official_template("local", "debian-11")
        assert res == "UPID:down_off"

def test_service_get_available_templates_error(service):
    with patch.object(service.proxmox.nodes("dummy").aplinfo, "get", side_effect=Exception("Avail Error")):
        with pytest.raises(Exception) as exc:
            service.get_available_templates()
        assert "Avail Error" in str(exc.value)

def test_service_download_official_template_error(service):
    with patch.object(service.proxmox.nodes("dummy").vztmpl, "post", side_effect=Exception("Down Off Error")):
        with pytest.raises(Exception) as exc:
            service.download_official_template("local", "debian-11")
        assert "Down Off Error" in str(exc.value)

def test_service_upload_template_from_path_success(service):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": "UPID:upload"}
    with patch("requests.Session.post", return_value=mock_resp):
        with patch("os.path.getsize", return_value=100):
            with patch("builtins.open"):
                res = service.upload_template_from_path("local", "file", "path")
                assert res == "UPID:upload"

def test_service_upload_template_from_path_error(service):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Error detail"
    mock_resp.raise_for_status.side_effect = Exception("HTTP Error")
    mock_resp.ok = False
    with patch("requests.Session.post", return_value=mock_resp):
        with patch("os.path.getsize", return_value=100):
            with patch("builtins.open"):
                with pytest.raises(Exception) as exc:
                    service.upload_template_from_path("local", "file", "path")
                assert "HTTP Error" in str(exc.value)

def test_service_upload_template_from_path_curl_fallback(service):
    # Mock requests to fail with a connection error
    with patch("requests.Session.post", side_effect=Exception("RemoteDisconnected")):
        with patch("os.path.getsize", return_value=100):
            with patch("builtins.open"):
                # Mock subprocess to succeed
                mock_proc = MagicMock()
                mock_proc.returncode = 0
                mock_proc.stdout = '{"data": "UPID:curl"}'
                with patch("subprocess.run", return_value=mock_proc):
                    res = service.upload_template_from_path("local", "file", "path")
                    assert res == "UPID:curl"

def test_service_upload_template_curl_error(service):
    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stderr = "Curl failed"
    with patch("subprocess.run", return_value=mock_proc):
        with pytest.raises(RuntimeError) as exc:
            service.upload_template_from_path_with_curl("local", "file", "path")
        assert "curl upload failed" in str(exc.value)

def test_service_upload_template_wrapper(service):
    with patch.object(service, "upload_template_from_path", return_value="UPID:wrapper"):
        res = service.upload_template("local", "file", b"content")
        assert res == "UPID:wrapper"
