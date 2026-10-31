"""HTTP layer only: parse request, call service, map errors to status codes."""
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models, schemas, services
from app.core.security import create_access_token, decode_access_token
from app.db.session import get_db

DB = Annotated[Session, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: DB, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> models.User:
    user_id = decode_access_token(creds.credentials) if creds else None
    user = db.get(models.User, user_id) if user_id else None
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]


def _not_found(e: services.NotFound) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, str(e))


# --- health --------------------------------------------------------------
health_router = APIRouter(tags=["health"])


@health_router.get("/health")
def health(db: DB, response: Response):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "degraded", "db": "error"}


# --- auth ----------------------------------------------------------------
auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@auth_router.post("/register", response_model=schemas.Token, status_code=201)
def register(data: schemas.UserCreate, db: DB):
    try:
        user = services.register_user(db, data)
    except services.Conflict as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return schemas.Token(access_token=create_access_token(user.id))


@auth_router.post("/login", response_model=schemas.Token)
def login(data: schemas.LoginRequest, db: DB):
    user = services.authenticate(db, data.email, data.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return schemas.Token(access_token=create_access_token(user.id))


@auth_router.get("/me", response_model=schemas.UserRead)
def me(user: CurrentUser):
    return user


# --- categories ----------------------------------------------------------
categories_router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@categories_router.get("", response_model=list[schemas.CategoryRead])
def list_categories(db: DB, user: CurrentUser):
    return services.list_categories(db, user.id)


@categories_router.post("", response_model=schemas.CategoryRead, status_code=201)
def create_category(data: schemas.CategoryCreate, db: DB, user: CurrentUser):
    try:
        return services.create_category(db, user.id, data)
    except services.Conflict as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))


# --- expenses ------------------------------------------------------------
expenses_router = APIRouter(prefix="/api/v1/expenses", tags=["expenses"])


@expenses_router.get("", response_model=schemas.ExpensePage)
def list_expenses(
    db: DB,
    user: CurrentUser,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    category_id: int | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "'from' must be on or before 'to'")
    items, total = services.list_expenses(db, user.id, date_from, date_to, category_id, page, page_size)
    return schemas.ExpensePage(items=items, total=total, page=page, page_size=page_size)


@expenses_router.post("", response_model=schemas.ExpenseRead, status_code=201)
def create_expense(data: schemas.ExpenseCreate, db: DB, user: CurrentUser):
    try:
        return services.create_expense(db, user.id, data)
    except services.NotFound as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))


@expenses_router.get("/{expense_id}", response_model=schemas.ExpenseRead)
def get_expense(expense_id: int, db: DB, user: CurrentUser):
    try:
        return services.get_expense(db, user.id, expense_id)
    except services.NotFound as e:
        raise _not_found(e)


@expenses_router.patch("/{expense_id}", response_model=schemas.ExpenseRead)
def update_expense(expense_id: int, data: schemas.ExpenseUpdate, db: DB, user: CurrentUser):
    try:
        services.get_expense(db, user.id, expense_id)
    except services.NotFound as e:
        raise _not_found(e)
    try:
        return services.update_expense(db, user.id, expense_id, data)
    except services.NotFound as e:  # category not owned
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))


@expenses_router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: DB, user: CurrentUser):
    try:
        services.delete_expense(db, user.id, expense_id)
    except services.NotFound as e:
        raise _not_found(e)


# --- summary -------------------------------------------------------------
summary_router = APIRouter(prefix="/api/v1/summary", tags=["summary"])


@summary_router.get("", response_model=schemas.Summary)
def summary(
    db: DB,
    user: CurrentUser,
    month: Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", examples=["2026-10"])],
):
    year, mon = (int(p) for p in month.split("-"))
    return services.monthly_summary(db, user.id, year, mon)
