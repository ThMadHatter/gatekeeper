import pytest
import os
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch, MagicMock
from app.routers.proxmox import get_proxmox_service

# Toggle for real tests vs mocked tests
RUN_REAL_TESTS = os.getenv("RUN_REAL_TESTS", "false").lower() == "true"

@pytest.mark.asyncio
async def test_full_lxc_lifecycle():
    """
    Tests the full lifecycle of an LXC: List -> Create -> Start -> Execute -> Stop -> Delete -> List
    Can run against a real Proxmox server if RUN_REAL_TESTS=true and credentials are provided.
    Otherwise, runs against mocks.
    """

    if RUN_REAL_TESTS:
        test_vmid = int(os.getenv("TEST_VMID", "9999"))
        test_template = os.getenv("TEST_TEMPLATE", "local:vztmpl/debian-11-standard_11.0-1_amd64.tar.gz")
        test_hostname = "gatekeeper-integration-test"

        additional_params = {}
        if os.getenv("TEST_STORAGE"):
            additional_params["storage"] = os.getenv("TEST_STORAGE")
        if os.getenv("TEST_PASSWORD"):
            additional_params["password"] = os.getenv("TEST_PASSWORD")
        if os.getenv("TEST_NET0"):
            additional_params["net0"] = os.getenv("TEST_NET0")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. List (Initial)
            response = await ac.get("/proxmox/list-lxcs")
            assert response.status_code == 200

            # 2. Create
            response = await ac.post("/proxmox/create-lxc", json={
                "vmid": test_vmid,
                "ostemplate": test_template,
                "hostname": test_hostname,
                "additional_params": additional_params
            })
            assert response.status_code == 200

            # Wait for creation task to finish (simple sleep or poll task status)
            await asyncio.sleep(10)

            # 3. Start
            response = await ac.post(f"/proxmox/start-lxc/{test_vmid}")
            assert response.status_code == 200

            # 4. Wait for running status
            running = False
            for _ in range(12): # Wait up to 60 seconds
                await asyncio.sleep(5)
                status_resp = await ac.get(f"/proxmox/status-lxc/{test_vmid}")
                if status_resp.status_code == 200 and status_resp.json()["data"]["status"] == "running":
                    running = True
                    break
            assert running, "LXC failed to start within timeout"

            # 5. Execute
            response = await ac.post("/proxmox/execute", json={
                "vmid": test_vmid,
                "command": "uptime"
            })
            assert response.status_code == 200

            # 6. Stop
            response = await ac.post(f"/proxmox/stop-lxc/{test_vmid}")
            assert response.status_code == 200
            await asyncio.sleep(5)

            # 7. Delete
            response = await ac.delete(f"/proxmox/delete-lxc/{test_vmid}")
            assert response.status_code == 200

    else:
        # Mocked version
        with patch("app.routers.proxmox.ProxmoxService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.list_lxcs.side_effect = [[], [{"vmid": 100}], []]
            mock_instance.create_lxc.return_value = "UPID:pve:00001:create"
            mock_instance.start_lxc.return_value = "UPID:pve:00002:start"
            mock_instance.get_lxc_status.return_value = {"status": "running"}
            mock_instance.execute_command.return_value = "UPID:pve:00003:exec"
            mock_instance.stop_lxc.return_value = "UPID:pve:00004:stop"
            mock_instance.delete_lxc.return_value = "UPID:pve:00005:delete"

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                # 1. List
                response = await ac.get("/proxmox/list-lxcs")
                assert response.status_code == 200

                # 2. Create
                response = await ac.post("/proxmox/create-lxc", json={"vmid": 100, "ostemplate": "t", "hostname": "h"})
                assert response.status_code == 200

                # 3. Start
                response = await ac.post("/proxmox/start-lxc/100")
                assert response.status_code == 200

                # 4. Execute
                response = await ac.post("/proxmox/execute", json={"vmid": 100, "command": "uptime"})
                assert response.status_code == 200

                # 5. Stop
                response = await ac.post("/proxmox/stop-lxc/100")
                assert response.status_code == 200

                # 6. Delete
                response = await ac.delete("/proxmox/delete-lxc/100")
                assert response.status_code == 200
