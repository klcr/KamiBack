"""Uvicorn エントリーポイント。uvicorn api.src.main:app で起動する。"""

from api.src.api import app

__all__ = ["app"]
