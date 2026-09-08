import os
from datetime import date, datetime, timedelta
from decimal import Decimal

import uvicorn

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from jose import JWTError, jwt
import base64
import hashlib
import hmac
import secrets

from pydantic import BaseModel, EmailStr, Field

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    create_engine,
    func,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    joinedload,
    mapped_column,
    relationship,
    sessionmaker,
)


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "Expense Tracker"

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))

STREAMLIT_HOST = "127.0.0.1"
STREAMLIT_PORT = 8501

DATABASE_FILE = os.getenv("DATABASE_FILE", "expense_tracker.db")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")

# Render/Postgres may provide postgres:// or postgresql:// URLs.
# SQLAlchemy with psycopg uses the explicit postgresql+psycopg:// driver.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgres://"): ]
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"): ]

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "expense-tracker-change-this-secret",
)

JWT_ALGORITHM = "HS256"

JWT_EXPIRE_MINUTES = 1440


# ============================================================
# DATABASE
# ============================================================

engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


# ============================================================
# DATABASE MODELS
# ============================================================

class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    expenses = relationship(
        "Expense",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    incomes = relationship(
        "Income",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    budgets = relationship(
        "Budget",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Category(Base):

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    icon: Mapped[str] = mapped_column(
        String(10),
        default="📌",
    )

    expenses = relationship(
        "Expense",
        back_populates="category",
    )


class Expense(Base):

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    expense_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    user = relationship(
        "User",
        back_populates="expenses",
    )

    category = relationship(
        "Category",
        back_populates="expenses",
    )


class Income(Base):

    __tablename__ = "incomes"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    income_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    user = relationship(
        "User",
        back_populates="incomes",
    )


class Budget(Base):

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
    )

    month: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="budgets",
    )

    category = relationship(
        "Category"
    )


# ============================================================
# CREATE DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# DEFAULT CATEGORIES
# ============================================================

def create_default_categories():

    db = SessionLocal()

    categories = [
        ("Food", "🍔"),
        ("Transport", "🚗"),
        ("Shopping", "🛍️"),
        ("Bills", "🧾"),
        ("Entertainment", "🎬"),
        ("Healthcare", "💊"),
        ("Education", "📚"),
        ("Travel", "✈️"),
        ("Rent", "🏠"),
        ("Subscriptions", "📱"),
        ("Salary", "💼"),
        ("Other", "📌"),
    ]

    for name, icon in categories:

        existing = (
            db.query(Category)
            .filter(
                Category.name == name
            )
            .first()
        )

        if not existing:

            db.add(
                Category(
                    name=name,
                    icon=icon,
                )
            )

    db.commit()

    db.close()


create_default_categories()


# ============================================================
# SECURITY
# ============================================================

# Password hashing
#
# The original app used Passlib + bcrypt.  Newer bcrypt releases are not
# compatible with the version of Passlib commonly installed on Windows/Python
# 3.14, which causes registration to fail before the password is even hashed.
# Use Python's standard-library PBKDF2 instead; it is portable and does not
# depend on the incompatible Passlib/bcrypt combination.
PASSWORD_ITERATIONS = 600_000


bearer_scheme = HTTPBearer(
    auto_error=False
)


def hash_password(password):
    password_bytes = password.encode("utf-8")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        PASSWORD_ITERATIONS,
    )
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    digest_text = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt_text}${digest_text}"


