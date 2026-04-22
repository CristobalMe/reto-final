from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mysql_host: str = Field(default="127.0.0.1", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3307, alias="MYSQL_PORT")
    mysql_user: str = Field(default="root", alias="MYSQL_USER")
    mysql_password: str = Field(default="root", alias="MYSQL_ROOT_PASSWORD")
    mysql_database: str = Field(default="talos_tecmty", alias="MYSQL_DATABASE")

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="CORS_ORIGINS",
    )

    @property
    def mysql_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
