import pytest
import os
import asyncio
import logging
import httpx
import urllib.parse
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
            exit_status = status.get("exitstatus", "")
            # Task is successful if exitstatus is "OK" or contains "OK" with warnings
            if "OK" in exit_status:
                return True
            else:
                pytest.fail(f"Proxmox task {upid} failed: {exit_status}")
    pytest.fail(f"Proxmox task {upid} timed out")

@pytest.mark.asyncio
async def test_full_lxc_lifecycle():
    """
    Tests the full lifecycle:
    Download Template locally -> Upload to Proxmox -> Create LXC -> Start -> Execute -> Stop -> Delete LXC -> Delete Template
    """

    if RUN_REAL_TESTS:
        test_vmid = int(os.getenv("TEST_VMID", "9999"))
        test_template_storage = os.getenv("TEST_TEMPLATE_STORAGE", "local")
        test_rootfs_storage = os.getenv("TEST_ROOTFS_STORAGE", os.getenv("TEST_STORAGE", "local-lvm"))
        # Using a small template (Alpine Linux) for faster upload during tests.
        template_url_raw = os.getenv("TEST_TEMPLATE_URL", "https://mirror.accum.se/mirror/linuxcontainers.org/images/alpine/3.18/amd64/default/20230607_13:00/rootfs.tar.xz")
        template_filename = os.getenv("TEST_TEMPLATE_NAME", "alpine-3.18-test.tar.xz")

        # If URL is a directory or base URL, append the filename intelligently
        if template_filename:
            # Ensure base URL has a trailing slash for urljoin to work correctly
            base_url = template_url_raw if template_url_raw.endswith("/") else f"{template_url_raw}/"
            template_url = urllib.parse.urljoin(base_url, template_filename)
        else:
            template_url = template_url_raw

        test_hostname = "gatekeeper-upload-test"

        additional_params = {}
        if os.getenv("TEST_STORAGE"):
            additional_params["storage"] = os.getenv("TEST_STORAGE")
        if os.getenv("TEST_PASSWORD"):
            additional_params["password"] = os.getenv("TEST_PASSWORD")
        if os.getenv("TEST_NET0"):
            additional_params["net0"] = os.getenv("TEST_NET0")
        if os.getenv("TEST_FEATURES"):
            additional_params["features"] = os.getenv("TEST_FEATURES")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=600) as ac:
            # 0. Cleanup any existing template for idempotency
            print(f"Pre-cleanup of existing template {template_filename} on {test_template_storage}...")
            volume_id = f"{test_template_storage}:vztmpl/{template_filename}"
            try:
                await ac.delete(f"/proxmox/delete-template/{test_template_storage}/{volume_id}")
            except Exception as e:
                print(f"Warning: pre-cleanup failed: {e}")

            # 1. Download Template Locally
            print(f"\nDownloading template locally from {template_url}...")
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(template_url)
                resp.raise_for_status()
                template_content = resp.content
                content_type = resp.headers.get('content-type', '')
                print(f"Downloaded {len(template_content)} bytes (Content-Type: {content_type})")

                if "text/html" in content_type:
                    snippet = template_content[:200].decode(errors='ignore')
                    pytest.fail(f"Downloaded template is HTML, not a binary image. Check your URL: {template_url}\nSnippet: {snippet}")

            # 2. Upload to Proxmox
            print(f"Uploading template to Proxmox storage {test_template_storage} ({len(template_content)} bytes)...")
            files = {'file': (template_filename, template_content)}
            data = {'storage': test_template_storage}
            response = await ac.post("/proxmox/upload-template", data=data, files=files)
            assert response.status_code == 200, f"Upload failed: {response.text}"
            upload_upid = response.json()["data"]
            await wait_for_task(ac, upload_upid)

            template_vol = f"{test_template_storage}:vztmpl/{template_filename}"
            print(f"Using template volume: {template_vol}")

            # 3. Create LXC
            print(f"Creating LXC {test_vmid} on storage {test_rootfs_storage}...")
            additional_params["storage"] = test_rootfs_storage
            response = await ac.post("/proxmox/create-lxc", json={
                "vmid": test_vmid,
                "ostemplate": template_vol,
                "hostname": test_hostname,
                "additional_params": additional_params
            })
            assert response.status_code == 200
            await wait_for_task(ac, response.json()["data"])

            # 4. Start
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

            # 5. Execute
            print(f"Executing command in LXC {test_vmid}...")
            response = await ac.post("/proxmox/execute", json={"vmid": test_vmid, "command": "uptime"})
            assert response.status_code == 200

            # 6. Stop
            print(f"Stopping LXC {test_vmid}...")
            await ac.post(f"/proxmox/stop-lxc/{test_vmid}")
            await asyncio.sleep(5)

            # 7. Delete LXC
            print(f"Deleting LXC {test_vmid}...")
            await ac.delete(f"/proxmox/delete-lxc/{test_vmid}")

            # 8. Delete Template
            print(f"Deleting template {template_vol} from {test_template_storage}...")
            # Use the full volid for deletion consistency
            await ac.delete(f"/proxmox/delete-template/{test_template_storage}/{template_vol}")

    else:
        # Mocked version
        with patch("app.routers.proxmox.ProxmoxService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.upload_template.return_value = "UPID:upload"
            mock_instance.get_task_status.return_value = {"status": "stopped", "exitstatus": "OK"}
            mock_instance.create_lxc.return_value = "UPID:create"
            mock_instance.start_lxc.return_value = "UPID:start"
            mock_instance.get_lxc_status.return_value = {"status": "running"}
            mock_instance.execute_command.return_value = "UPID:exec"
            mock_instance.stop_lxc.return_value = "UPID:stop"
            mock_instance.delete_lxc.return_value = "UPID:delete"
            mock_instance.delete_template.return_value = "UPID:delete_temp"

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                # Mocking file upload
                await ac.post("/proxmox/upload-template", data={"storage": "s"}, files={"file": ("f", b"c")})
                await ac.post("/proxmox/create-lxc", json={"vmid": 100, "ostemplate": "t", "hostname": "h"})
                await ac.post("/proxmox/start-lxc/100")
                await ac.post("/proxmox/execute", json={"vmid": 100, "command": "uptime"})
                await ac.post("/proxmox/stop-lxc/100")
                await ac.delete("/proxmox/delete-lxc/100")
                await ac.delete("/proxmox/delete-template/s/vztmpl/f")
