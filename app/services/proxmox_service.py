from proxmoxer import ProxmoxAPI
from app.config import settings
import logging
import urllib3
import io
import requests
import os
import tempfile
import json
import subprocess
import urllib.parse

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

        # Volume could be 'vztmpl/file.tar.gz' or 'local:vztmpl/file.tar.gz'
        # Proxmox API needs it to be URL encoded in the path
        encoded_volume = urllib.parse.quote(volume, safe="")

        host = settings.PROXMOX_HOST
        if not host.startswith("http"):
            host = f"https://{host}:8006"

        delete_url = (
            f"{host}/api2/json/nodes/{settings.PROXMOX_NODE}/"
            f"storage/{storage}/content/{encoded_volume}"
        )

        headers = {
            "Authorization": (
                f"PVEAPIToken={settings.PROXMOX_USER}!"
                f"{settings.PROXMOX_TOKEN_NAME}={settings.PROXMOX_TOKEN_VALUE}"
            )
        }

        try:
            with requests.Session() as session:
                session.trust_env = False
                response = session.delete(
                    delete_url,
                    headers=headers,
                    verify=False,
                    timeout=120,
                )

            if response.status_code == 404:
                logger.info(f"Template {volume} not found on {storage}, skipping deletion.")
                return {"message": "Not found"}

            response.raise_for_status()
            return response.json().get("data")
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

    def upload_template_from_path_with_curl(self, storage: str, filename: str, file_path: str):
        # Build the direct Proxmox API URL for upload
        host = settings.PROXMOX_HOST
        if not host.startswith("http"):
            host = f"https://{host}:8006"

        upload_url = f"{host}/api2/json/nodes/{settings.PROXMOX_NODE}/storage/{storage}/upload"

        auth_header = (
            f"Authorization: PVEAPIToken={settings.PROXMOX_USER}!"
            f"{settings.PROXMOX_TOKEN_NAME}={settings.PROXMOX_TOKEN_VALUE}"
        )

        cmd = [
            "curl", "-k", "--fail-with-body", upload_url,
            "-H", auth_header,
            "-F", "content=vztmpl",
            "-F", f"filename=@{file_path};filename={filename};type=application/octet-stream",
        ]

        # Redacted command for logging
        safe_cmd = [c if "PVEAPIToken" not in c else "-H Authorization: PVEAPIToken=<redacted>" for c in cmd]
        logger.info(f"Uploading template using curl fallback: {' '.join(safe_cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            if result.returncode != 0:
                logger.error(f"curl upload failed: status={result.returncode}, stderr={result.stderr}, stdout={result.stdout}")
                raise RuntimeError(f"curl upload failed: {result.stderr or result.stdout}")

            return json.loads(result.stdout)["data"]
        except Exception as e:
            logger.error(f"Failed during curl fallback upload: {e}")
            raise

    def upload_template_from_path(self, storage: str, filename: str, file_path: str):
        file_size = os.path.getsize(file_path)
        logger.info(f"Uploading template {filename} to storage {storage} from {file_path} ({file_size} bytes)")

        # Build the direct Proxmox API URL for upload
        host = settings.PROXMOX_HOST
        if not host.startswith("http"):
            host = f"https://{host}:8006"

        upload_url = f"{host}/api2/json/nodes/{settings.PROXMOX_NODE}/storage/{storage}/upload"
        logger.debug(f"Target Upload URL: {upload_url}")

        headers = {
            "Authorization": (
                f"PVEAPIToken={settings.PROXMOX_USER}!"
                f"{settings.PROXMOX_TOKEN_NAME}={settings.PROXMOX_TOKEN_VALUE}"
            ),
            "Accept": "*/*",
            "Connection": "close",
        }

        try:
            with requests.Session() as session:
                session.trust_env = False
                with open(file_path, "rb") as f:
                    # 'filename' field is mandatory for Proxmox upload
                    files = {"filename": (filename, f, "application/octet-stream")}
                    data = {"content": "vztmpl"}

                    response = session.post(
                        upload_url,
                        headers=headers,
                        data=data,
                        files=files,
                        verify=False,
                        timeout=600,
                    )

            logger.info(f"Proxmox upload response status for {filename}: {response.status_code}")

            if not response.ok:
                logger.error(f"Proxmox upload failed for {filename}: status={response.status_code}, body={response.text}")

            response.raise_for_status()
            return response.json()["data"]

        except Exception as e:
            # Fallback to curl if requests fails with a connection abortion
            if "RemoteDisconnected" in str(e) or "Connection aborted" in str(e):
                logger.warning(f"Requests upload failed with connection error, attempting curl fallback: {e}")
                return self.upload_template_from_path_with_curl(storage, filename, file_path)

            logger.error(f"Failed to upload template {filename} from {file_path}: {e}")
            raise

    def upload_template(self, storage: str, filename: str, file_content: bytes):
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp:
                tmp_path = tmp.name
                tmp.write(file_content)

            return self.upload_template_from_path(
                storage=storage,
                filename=filename,
                file_path=tmp_path,
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
