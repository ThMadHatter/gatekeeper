from proxmoxer import ProxmoxAPI
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class ProxmoxService:
    def __init__(self):
        self.proxmox = ProxmoxAPI(
            settings.PROXMOX_HOST,
            user=settings.PROXMOX_USER,
            token_name=settings.PROXMOX_TOKEN_NAME,
            token_value=settings.PROXMOX_TOKEN_VALUE,
            verify_ssl=False # Often needed for Proxmox self-signed certs, can be made configurable
        )

    def create_lxc(self, vmid: int, ostemplate: str, hostname: str, **kwargs):
        logger.info(f"Creating LXC with VMID: {vmid}, Hostname: {hostname}")
        # Implementation details for Proxmox LXC creation
        # Using the Proxmoxer API
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).lxc.create(
                vmid=vmid,
                ostemplate=ostemplate,
                hostname=hostname,
                **kwargs
            )
            return result
        except Exception as e:
            logger.error(f"Failed to create LXC: {e}")
            raise

    def execute_command(self, vmid: int, command: str):
        logger.info(f"Executing command on VMID {vmid}: {command}")
        try:
            # Proxmox lxc execute endpoint
            result = self.proxmox.nodes(settings.PROXMOX_NODE).lxc(vmid).exec.post(command=command)
            return result
        except Exception as e:
            logger.error(f"Failed to execute command on VMID {vmid}: {e}")
            raise
