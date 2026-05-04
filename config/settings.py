from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Centrale configuratie van de applicatie.

    Leest instellingen uit omgevingsvariabelen (via een .env bestand) en
    groepeert configuratie voor externe diensten en applicatiegedrag.

    Bevat o.a.:
    - SharePoint configuratie
    - TOPdesk configuratie
    - API instellingen
    - Logging configuratie
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # SharePoint
    SHAREPOINT_BASE_URL: Optional[str] = None
    SHAREPOINT_CLIENT_ID: Optional[str] = None
    SHAREPOINT_CLIENT_SECRET: Optional[str] = None
    SHAREPOINT_TENANT_ID: Optional[str] = None
    LMS_SITE_ID: Optional[str] = None
    SERVICE_CATALOG_ID: Optional[str] = None
    ICTS_SITE_ID: Optional[str] = None

    # TOPdesk
    TOPDESK_BASE_URL: Optional[str] = None
    TOPDESK_USER: Optional[str] = None
    TOPDESK_SECRET: Optional[str] = None
    TOPDESK_ENABLED: bool = False

    # Server
    API_BASE_URL: str = "http://localhost:8000"

    LOG_LEVEL: str = "INFO"


settings = Settings()
