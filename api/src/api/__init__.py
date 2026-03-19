"""FastAPI アプリケーション定義。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.src.api.routes.scan.correct import router as scan_correct_router
from api.src.api.routes.scan.ocr import router as scan_ocr_router
from api.src.api.routes.templates.extend import router as templates_extend_router
from api.src.api.routes.templates.parse import router as templates_parse_router
from api.src.api.routes.templates.validate import router as templates_validate_router

app = FastAPI(title="KamiBack API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://klcr.github.io",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(templates_parse_router, prefix="/api/templates", tags=["templates"])
app.include_router(templates_validate_router, prefix="/api/templates", tags=["templates"])
app.include_router(templates_extend_router, prefix="/api/templates", tags=["templates"])
app.include_router(scan_correct_router, prefix="/api/scan", tags=["scan"])
app.include_router(scan_ocr_router, prefix="/api/scan", tags=["scan"])
