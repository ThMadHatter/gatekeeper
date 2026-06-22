import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch, MagicMock
from app.routers.proxmox import get_proxmox_service

# Toggle for real tests vs mocked tests
RUN_REAL_TESTS = os.getenv("RUN_REAL_TESTS", "false").lower() == "true"

@pytest.mark.asyncio
async def test_full_lxc_lifecycle():
    """
    Tests the full lifecycle of an LXC: List -> Create -> Execute -> Delete -> List
    Can run against a real Proxmox server if RUN_REAL_TESTS=true and credentials are provided.
    Otherwise, runs against mocks.
    """

    if RUN_REAL_TESTS:
        # For real tests, we use the actual service as configured in .secrets or env
        test_vmid = int(os.getenv("TEST_VMID", "9999"))
        test_template = os.getenv("TEST_TEMPLATE", "local:vztmpl/debian-11-standard_11.0-1_amd64.tar.gz")
        test_hostname = "gatekeeper-integration-test"

        # Additional params often needed for a successful creation on real Proxmox
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

            # 3. List (After creation)
            response = await ac.get("/proxmox/list-lxcs")
            assert response.status_code == 200

            # 4. Execute
            response = await ac.post("/proxmox/execute", json={
                "vmid": test_vmid,
                "command": "uptime"
            })
            assert response.status_code == 200

            # 5. Delete
            response = await ac.delete(f"/proxmox/delete-lxc/{test_vmid}")
            assert response.status_code == 200

    else:
        # Mocked version
        with patch("app.routers.proxmox.ProxmoxService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.list_lxcs.side_effect = [[], [{"vmid": 100}], []]
            mock_instance.create_lxc.return_value = "UPID:pve:00001:create"
            mock_instance.execute_command.return_value = "UPID:pve:00002:exec"
            mock_instance.delete_lxc.return_value = "UPID:pve:00003:delete"

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                # 1. List
                response = await ac.get("/proxmox/list-lxcs")
                assert response.status_code == 200
                assert response.json()["data"] == []

                # 2. Create
                response = await ac.post("/proxmox/create-lxc", json={
                    "vmid": 100,
                    "ostemplate": "template",
                    "hostname": "test"
                })
                assert response.status_code == 200

                # 3. List
                response = await ac.get("/proxmox/list-lxcs")
                assert response.json()["data"] == [{"vmid": 100}]

                # 4. Execute
                response = await ac.post("/proxmox/execute", json={
                    "vmid": 100,
                    "command": "ls"
                })
                assert response.status_code == 200

                # 5. Delete
                response = await ac.delete("/proxmox/delete-lxc/100")
                assert response.status_code == 200
