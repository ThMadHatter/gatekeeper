from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import logging

class Settings(BaseSettings):
    PROXMOX_HOST: str
    PROXMOX_USER: str
    PROXMOX_TOKEN_NAME: str
    PROXMOX_TOKEN_VALUE: str
    PROXMOX_NODE: str
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="/var/log/gatekeeper.log")

    model_config = SettingsConfigDict(env_file=".secrets", env_file_encoding="utf-8", extra="ignore")

try:
    settings = Settings()
except Exception as e:
    logging.error(f"Configuration validation failed: {e}")
    raise SystemExit(f"Error: Missing or invalid configuration variables. Check your .secrets file. Details: {e}")
