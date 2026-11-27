from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.domain.houses import ParticipantRole, ParticipantStatus
from src.models.users import User


class House(Base):
    __tablename__ = "houses_table"
    __table_args__ = (UniqueConstraint("login", name="uq_houses_table_login"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    login: Mapped[str] = mapped_column(String(64))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    info: Mapped["HouseInfo"] = relationship(
        back_populates="house", cascade="all, delete-orphan", passive_deletes=True
    )
    participants: Mapped[list["HouseParticipant"]] = relationship(
        back_populates="house", cascade="all, delete-orphan", passive_deletes=True
    )


class HouseInfo(Base):
    __tablename__ = "houses_info_table"

    house_id: Mapped[UUID] = mapped_column(
        ForeignKey("houses_table.id", ondelete="CASCADE"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    house: Mapped[House] = relationship(back_populates="info")


class HouseParticipant(Base):
    __tablename__ = "houses_participants_table"
    __table_args__ = (
        UniqueConstraint(
            "house_id", "user_id", name="uq_houses_participants_house_user"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    house_id: Mapped[UUID] = mapped_column(
        ForeignKey("houses_table.id", ondelete="CASCADE")
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users_table.id"), index=True)
    role: Mapped[ParticipantRole] = mapped_column(
        Enum(
            ParticipantRole,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            name="house_participant_role",
        )
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        Enum(
            ParticipantStatus,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            name="house_participant_status",
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    house: Mapped[House] = relationship(back_populates="participants")
    user: Mapped[User] = relationship()
