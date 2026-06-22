import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch

@pytest.mark.asyncio
async def test_full_lxc_lifecycle_mocked():
    """
    Tests the full lifecycle of an LXC: List -> Create -> Execute -> Delete -> List
    Using mocks to avoid needing a real Proxmox server.
    """
    with patch("app.routers.proxmox.ProxmoxService") as MockService:
        mock_instance = MockService.return_value

        # 1. Setup mocks
        mock_instance.list_lxcs.side_effect = [[], [{"vmid": 100}]] # Empty first, then with one
        mock_instance.create_lxc.return_value = "UPID:pve:00001:create"
        mock_instance.execute_command.return_value = "UPID:pve:00002:exec"
        mock_instance.delete_lxc.return_value = "UPID:pve:00003:delete"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 2. List LXCs (Initial)
            response = await ac.get("/proxmox/list-lxcs")
            assert response.status_code == 200
            assert response.json()["data"] == []

            # 3. Create LXC
            vmid = 100
            response = await ac.post("/proxmox/create-lxc", json={
                "vmid": vmid,
                "ostemplate": "local:vztmpl/debian-11.tar.gz",
                "hostname": "test-integration"
            })
            assert response.status_code == 200
            assert "UPID" in response.json()["data"]

            # 4. List LXCs (After creation)
            response = await ac.get("/proxmox/list-lxcs")
            assert response.status_code == 200
            assert any(lxc["vmid"] == vmid for lxc in response.json()["data"])

            # 5. Execute Command
            response = await ac.post("/proxmox/execute", json={
                "vmid": vmid,
                "command": "apt-get update"
            })
            assert response.status_code == 200
            assert "UPID" in response.json()["data"]

            # 6. Delete LXC
            response = await ac.delete(f"/proxmox/delete-lxc/{vmid}")
            assert response.status_code == 200
            assert "UPID" in response.json()["data"]

            # Reset mock for final list check if needed,
            # or just rely on side_effect if we planned it
            mock_instance.list_lxcs.side_effect = [[]]
            response = await ac.get("/proxmox/list-lxcs")
            assert response.status_code == 200
            assert response.json()["data"] == []
