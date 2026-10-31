"""Business rules. Every query here is scoped to a user_id — that's the authorization layer."""
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.security import hash_password, verify_password

DEFAULT_CATEGORIES = [
    "Food", "Transport", "Housing", "Utilities",
    "Shopping", "Entertainment", "Health", "Other",
]


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


# --- users ---------------------------------------------------------------

def register_user(db: Session, data: schemas.UserCreate) -> models.User:
    email = data.email.lower()
    if db.scalar(select(models.User).where(models.User.email == email)):
        raise Conflict("An account with this email already exists")
    user = models.User(email=email, password_hash=hash_password(data.password))
    db.add(user)
    db.flush()
    db.add_all(models.Category(user_id=user.id, name=n) for n in DEFAULT_CATEGORIES)
    db.commit()
    return user


def authenticate(db: Session, email: str, password: str) -> models.User | None:
    user = db.scalar(select(models.User).where(models.User.email == email.lower()))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


# --- categories ----------------------------------------------------------

def list_categories(db: Session, user_id: int) -> list[models.Category]:
    stmt = select(models.Category).where(models.Category.user_id == user_id).order_by(models.Category.name)
    return list(db.scalars(stmt))


def create_category(db: Session, user_id: int, data: schemas.CategoryCreate) -> models.Category:
    exists = db.scalar(
        select(models.Category).where(
            models.Category.user_id == user_id,
            func.lower(models.Category.name) == data.name.lower(),
        )
    )
    if exists:
        raise Conflict("Category already exists")
    cat = models.Category(user_id=user_id, name=data.name)
    db.add(cat)
    db.commit()
    return cat


def _owned_category(db: Session, user_id: int, category_id: int) -> models.Category:
    cat = db.get(models.Category, category_id)
    if cat is None or cat.user_id != user_id:
        raise NotFound("Category not found")
    return cat


# --- expenses ------------------------------------------------------------

def get_expense(db: Session, user_id: int, expense_id: int) -> models.Expense:
    exp = db.get(models.Expense, expense_id)
    # Same 404 for "doesn't exist" and "not yours" — don't reveal other users' ids.
    if exp is None or exp.user_id != user_id:
        raise NotFound("Expense not found")
    return exp


def list_expenses(
    db: Session,
    user_id: int,
    date_from: date | None,
    date_to: date | None,
    category_id: int | None,
    page: int,
    page_size: int,
) -> tuple[list[models.Expense], int]:
    conds = [models.Expense.user_id == user_id]
    if date_from:
        conds.append(models.Expense.expense_date >= date_from)
    if date_to:
        conds.append(models.Expense.expense_date <= date_to)
    if category_id:
        conds.append(models.Expense.category_id == category_id)

    total = db.scalar(select(func.count()).select_from(models.Expense).where(*conds)) or 0
    stmt = (
        select(models.Expense)
        .where(*conds)
        .order_by(models.Expense.expense_date.desc(), models.Expense.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(stmt).unique()), total


def create_expense(db: Session, user_id: int, data: schemas.ExpenseCreate) -> models.Expense:
    _owned_category(db, user_id, data.category_id)
    exp = models.Expense(user_id=user_id, **data.model_dump())
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


def update_expense(db: Session, user_id: int, expense_id: int, data: schemas.ExpenseUpdate) -> models.Expense:
    exp = get_expense(db, user_id, expense_id)
    changes = data.model_dump(exclude_unset=True)
    if "category_id" in changes:
        _owned_category(db, user_id, changes["category_id"])
    for field, value in changes.items():
        setattr(exp, field, value)
    db.commit()
    db.refresh(exp)
    return exp


def delete_expense(db: Session, user_id: int, expense_id: int) -> None:
    exp = get_expense(db, user_id, expense_id)
    db.delete(exp)
    db.commit()


# --- summary -------------------------------------------------------------

def monthly_summary(db: Session, user_id: int, year: int, month: int) -> schemas.Summary:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    stmt = (
        select(
            models.Category.id,
            models.Category.name,
            func.sum(models.Expense.amount),
            func.count(models.Expense.id),
        )
        .join(models.Category, models.Expense.category_id == models.Category.id)
        .where(
            models.Expense.user_id == user_id,
            models.Expense.expense_date >= start,
            models.Expense.expense_date < end,
        )
        .group_by(models.Category.id, models.Category.name)
        .order_by(func.sum(models.Expense.amount).desc())
    )
    rows = db.execute(stmt).all()
    by_cat = [
        schemas.CategoryTotal(category_id=r[0], category_name=r[1], total=r[2], count=r[3]) for r in rows
    ]
    return schemas.Summary(
        month=f"{year:04d}-{month:02d}",
        total=sum((c.total for c in by_cat), Decimal("0.00")),
        count=sum(c.count for c in by_cat),
        by_category=by_cat,
    )
