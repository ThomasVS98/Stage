from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    #SharePoint
    SHAREPOINT_BASE_URL: str
    SHAREPOINT_CLIENT_ID: str
    SHAREPOINT_CLIENT_SECRET: str 
    SHAREPOINT_TENANT_ID: str
    LMS_SITE_ID: str
    SERVICE_CATALOG_ID: str
    ICTS_SITE_ID: str

    #TOPdesk
    TOPDESK_BASE_URL: str
    TOPDESK_USER: str
    TOPDESK_SECRET: str
    TOPDESK_ENABLED: bool

    #Server
    API_BASE_URL: str
    #API_BASE_URL: str

    LOG_LEVEL: str

    class Config:
        env_file = ".env"

settings = Settings()

