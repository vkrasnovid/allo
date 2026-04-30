"""Initial schema — all tables."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"btree_gist\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\"")

    # ===== tenants =====
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address", sa.String(500)),
        sa.Column("description", sa.String(1000)),
        sa.Column("timezone", sa.String(50), server_default="Europe/Moscow"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_tenants_slug", "tenants", ["slug"])

    # ===== services =====
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("yclients_id", sa.Integer()),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("price_rub", sa.Numeric(10, 2), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "yclients_id", name="unique_tenant_yclients"),
    )
    op.create_index("idx_services_tenant", "services", ["tenant_id"])
    op.create_index("idx_services_category", "services", ["tenant_id", "category"])

    # ===== masters =====
    op.create_table(
        "masters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("yclients_id", sa.Integer()),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("specialization", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_masters_tenant", "masters", ["tenant_id"])

    # ===== master_services =====
    op.create_table(
        "master_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("master_id", "service_id", name="unique_master_service"),
    )
    op.create_index("idx_master_services_master", "master_services", ["master_id"])
    op.create_index("idx_master_services_service", "master_services", ["service_id"])

    # ===== clients =====
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("total_visits", sa.Integer(), server_default=sa.text("0")),
        sa.Column("last_visit_at", sa.DateTime(timezone=True)),
        sa.Column("preferences", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "phone", name="unique_tenant_phone"),
    )
    op.create_index("idx_clients_tenant", "clients", ["tenant_id"])
    op.create_index("idx_clients_phone", "clients", ["tenant_id", "phone"])

    # ===== bookings =====
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("yclients_id", sa.Integer()),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_rub", sa.Numeric(10, 2), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("source", sa.String(20), server_default="phone"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
    )
    op.create_index("idx_bookings_tenant", "bookings", ["tenant_id"])
    op.create_index("idx_bookings_client", "bookings", ["tenant_id", "client_id"])
    op.create_index("idx_bookings_master", "bookings", ["tenant_id", "master_id"])
    op.create_index("idx_bookings_start", "bookings", ["tenant_id", "start_at"])
    op.create_index("idx_bookings_status", "bookings", ["tenant_id", "status"])
    op.create_index("idx_bookings_date", "bookings", [sa.text("tenant_id"), sa.text("start_at::date")])

    # GIST index for overlap exclusion
    op.execute("""
        CREATE INDEX idx_bookings_no_overlap
        ON bookings USING GIST (tenant_id, master_id,
                                tstzrange(start_at, end_at) WITH =)
        WHERE status NOT IN ('cancelled', 'no_show')
    """)

    # ===== booking_history =====
    op.create_table(
        "booking_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.String(20)),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column("changed_by", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_book_hist_booking", "booking_history", ["booking_id"])

    # ===== calls =====
    op.create_table(
        "calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("caller_phone", sa.String(20), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True)),
        sa.Column("did", sa.String(20), nullable=False),
        sa.Column("session_id", sa.String(255)),
        sa.Column("status", sa.String(30), server_default="in_progress"),
        sa.Column("duration_sec", sa.Integer()),
        sa.Column("audio_key", sa.String(500)),
        sa.Column("transcript_text", sa.Text()),
        sa.Column("result", sa.String(50)),
        sa.Column("error_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_calls_tenant", "calls", ["tenant_id"])
    op.create_index("idx_calls_caller", "calls", ["tenant_id", "caller_phone"])
    op.create_index("idx_calls_created", "calls", ["tenant_id", sa.text("created_at DESC")])
    op.create_index("idx_calls_status", "calls", ["tenant_id", "status"])

    # ===== call_transcripts =====
    op.create_table(
        "call_transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("speaker", sa.String(10), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_sec", sa.Numeric(8, 3)),
        sa.Column("end_sec", sa.Numeric(8, 3)),
        sa.Column("tool_calls", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_transcripts_call", "call_transcripts", ["call_id"])

    # ===== call_bookings =====
    op.create_table(
        "call_bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("call_id", "booking_id", name="unique_call_booking"),
    )
    op.create_index("idx_call_bookings_call", "call_bookings", ["call_id"])
    op.create_index("idx_call_bookings_booking", "call_bookings", ["booking_id"])

    # ===== prompt_profiles =====
    op.create_table(
        "prompt_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "name", name="unique_tenant_profile_name"),
    )
    op.create_index("idx_prompt_profiles_tenant", "prompt_profiles", ["tenant_id"])

    # ===== prompt_blocks =====
    op.create_table(
        "prompt_blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("block_key", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["profile_id"], ["prompt_profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("profile_id", "block_key", name="unique_profile_block_key"),
    )
    op.create_index("idx_prompt_blocks_profile", "prompt_blocks", ["profile_id"])

    # ===== sip_settings =====
    op.create_table(
        "sip_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("did", sa.String(20), unique=True, nullable=False),
        sa.Column("forward_number", sa.String(20)),
        sa.Column("sip_user", sa.String(100)),
        sa.Column("sip_password", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_sip_tenant", "sip_settings", ["tenant_id"])
    op.create_index("idx_sip_did", "sip_settings", ["did"])

    # ===== notification_settings =====
    op.create_table(
        "notification_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("telegram_chat_id", sa.String(100)),
        sa.Column("sms_enabled", sa.Boolean(), server_default=sa.text("TRUE")),
        sa.Column("reminder_day", sa.Boolean(), server_default=sa.text("TRUE")),
        sa.Column("reminder_hour", sa.Boolean(), server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )

    # ===== scheduled_notifications =====
    op.create_table(
        "scheduled_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_type", sa.String(20), nullable=False),
        sa.Column("send_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent", sa.Boolean(), server_default=sa.text("FALSE")),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_sched_notif_send", "scheduled_notifications", ["send_at", "sent"],
                    postgresql_where=sa.text("sent = FALSE"))


def downgrade() -> None:
    op.drop_table("scheduled_notifications")
    op.drop_table("notification_settings")
    op.drop_table("sip_settings")
    op.drop_table("prompt_blocks")
    op.drop_table("prompt_profiles")
    op.drop_table("call_bookings")
    op.drop_table("call_transcripts")
    op.drop_table("calls")
    op.drop_table("booking_history")
    op.drop_table("bookings")
    op.drop_table("clients")
    op.drop_table("master_services")
    op.drop_table("masters")
    op.drop_table("services")
    op.drop_table("tenants")
