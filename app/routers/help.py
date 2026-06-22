from fastapi import APIRouter

router = APIRouter(prefix="/help", tags=["help"])

@router.get("/")
async def get_help():
    return {
        "message": "Welcome to Proxmox Gatekeeper API",
        "usage": "Use these endpoints to manage your Proxmox LXC infrastructure.",
        "endpoints": {
            "LXC Management": {
                "GET /proxmox/list-lxcs": "List all LXC containers on the Proxmox node.",
                "POST /proxmox/create-lxc": "Create a new LXC container. Requires vmid, ostemplate, and hostname.",
                "POST /proxmox/start-lxc/{vmid}": "Start a specific LXC container.",
                "POST /proxmox/stop-lxc/{vmid}": "Stop a specific LXC container.",
                "GET /proxmox/status-lxc/{vmid}": "Get current status (running, stopped) of a container.",
                "POST /proxmox/execute": "Execute a shell command inside a running LXC. Requires vmid and command.",
                "DELETE /proxmox/delete-lxc/{vmid}": "Delete an LXC container."
            },
            "Template Management": {
                "GET /proxmox/templates": "List templates currently stored on Proxmox storage.",
                "GET /proxmox/available-templates": "List official Proxmox templates available for download.",
                "POST /proxmox/download-official-template": "Download an official template to Proxmox storage.",
                "POST /proxmox/download-template": "Download a template from a custom URL.",
                "POST /proxmox/upload-template": "Upload a local template file to Proxmox storage (Multipart Form).",
                "DELETE /proxmox/delete-template/{storage}/{volume}": "Delete a template file from storage."
            },
            "Repository Management": {
                "GET /repos": "List registered online template repositories.",
                "POST /repos": "Register a new template repository URL (validates URL on add).",
                "DELETE /repos/{name}": "Remove a registered repository."
            },
            "System": {
                "GET /": "Health check endpoint.",
                "GET /proxmox/tasks/{upid}": "Check the status of an asynchronous Proxmox task.",
                "GET /help": "Show this help guide."
            }
        },
        "examples": {
            "create_lxc": {
                "method": "POST",
                "url": "/proxmox/create-lxc",
                "body": {
                    "vmid": 100,
                    "ostemplate": "local:vztmpl/debian-11.tar.gz",
                    "hostname": "my-container",
                    "additional_params": {"storage": "local-lvm", "password": "secure"}
                }
            }
        }
    }
