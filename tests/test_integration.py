import pytest
import os
import asyncio
import logging
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch

# Toggle for real tests vs mocked tests
RUN_REAL_TESTS = os.getenv("RUN_REAL_TESTS", "false").lower() == "true"
logger = logging.getLogger(__name__)

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
            print(f"\nCreating LXC {test_vmid} using template {test_template}...")
            response = await ac.post("/proxmox/create-lxc", json={
                "vmid": test_vmid,
                "ostemplate": test_template,
                "hostname": test_hostname,
                "additional_params": additional_params
            })
            assert response.status_code == 200, f"Create request failed: {response.text}"
            upid = response.json()["data"]

            # Wait for creation task to finish
            print(f"Waiting for creation task {upid} to complete...")
            task_success = False
            for _ in range(30): # Wait up to 5 minutes
                await asyncio.sleep(10)
                task_resp = await ac.get(f"/proxmox/tasks/{upid}")
                assert task_resp.status_code == 200
                status = task_resp.json()["data"]
                if status["status"] == "stopped": # Proxmox tasks are 'stopped' when finished
                    if status.get("exitstatus") == "OK":
                        task_success = True
                        break
                    else:
                        pytest.fail(f"LXC Creation task failed: {status.get('exitstatus')}")
            assert task_success, "LXC creation task timed out"

            # 3. Start
            print(f"Starting LXC {test_vmid}...")
            response = await ac.post(f"/proxmox/start-lxc/{test_vmid}")
            assert response.status_code == 200

            # 4. Wait for running status
            print(f"Waiting for LXC {test_vmid} to reach 'running' status...")
            running = False
            for _ in range(12): # Wait up to 60 seconds
                await asyncio.sleep(5)
                status_resp = await ac.get(f"/proxmox/status-lxc/{test_vmid}")
                if status_resp.status_code == 200 and status_resp.json()["data"]["status"] == "running":
                    running = True
                    break
            assert running, f"LXC {test_vmid} failed to start within timeout. Current status: {status_resp.text}"

            # 5. Execute
            print(f"Executing command in LXC {test_vmid}...")
            response = await ac.post("/proxmox/execute", json={
                "vmid": test_vmid,
                "command": "uptime"
            })
            assert response.status_code == 200, f"Execute failed: {response.text}"

            # 6. Stop
            print(f"Stopping LXC {test_vmid}...")
            response = await ac.post(f"/proxmox/stop-lxc/{test_vmid}")
            assert response.status_code == 200
            await asyncio.sleep(5)

            # 7. Delete
            print(f"Deleting LXC {test_vmid}...")
            response = await ac.delete(f"/proxmox/delete-lxc/{test_vmid}")
            assert response.status_code == 200

    else:
        # Mocked version
        with patch("app.routers.proxmox.ProxmoxService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.list_lxcs.side_effect = [[], [{"vmid": 100}], []]
            mock_instance.create_lxc.return_value = "UPID:pve:00001:create"
            mock_instance.get_task_status.return_value = {"status": "stopped", "exitstatus": "OK"}
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

                # 3. Task Status
                response = await ac.get("/proxmox/tasks/UPID:pve:00001:create")
                assert response.status_code == 200

                # 4. Start
                response = await ac.post("/proxmox/start-lxc/100")
                assert response.status_code == 200

                # 5. Execute
                response = await ac.post("/proxmox/execute", json={"vmid": 100, "command": "uptime"})
                assert response.status_code == 200

                # 6. Stop
                response = await ac.post("/proxmox/stop-lxc/100")
                assert response.status_code == 200

                # 7. Delete
                response = await ac.delete("/proxmox/delete-lxc/100")
                assert response.status_code == 200
