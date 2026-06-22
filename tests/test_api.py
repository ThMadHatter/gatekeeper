import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Proxmox Gatekeeper API is running"}

@pytest.mark.asyncio
async def test_create_lxc_endpoint_mocked():
    # Mock ProxmoxService
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.create_lxc.return_value = {"vmid": 100}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/create-lxc", json={
                "vmid": 100,
                "ostemplate": "local:vztmpl/debian-11-standard_11.0-1_amd64.tar.gz",
                "hostname": "test-lxc"
            })

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["data"] == {"vmid": 100}

@pytest.mark.asyncio
async def test_execute_endpoint_mocked():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.execute_command.return_value = "UPID:pve:00001234:00005678:..."

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/execute", json={
                "vmid": 100,
                "command": "ls -l"
            })

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "UPID" in response.json()["data"]

@pytest.mark.asyncio
async def test_create_lxc_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.create_lxc.side_effect = Exception("Router Error")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/create-lxc", json={
                "vmid": 100,
                "ostemplate": "temp",
                "hostname": "test"
            })

        assert response.status_code == 500
        assert "Router Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_lxcs_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_lxcs.side_effect = Exception("List Error")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/list-lxcs")

        assert response.status_code == 500
        assert "List Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_execute_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.execute_command.side_effect = Exception("Exec Error")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/execute", json={"vmid": 100, "command": "ls"})

        assert response.status_code == 500
        assert "Exec Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_lxc_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.delete_lxc.side_effect = Exception("Delete Error")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.delete("/proxmox/delete-lxc/100")

        assert response.status_code == 500
        assert "Delete Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_available_templates_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_available_templates.return_value = []
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/available-templates")
        assert response.status_code == 200
        assert response.json()["data"] == []

@pytest.mark.asyncio
async def test_download_official_template_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.download_official_template.return_value = "UPID:down_off"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/download-official-template", json={
                "storage": "local", "template": "debian-11"
            })
        assert response.status_code == 200
        assert response.json()["data"] == "UPID:down_off"

@pytest.mark.asyncio
async def test_get_available_templates_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_available_templates.side_effect = Exception("Avail Error")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/available-templates")
        assert response.status_code == 500
        assert "Avail Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_download_official_template_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.download_official_template.side_effect = Exception("Down Off Error")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/download-official-template", json={
                "storage": "local", "template": "debian-11"
            })
        assert response.status_code == 500
        assert "Down Off Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_execute_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.execute_command.return_value = "UPID:exec"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/execute", json={"vmid": 100, "command": "ls"})
        assert response.status_code == 200
        assert response.json()["data"] == "UPID:exec"

@pytest.mark.asyncio
async def test_list_lxcs_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_lxcs.return_value = []
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/list-lxcs")
        assert response.status_code == 200
        assert response.json()["data"] == []

@pytest.mark.asyncio
async def test_create_lxc_endpoint_success_no_params():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.create_lxc.return_value = "UPID:create"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/create-lxc", json={
                "vmid": 100, "ostemplate": "t", "hostname": "h"
            })
        assert response.status_code == 200
        assert response.json()["data"] == "UPID:create"

@pytest.mark.asyncio
async def test_list_templates_endpoint_success_no_storage():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_templates.return_value = []
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/templates")
        assert response.status_code == 200
        assert response.json()["data"] == []

@pytest.mark.asyncio
async def test_list_templates_endpoint_default_storage():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_templates.return_value = []
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/templates")
        assert response.status_code == 200
        assert response.json()["data"] == []

@pytest.mark.asyncio
async def test_start_lxc_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.start_lxc.side_effect = Exception("Start Error")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/start-lxc/100")
        assert response.status_code == 500
        assert "Start Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_stop_lxc_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.stop_lxc.side_effect = Exception("Stop Error")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/stop-lxc/100")
        assert response.status_code == 500
        assert "Stop Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_status_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_lxc_status.side_effect = Exception("Status Error")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/status-lxc/100")
        assert response.status_code == 500
        assert "Status Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_stop_lxc_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.stop_lxc.return_value = "UPID:stop"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/stop-lxc/100")
        assert response.status_code == 200
        assert response.json()["data"] == "UPID:stop"

@pytest.mark.asyncio
async def test_start_lxc_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.start_lxc.return_value = "UPID:start"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/start-lxc/100")
        assert response.status_code == 200
        assert response.json()["data"] == "UPID:start"

@pytest.mark.asyncio
async def test_get_status_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_lxc_status.return_value = {"status": "running"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/status-lxc/100")
        assert response.status_code == 200
        assert response.json()["data"] == {"status": "running"}

@pytest.mark.asyncio
async def test_get_task_status_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_task_status.return_value = {"status": "stopped"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/tasks/upid")
        assert response.status_code == 200
        assert response.json()["data"] == {"status": "stopped"}

@pytest.mark.asyncio
async def test_list_templates_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_templates.return_value = []
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/templates?storage=local")
        assert response.status_code == 200
        assert response.json()["data"] == []

@pytest.mark.asyncio
async def test_get_task_status_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_task_status.side_effect = Exception("Task Error")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/tasks/upid")
        assert response.status_code == 500
        assert "Task Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_templates_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_templates.side_effect = Exception("Template Error")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/proxmox/templates")
        assert response.status_code == 500
        assert "Template Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_download_template_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.download_template.return_value = "UPID:download"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/download-template", json={
                "storage": "local", "url": "http://url", "filename": "file"
            })
        assert response.status_code == 200
        assert response.json()["data"] == "UPID:download"

@pytest.mark.asyncio
async def test_delete_template_endpoint_success():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.delete_template.return_value = "UPID:delete"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.delete("/proxmox/delete-template/local/vztmpl/file")
        assert response.status_code == 200
        assert response.json()["data"] == "UPID:delete"

@pytest.mark.asyncio
async def test_download_template_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.download_template.side_effect = Exception("Download Error")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/proxmox/download-template", json={
                "storage": "local", "url": "http://url", "filename": "file"
            })
        assert response.status_code == 500
        assert "Download Error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_template_endpoint_error():
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.delete_template.side_effect = Exception("Delete Error")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.delete("/proxmox/delete-template/local/vztmpl/file")
        assert response.status_code == 500
        assert "Delete Error" in response.json()["detail"]
