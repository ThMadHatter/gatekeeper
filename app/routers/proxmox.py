from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.proxmox_service import ProxmoxService
from typing import Dict, Any, Optional

router = APIRouter(prefix="/proxmox", tags=["proxmox"])

class LXCCreateRequest(BaseModel):
    vmid: int
    ostemplate: str
    hostname: str
    additional_params: Optional[Dict[str, Any]] = None

class ExecuteRequest(BaseModel):
    vmid: int
    command: str

class TemplateDownloadRequest(BaseModel):
    storage: str
    url: str
    filename: str

def get_proxmox_service():
    return ProxmoxService()

@router.post("/create-lxc")
async def create_lxc(request: LXCCreateRequest, service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        params = request.additional_params or {}
        result = service.create_lxc(
            vmid=request.vmid,
            ostemplate=request.ostemplate,
            hostname=request.hostname,
            **params
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download-template")
async def download_template(request: TemplateDownloadRequest, service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.download_template(
            storage=request.storage,
            url=request.url,
            filename=request.filename
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-template/{storage}/{volume:path}")
async def delete_template(storage: str, volume: str, service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.delete_template(storage=storage, volume=volume)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{upid}")
async def get_task_status(upid: str, service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.get_task_status(upid=upid)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def list_templates(storage: str = "local", service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.list_templates(storage=storage)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-lxc/{vmid}")
async def start_lxc(vmid: int, service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.start_lxc(vmid=vmid)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-lxc/{vmid}")
async def stop_lxc(vmid: int, service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.stop_lxc(vmid=vmid)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status-lxc/{vmid}")
async def get_lxc_status(vmid: int, service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.get_lxc_status(vmid=vmid)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list-lxcs")
async def list_lxcs(service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.list_lxcs()
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-lxc/{vmid}")
async def delete_lxc(vmid: int, service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.delete_lxc(vmid=vmid)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute(request: ExecuteRequest, service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.execute_command(vmid=request.vmid, command=request.command)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
