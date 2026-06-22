import pytest
import os
import json
from app.services.repo_service import RepoService, REPO_FILE
from unittest.mock import patch, AsyncMock

@pytest.fixture
def repo_service():
    if os.path.exists(REPO_FILE):
        os.remove(REPO_FILE)
    return RepoService()

def test_list_repos_default(repo_service):
    repos = repo_service.list_repos()
    assert len(repos) == 2
    assert repos[0]["name"] == "Proxmox Official"

def test_repo_service_ensure_dir(monkeypatch):
    # Test _ensure_repo_file when data dir doesn't exist
    with patch("os.path.exists", return_value=False):
        with patch("os.makedirs") as mock_mkdir:
            with patch("builtins.open"):
                with patch("json.dump"):
                    RepoService()
                    mock_mkdir.assert_called_with("data")

@pytest.mark.asyncio
async def test_add_repo_success(repo_service):
    with patch("httpx.AsyncClient.head", return_value=AsyncMock(status_code=200)):
        new_repo = await repo_service.add_repo("New", "http://valid.com")
        assert new_repo["name"] == "New"
        assert len(repo_service.list_repos()) == 3

@pytest.mark.asyncio
async def test_add_repo_invalid_url(repo_service):
    with patch("httpx.AsyncClient.head", return_value=AsyncMock(status_code=404)):
        with pytest.raises(Exception) as exc:
            await repo_service.add_repo("Bad", "http://invalid.com")
        assert "URL returned status 404" in str(exc.value)

@pytest.mark.asyncio
async def test_add_repo_duplicate(repo_service):
    with patch("httpx.AsyncClient.head", return_value=AsyncMock(status_code=200)):
        await repo_service.add_repo("Dup", "http://valid.com")
        with pytest.raises(Exception) as exc:
            await repo_service.add_repo("Dup", "http://other.com")
        assert "already exists" in str(exc.value)

def test_remove_repo_success(repo_service):
    repo_service.remove_repo("Proxmox Official")
    assert len(repo_service.list_repos()) == 1

def test_remove_repo_not_found(repo_service):
    with pytest.raises(Exception) as exc:
        repo_service.remove_repo("Missing")
    assert "not found" in str(exc.value)

def test_list_repos_error(repo_service):
    with patch("builtins.open", side_effect=Exception("Read error")):
        assert repo_service.list_repos() == []

@pytest.mark.asyncio
async def test_add_repo_write_error(repo_service):
    with patch("httpx.AsyncClient.head", return_value=AsyncMock(status_code=200)):
        with patch("json.dump", side_effect=Exception("Write error")):
            with pytest.raises(Exception) as exc:
                await repo_service.add_repo("Fail", "http://v.com")
            assert "Failed to save" in str(exc.value)

def test_remove_repo_write_error(repo_service):
    with patch("json.dump", side_effect=Exception("Write error")):
        with pytest.raises(Exception) as exc:
            repo_service.remove_repo("Proxmox Official")
        assert "Failed to update" in str(exc.value)
