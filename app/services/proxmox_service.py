from proxmoxer import ProxmoxAPI
from app.config import settings
import logging
import urllib3

# Suppress InsecureRequestWarning for self-signed Proxmox certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class ProxmoxService:
    def __init__(self):
        self.proxmox = ProxmoxAPI(
            settings.PROXMOX_HOST,
            user=settings.PROXMOX_USER,
            token_name=settings.PROXMOX_TOKEN_NAME,
            token_value=settings.PROXMOX_TOKEN_VALUE,
            verify_ssl=False, # Often needed for Proxmox self-signed certs
            timeout=600       # 10 minutes timeout for uploads and slow operations
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
            if "501 Not Implemented" in str(e):
                logger.error(f"Failed to execute command on VMID {vmid}: {e}. Ensure the container is running.")
            else:
                logger.error(f"Failed to execute command on VMID {vmid}: {e}")
            raise

    def list_lxcs(self):
        logger.info("Listing all LXCs")
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).lxc.get()
            return result
        except Exception as e:
            logger.error(f"Failed to list LXCs: {e}")
            raise

    def delete_lxc(self, vmid: int):
        logger.info(f"Deleting LXC with VMID: {vmid}")
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).lxc(vmid).delete()
            return result
        except Exception as e:
            logger.error(f"Failed to delete LXC {vmid}: {e}")
            raise

    def start_lxc(self, vmid: int):
        logger.info(f"Starting LXC with VMID: {vmid}")
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).lxc(vmid).status.start.post()
            return result
        except Exception as e:
            logger.error(f"Failed to start LXC {vmid}: {e}")
            raise

    def stop_lxc(self, vmid: int):
        logger.info(f"Stopping LXC with VMID: {vmid}")
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).lxc(vmid).status.stop.post()
            return result
        except Exception as e:
            logger.error(f"Failed to stop LXC {vmid}: {e}")
            raise

    def get_lxc_status(self, vmid: int):
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).lxc(vmid).status.current.get()
            return result
        except Exception as e:
            logger.error(f"Failed to get status for LXC {vmid}: {e}")
            raise

    def get_task_status(self, upid: str):
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).tasks(upid).status.get()
            return result
        except Exception as e:
            logger.error(f"Failed to get task status for {upid}: {e}")
            raise

    def list_templates(self, storage: str = "local"):
        logger.info(f"Listing templates on storage: {storage}")
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).storage(storage).content.get(content="vztmpl")
            return result
        except Exception as e:
            logger.error(f"Failed to list templates on {storage}: {e}")
            raise

    def download_template(self, storage: str, url: str, filename: str):
        logger.info(f"Downloading template from {url} to {storage}/{filename}")
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).storage(storage).download_url.post(
                url=url,
                filename=filename,
                content="vztmpl"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to initiate template download: {e}")
            raise

    def delete_template(self, storage: str, volume: str):
        logger.info(f"Deleting template {volume} from storage {storage}")
        try:
            # Volume is usually something like 'vztmpl/debian-11-standard_11.0-1_amd64.tar.gz'
            result = self.proxmox.nodes(settings.PROXMOX_NODE).storage(storage).content(volume).delete()
            return result
        except Exception as e:
            logger.error(f"Failed to delete template {volume} from {storage}: {e}")
            raise

    def get_available_templates(self):
        logger.info("Getting available official templates")
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).aplinfo.get()
            return result
        except Exception as e:
            logger.error(f"Failed to get available templates: {e}")
            raise

    def download_official_template(self, storage: str, template: str):
        logger.info(f"Downloading official template {template} to storage {storage}")
        try:
            result = self.proxmox.nodes(settings.PROXMOX_NODE).vztmpl.post(
                storage=storage,
                template=template
            )
            return result
        except Exception as e:
            logger.error(f"Failed to download official template: {e}")
            raise

    def upload_template(self, storage: str, filename: str, file_content: bytes):
        logger.info(f"Uploading template {filename} to storage {storage} ({len(file_content)} bytes)")
        try:
            # Using the Proxmox upload endpoint
            # Proxmoxer passes extra kwargs to the underlying requests library.
            # To ensure a proper multipart/form-data upload, we use the 'files' parameter.
            result = self.proxmox.nodes(settings.PROXMOX_NODE).storage(storage).upload.post(
                content="vztmpl",
                files={
                    'filename': (filename, file_content)
                }
            )
            return result
        except Exception as e:
            logger.error(f"Failed to upload template {filename}: {e}")
            raise
