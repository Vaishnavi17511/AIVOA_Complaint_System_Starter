from datetime import datetime

from sqlalchemy import create_engine, String, Text, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class ComplaintRecord(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    # Complaint form parameters
    complaint_source: Mapped[str | None] = mapped_column(String(255))
    customer_name: Mapped[str | None] = mapped_column(String(255))
    product_name: Mapped[str | None] = mapped_column(String(255))
    product_strength: Mapped[str | None] = mapped_column(String(255))

    batch_lot_number: Mapped[str | None] = mapped_column(String(255))

    manufacturing_date: Mapped[str | None] = mapped_column(String(50))
    expiry_date: Mapped[str | None] = mapped_column(String(50))

    quantity_affected: Mapped[str | None] = mapped_column(String(255))

    complaint_type: Mapped[str | None] = mapped_column(String(255))
    complaint_date: Mapped[str | None] = mapped_column(String(50))

    detailed_complaint_description: Mapped[str | None] = mapped_column(
        Text
    )

    # AI-generated risk assessment
    severity: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[str | None] = mapped_column(String(50))

    rationale: Mapped[str | None] = mapped_column(Text)

    recommended_action: Mapped[str | None] = mapped_column(Text)

    investigation_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    missing_information: Mapped[str | None] = mapped_column(Text)

    # Database timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


def init_db():
    Base.metadata.create_all(bind=engine)