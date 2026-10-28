"""应用配置:环境变量驱动,本地/线上同一套代码。"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> 上溯 3 层到仓库根
BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BASE_DIR.parent
# 既有数据库在 admin/data/ 下,新后端直接复用,不搬迁
LEGACY_DB = REPO_ROOT / "admin" / "data" / "mysite.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MYSITE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- 基础 ---
    app_name: str = "至尊杰的小窝"
    debug: bool = False
    site_origin: str = "https://imyxj.xyz"

    # --- 数据库:沿用既有 SQLite,零迁移成本 ---
    db_path: str = str(LEGACY_DB)

    # --- 会话与安全 ---
    secret_key: str = "dev-only-change-me"
    session_cookie: str = "mysite_session"
    cookie_secure: bool = True
    session_max_age: int = 168 * 3600
    idle_timeout_min: int = 60

    # --- 上传 ---
    upload_dir: str = str(REPO_ROOT / "assets" / "uploads")
    max_upload_bytes: int = 8 * 1024 * 1024

    # --- 前端产物(生产由 nginx 直出,开发走 Vite) ---
    frontend_dist: str = str(REPO_ROOT / "frontend" / "dist")

    @property
    def db_file(self) -> Path:
        return Path(self.db_path)


settings = Settings()
