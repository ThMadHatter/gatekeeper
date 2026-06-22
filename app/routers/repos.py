from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.repo_service import RepoService
from typing import List

router = APIRouter(prefix="/repos", tags=["template repositories"])

class RepoAddRequest(BaseModel):
    name: str
    url: str

def get_repo_service():
    return RepoService()

@router.get("/")
async def list_repos(service: RepoService = Depends(get_repo_service)):
    return {"status": "success", "data": service.list_repos()}

@router.post("/")
async def add_repo(request: RepoAddRequest, service: RepoService = Depends(get_repo_service)):
    try:
        result = await service.add_repo(request.name, request.url)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{name}")
async def remove_repo(name: str, service: RepoService = Depends(get_repo_service)):
    try:
        service.remove_repo(name)
        return {"status": "success", "message": f"Repository '{name}' removed"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{name}")
async def get_repo(name: str, service: RepoService = Depends(get_repo_service)):
    try:
        result = service.get_repo_by_name(name)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
