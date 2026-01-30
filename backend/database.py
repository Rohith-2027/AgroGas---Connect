# backend/database.py
import os
from typing import Generator
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime

# -------------------------------
# Database configuration (env-friendly)
# -------------------------------
DB_USER = os.getenv("DB_USER", "agrogas_user")
DB_PASS = os.getenv("DB_PASS", "agro123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "agrogas_db")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine; pool_pre_ping helps avoid stale connections
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for models
Base = declarative_base()


# -------------------------------
# Models
# -------------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    role = Column(String(20))
    phone = Column(String(20), unique=True)
    location = Column(String(100))
    password_hash = Column(String(255))
    reset_code = Column(String(6), nullable=True)
    reset_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Record(Base):
    """
    Farmer submission records. `available_kg` starts equal to mass_kg
    and is reduced when buyers place orders (so we can track stock).
    """
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    farmer_name = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)

    mass_kg = Column(Float, nullable=True)
    available_kg = Column(Float, nullable=True)        # available stock for orders
    mass_source = Column(String(20), nullable=True)    # "measured" or "predicted"

    moisture_percent = Column(Float, nullable=True)
    vs_fraction = Column(Float, nullable=True)

    predicted_m3_biogas = Column(Float, nullable=True)
    revenue_estimate = Column(Float, nullable=True)

    timestamp = Column(DateTime, server_default=func.now())

    # relationship to OrderItem (optional convenience)
    order_items = relationship("OrderItem", back_populates="record", cascade="none")


class Config(Base):
    __tablename__ = "config"

    id = Column(Integer, primary_key=True)
    price_per_m3 = Column(Float, default=50.0)
    default_yield_per_kgvs = Column(Float, default=0.20)
    default_methane_fraction = Column(Float, default=0.55)


class Order(Base):
    """
    Orders placed by buyers. Orders have items in OrderItem.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_name = Column(String(200), nullable=False)
    buyer_phone = Column(String(50), nullable=True)
    buyer_location = Column(String(200), nullable=True)

    total_price = Column(Float, nullable=False, default=0.0)
    status = Column(String(30), nullable=False, default="placed")
    created_at = Column(DateTime, server_default=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """
    Items inside an order referencing a Record (farmer submission).
    """
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    record_id = Column(Integer, ForeignKey("records.id"), nullable=False)

    qty_kg = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    record = relationship("Record", back_populates="order_items")


# -------------------------------
# Helpers
# -------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get a DB session for FastAPI routes.

    Usage in FastAPI:
        from database import get_db
        def my_route(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create tables (if not exist) and ensure a default config row exists.
    Call this once at setup or on application startup if you want auto-initialization.

    Example:
        from database import init_db
        init_db()
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created (if they did not exist).")

    # Ensure default config row exists
    db = SessionLocal()
    try:
        cfg = db.query(Config).first()
        if not cfg:
            cfg = Config(
                price_per_m3=float(os.getenv("DEFAULT_PRICE_PER_M3", 50.0)),
                default_yield_per_kgvs=float(os.getenv("DEFAULT_YIELD_PER_KGVS", 0.20)),
                default_methane_fraction=float(os.getenv("DEFAULT_METHANE_FRACTION", 0.55)),
            )
            db.add(cfg)
            db.commit()
            print("✅ Default config row inserted into `config` table.")
        else:
            print("ℹ️ Config row already exists.")
    except Exception as e:
        print("⚠️ Error while ensuring default config:", e)
    finally:
        db.close()