def verify_password(
    password,
    hashed_password,
):
    try:
        scheme, iterations_text, salt_text, digest_text = hashed_password.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        padding = "=" * (-len(salt_text) % 4)
        salt = base64.urlsafe_b64decode((salt_text + padding).encode("ascii"))
        expected_padding = "=" * (-len(digest_text) % 4)
        expected = base64.urlsafe_b64decode((digest_text + expected_padding).encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def create_access_token(
    user_id
):

    expiration = datetime.utcnow() + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(
    token
):

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        return int(
            payload["sub"]
        )

    except (
        JWTError,
        KeyError,
        ValueError,
        TypeError,
    ):

        return None


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()


# ============================================================
# CURRENT USER
# ============================================================

def get_current_user(

    credentials:
    HTTPAuthorizationCredentials | None =
    Depends(bearer_scheme),

    db: Session =
    Depends(get_db),
):

    if not credentials:

        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    user_id = decode_access_token(
        credentials.credentials
    )

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user = db.get(
        User,
        user_id,
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class RegisterRequest(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )


class LoginRequest(BaseModel):

    email: EmailStr

    password: str


class ExpenseRequest(BaseModel):

    amount: Decimal = Field(
        gt=0
    )

    category_id: int

    description: str | None = None

    expense_date: date


class IncomeRequest(BaseModel):

    amount: Decimal = Field(
        gt=0
    )

    source: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = None

    income_date: date


class BudgetRequest(BaseModel):

    category_id: int

    month: date

    amount: Decimal = Field(
        gt=0
    )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

api = FastAPI(
    title="Expense Tracker API",
    version="1.0.0",
)


api.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("FRONTEND_ORIGIN", "*").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API HOME
# ============================================================

@api.get("/")
def api_home():

    return {
        "application": APP_NAME,
        "status": "running",
        "database": "SQLite",
    }


@api.get("/health")
def api_health():

    return {
        "status": "ok"
    }


# ============================================================
# AUTHENTICATION
# ============================================================

@api.post("/auth/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):

    email = (
        str(data.email)
        .lower()
        .strip()
    )

    existing_user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        name=data.name.strip(),
        email=email,
        password_hash=hash_password(
            data.password
        ),
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    token = create_access_token(
        user.id
    )

    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    }


@api.post("/auth/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):

    email = (
        str(data.email)
        .lower()
        .strip()
    )

    user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if (
        not user
        or not verify_password(
            data.password,
            user.password_hash,
        )
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(
        user.id
    )

    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    }


@api.get("/auth/me")
def current_user_info(
    user: User =
    Depends(get_current_user),
):

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


# ============================================================
# CATEGORIES
# ============================================================

@api.get("/categories")
def categories(
    _: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    return (
        db.query(Category)
        .order_by(Category.name)
        .all()
    )


# ============================================================
# EXPENSES
# ============================================================

@api.get("/expenses")
def get_expenses(

    start: date | None = None,

    end: date | None = None,

    category_id: int | None = None,

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    query = (
        db.query(Expense)
        .options(
            joinedload(
                Expense.category
            )
        )
        .filter(
            Expense.user_id == user.id
        )
    )

    if start:

        query = query.filter(
            Expense.expense_date >= start
        )

    if end:

        query = query.filter(
            Expense.expense_date <= end
        )

    if category_id:

        query = query.filter(
            Expense.category_id
            == category_id
        )

    rows = (
        query
        .order_by(
            Expense.expense_date.desc(),
            Expense.id.desc(),
        )
        .limit(1000)
        .all()
    )

    return [
        {
            "id": item.id,
            "amount": float(
                item.amount
            ),
            "category_id": item.category_id,
            "category": item.category.name,
            "icon": item.category.icon,
            "description": item.description,
            "expense_date": str(
                item.expense_date
            ),
        }
        for item in rows
    ]


@api.post("/expenses")
def add_expense(

    data: ExpenseRequest,

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    category = db.get(
        Category,
        data.category_id,
    )

    if not category:

        raise HTTPException(
            status_code=400,
            detail="Invalid category",
        )

    expense = Expense(
        user_id=user.id,
        amount=data.amount,
        category_id=data.category_id,
        description=data.description,
        expense_date=data.expense_date,
    )

    db.add(expense)

    db.commit()

    db.refresh(expense)

    return {
        "message": "Expense added successfully",
        "id": expense.id,
    }


@api.put("/expenses/{expense_id}")
def update_expense(

    expense_id: int,

    data: ExpenseRequest,

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    expense = (
        db.query(Expense)
        .filter(
            Expense.id == expense_id,
            Expense.user_id == user.id,
        )
        .first()
    )

    if not expense:

        raise HTTPException(
            status_code=404,
            detail="Expense not found",
        )

    expense.amount = data.amount
    expense.category_id = data.category_id
    expense.description = data.description
    expense.expense_date = data.expense_date

    db.commit()

    return {
        "message": "Expense updated successfully"
    }


@api.delete("/expenses/{expense_id}")
def delete_expense(

    expense_id: int,

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    expense = (
        db.query(Expense)
        .filter(
            Expense.id == expense_id,
            Expense.user_id == user.id,
        )
        .first()
    )

    if not expense:

        raise HTTPException(
            status_code=404,
            detail="Expense not found",
        )

    db.delete(expense)

    db.commit()

    return {
        "message": "Expense deleted successfully"
    }


# ============================================================
# INCOME
# ============================================================

@api.get("/income")
def get_income(

    start: date | None = None,

    end: date | None = None,

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    query = (
        db.query(Income)
        .filter(
            Income.user_id == user.id
        )
    )

    if start:

        query = query.filter(
            Income.income_date >= start
        )

    if end:

        query = query.filter(
            Income.income_date <= end
        )

    rows = (
        query
        .order_by(
            Income.income_date.desc(),
            Income.id.desc(),
        )
        .limit(1000)
        .all()
    )

    return [
        {
            "id": item.id,
            "amount": float(
                item.amount
            ),
            "source": item.source,
            "description": item.description,
            "income_date": str(
                item.income_date
            ),
        }
        for item in rows
    ]


@api.post("/income")
def add_income(

    data: IncomeRequest,

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    income = Income(
        user_id=user.id,
        amount=data.amount,
        source=data.source,
        description=data.description,
        income_date=data.income_date,
    )

    db.add(income)

    db.commit()

    db.refresh(income)

    return {
        "message": "Income added successfully",
        "id": income.id,
    }


@api.put("/income/{income_id}")
def update_income(

    income_id: int,

    data: IncomeRequest,

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    income = (
        db.query(Income)
        .filter(
            Income.id == income_id,
            Income.user_id == user.id,
        )
        .first()
    )

    if not income:

        raise HTTPException(
            status_code=404,
            detail="Income not found",
        )

    income.amount = data.amount
    income.source = data.source
    income.description = data.description
    income.income_date = data.income_date

    db.commit()

    return {
        "message": "Income updated successfully"
    }


@api.delete("/income/{income_id}")
def delete_income(

    income_id: int,

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    income = (
        db.query(Income)
        .filter(
            Income.id == income_id,
            Income.user_id == user.id,
        )
        .first()
    )

    if not income:

        raise HTTPException(
            status_code=404,
            detail="Income not found",
        )

    db.delete(income)

    db.commit()

    return {
        "message": "Income deleted successfully"
    }


# ============================================================
# BUDGETS
# ============================================================

@api.get("/budgets")
def get_budgets(

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    rows = (
        db.query(Budget)
        .options(
            joinedload(
                Budget.category
            )
        )
        .filter(
            Budget.user_id == user.id
        )
        .order_by(
            Budget.month.desc()
        )
        .all()
    )

    return [
        {
            "id": item.id,
            "category_id": item.category_id,
            "category": item.category.name,
            "month": str(item.month),
            "amount": float(
                item.amount
            ),
        }
        for item in rows
    ]


@api.post("/budgets")
def save_budget(

    data: BudgetRequest,

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    month = data.month.replace(
        day=1
    )

    existing = (
        db.query(Budget)
        .filter(
            Budget.user_id == user.id,
            Budget.category_id
            == data.category_id,
            Budget.month == month,
        )
        .first()
    )

    if existing:

        existing.amount = data.amount

    else:

        budget = Budget(
            user_id=user.id,
            category_id=data.category_id,
            month=month,
            amount=data.amount,
        )

        db.add(budget)

    db.commit()

    return {
        "message": "Budget saved successfully"
    }


@api.delete("/budgets/{budget_id}")
def delete_budget(

    budget_id: int,

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    budget = (
        db.query(Budget)
        .filter(
            Budget.id == budget_id,
            Budget.user_id == user.id,
        )
        .first()
    )

    if not budget:

        raise HTTPException(
            status_code=404,
            detail="Budget not found",
        )

    db.delete(budget)

    db.commit()

    return {
        "message": "Budget deleted successfully"
    }


# ============================================================
# DASHBOARD
# ============================================================

@api.get("/dashboard")
def dashboard(

    user: User =
    Depends(get_current_user),

    db: Session =
    Depends(get_db),
):

    total_income = (
        db.query(
            func.coalesce(
                func.sum(
                    Income.amount
                ),
                0,
            )
        )
        .filter(
            Income.user_id == user.id
        )
        .scalar()
        or 0
    )

    total_expenses = (
        db.query(
            func.coalesce(
                func.sum(
                    Expense.amount
                ),
                0,
            )
        )
        .filter(
            Expense.user_id == user.id
        )
        .scalar()
        or 0
    )

    today = date.today()

    month_start = today.replace(
        day=1
    )

    month_expenses = (
        db.query(
            func.coalesce(
                func.sum(
                    Expense.amount
                ),
                0,
            )
        )
        .filter(
            Expense.user_id == user.id,
            Expense.expense_date
            >= month_start,
        )
        .scalar()
        or 0
    )

    category_rows = (
        db.query(
            Category.name,
            Category.icon,
            func.sum(
                Expense.amount
            ),
        )
        .join(
            Expense,
            Expense.category_id
            == Category.id,
        )
        .filter(
            Expense.user_id == user.id,
            Expense.expense_date
            >= month_start,
        )
        .group_by(
            Category.name,
            Category.icon,
        )
        .order_by(
            func.sum(
                Expense.amount
            ).desc()
        )
        .all()
    )

    return {
        "total_income": float(
            total_income
        ),
        "total_expenses": float(
            total_expenses
        ),
        "balance": float(
            total_income
            - total_expenses
        ),
        "month_expenses": float(
            month_expenses
        ),
        "category_breakdown": [
            {
                "category": name,
                "icon": icon,
                "amount": float(
                    amount
                ),
            }
            for (
                name,
                icon,
                amount,
            ) in category_rows
        ],
    }


# ============================================================


# ============================================================
# FASTAPI SERVER
# ============================================================

def run_fastapi():
    uvicorn.run(api, host=API_HOST, port=API_PORT, log_level="info")


if __name__ == "__main__":
    run_fastapi()
