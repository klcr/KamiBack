"""FastAPI アプリケーション定義。"""

from fastapi import FastAPI

from api.src.api.routes.templates.extend import router as templates_extend_router
from api.src.api.routes.templates.parse import router as templates_parse_router
from api.src.api.routes.templates.validate import router as templates_validate_router

app = FastAPI(title="KamiBack API", version="0.1.0")

app.include_router(templates_parse_router, prefix="/api/templates", tags=["templates"])
app.include_router(templates_validate_router, prefix="/api/templates", tags=["templates"])
app.include_router(templates_extend_router, prefix="/api/templates", tags=["templates"])
