"""API contract. Kept separate from DB models so password_hash can never leak."""
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Money = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    created_at: datetime


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("Name cannot be blank")
        return v


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ExpenseCreate(BaseModel):
    amount: Money
    expense_date: date
    category_id: int
    note: str | None = Field(default=None, max_length=255)


class ExpenseUpdate(BaseModel):
    """PATCH: every field optional, but required fields can't be set to null."""
    amount: Money | None = None
    expense_date: date | None = None
    category_id: int | None = None
    note: str | None = Field(default=None, max_length=255)

    @field_validator("amount", "expense_date", "category_id")
    @classmethod
    def not_null(cls, v):
        if v is None:
            raise ValueError("Cannot be null")
        return v


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: Decimal
    expense_date: date
    note: str | None
    category: CategoryRead
    created_at: datetime
    updated_at: datetime


class ExpensePage(BaseModel):
    items: list[ExpenseRead]
    total: int
    page: int
    page_size: int


class CategoryTotal(BaseModel):
    category_id: int
    category_name: str
    total: Decimal
    count: int


class Summary(BaseModel):
    month: str
    total: Decimal
    count: int
    by_category: list[CategoryTotal]
