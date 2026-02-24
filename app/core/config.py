from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    ROOT_CS_PATH: str = "data/cs-files"
    METADATA_CSV_PATH: str = "data/metadata.csv"
    LLM_MODEL: str = "gpt-4o"

    class Config:
        env_file = ".env"


settings = Settings()
CS_ROOT = Path(settings.ROOT_CS_PATH)
METADATA_PATH = Path(settings.METADATA_CSV_PATH)
