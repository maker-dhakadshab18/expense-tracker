from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth_router,
    categories_router,
    expenses_router,
    health_router,
    summary_router,
)
from app.core.config import settings

app = FastAPI(title="Personal Expense Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

for router in (health_router, auth_router, categories_router, expenses_router, summary_router):
    app.include_router(router)
