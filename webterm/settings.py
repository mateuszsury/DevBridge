from pydantic_settings import BaseSettings


class EnvSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DB_PATH: str = "data/webterm.sqlite3"

    # Cookie session
    SESSION_COOKIE: str = "webterm_session"
    SESSION_SECRET: str = "change-me-please-very-secret"

    # Bootstrap admin (utworzony jeśli brak użytkowników)
    BOOTSTRAP_ADMIN_USERNAME: str = "admin"
    BOOTSTRAP_ADMIN_PASSWORD: str = "admin-change-me"


env = EnvSettings()