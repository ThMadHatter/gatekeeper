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
