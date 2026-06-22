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

async def wait_for_task(ac, upid, timeout_mins=5):
    print(f"Waiting for task {upid} to complete...")
    for _ in range(timeout_mins * 6): # Polling every 10 seconds
        await asyncio.sleep(10)
        task_resp = await ac.get(f"/proxmox/tasks/{upid}")
        assert task_resp.status_code == 200
        status = task_resp.json()["data"]
        if status["status"] == "stopped":
            if status.get("exitstatus") == "OK":
                return True
            else:
                pytest.fail(f"Proxmox task {upid} failed: {status.get('exitstatus')}")
    pytest.fail(f"Proxmox task {upid} timed out")

@pytest.mark.asyncio
async def test_full_lxc_lifecycle():
    """
    Tests the full lifecycle:
    Download Template -> Create LXC -> Start -> Execute -> Stop -> Delete LXC -> Delete Template
    """

    if RUN_REAL_TESTS:
        test_vmid = int(os.getenv("TEST_VMID", "9999"))
        test_storage = os.getenv("TEST_STORAGE", "local")
        # Template name used for official download (e.g., 'debian-11-standard_11.0-1_amd64.tar.gz')
        test_template_name = os.getenv("TEST_TEMPLATE_NAME", "debian-11-standard_11.0-1_amd64.tar.gz")
        test_hostname = "gatekeeper-full-lifecycle-test"

        additional_params = {}
        if os.getenv("TEST_STORAGE"):
            additional_params["storage"] = os.getenv("TEST_STORAGE")
        if os.getenv("TEST_PASSWORD"):
            additional_params["password"] = os.getenv("TEST_PASSWORD")
        if os.getenv("TEST_NET0"):
            additional_params["net0"] = os.getenv("TEST_NET0")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Ensure Template Exists (Download if missing)
            print(f"\nChecking for template {test_template_name} on {test_storage}...")
            templates_resp = await ac.get(f"/proxmox/templates?storage={test_storage}")
            assert templates_resp.status_code == 200

            template_vol = None
            for t in templates_resp.json()["data"]:
                if test_template_name in t["volid"]:
                    template_vol = t["volid"]
                    break

            if not template_vol:
                print(f"Template {test_template_name} not found. Attempting official download...")
                download_resp = await ac.post("/proxmox/download-official-template", json={
                    "storage": test_storage,
                    "template": test_template_name
                })
                assert download_resp.status_code == 200, f"Download failed: {download_resp.text}"
                await wait_for_task(ac, download_resp.json()["data"])
                template_vol = f"{test_storage}:vztmpl/{test_template_name}"

            print(f"Using template volume: {template_vol}")

            # 2. Create LXC
            print(f"Creating LXC {test_vmid}...")
            response = await ac.post("/proxmox/create-lxc", json={
                "vmid": test_vmid,
                "ostemplate": template_vol,
                "hostname": test_hostname,
                "additional_params": additional_params
            })
            assert response.status_code == 200
            await wait_for_task(ac, response.json()["data"])

            # 3. Start
            print(f"Starting LXC {test_vmid}...")
            await ac.post(f"/proxmox/start-lxc/{test_vmid}")

            # Wait for running status
            running = False
            for _ in range(12):
                await asyncio.sleep(5)
                status_resp = await ac.get(f"/proxmox/status-lxc/{test_vmid}")
                if status_resp.status_code == 200 and status_resp.json()["data"]["status"] == "running":
                    running = True
                    break
            assert running, f"LXC failed to start. Status: {status_resp.text}"

            # 4. Execute
            print(f"Executing command in LXC {test_vmid}...")
            response = await ac.post("/proxmox/execute", json={"vmid": test_vmid, "command": "uptime"})
            assert response.status_code == 200

            # 5. Stop
            print(f"Stopping LXC {test_vmid}...")
            await ac.post(f"/proxmox/stop-lxc/{test_vmid}")
            await asyncio.sleep(5)

            # 6. Delete LXC
            print(f"Deleting LXC {test_vmid}...")
            await ac.delete(f"/proxmox/delete-lxc/{test_vmid}")

    else:
        # Mocked version
        with patch("app.routers.proxmox.ProxmoxService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.list_templates.return_value = [{"volid": "local:vztmpl/debian-11.tar.gz"}]
            mock_instance.get_task_status.return_value = {"status": "stopped", "exitstatus": "OK"}
            mock_instance.create_lxc.return_value = "UPID:create"
            mock_instance.start_lxc.return_value = "UPID:start"
            mock_instance.get_lxc_status.return_value = {"status": "running"}
            mock_instance.execute_command.return_value = "UPID:exec"
            mock_instance.stop_lxc.return_value = "UPID:stop"
            mock_instance.delete_lxc.return_value = "UPID:delete"

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                await ac.get("/proxmox/templates?storage=local")
                await ac.post("/proxmox/create-lxc", json={"vmid": 100, "ostemplate": "t", "hostname": "h"})
                await ac.post("/proxmox/start-lxc/100")
                await ac.post("/proxmox/execute", json={"vmid": 100, "command": "uptime"})
                await ac.post("/proxmox/stop-lxc/100")
                await ac.delete("/proxmox/delete-lxc/100")
