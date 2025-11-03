from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Game Rule API"
    debug: bool = False


settings = Settings()
