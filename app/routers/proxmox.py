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

@router.post("/execute")
async def execute(request: ExecuteRequest, service: ProxmoxService = Depends(get_proxmox_service)):
    try:
        result = service.execute_command(vmid=request.vmid, command=request.command)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
