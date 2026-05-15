"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("team_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("team_name", sa.String(255), nullable=False),
        sa.Column("parent_team_id", UUID(as_uuid=True), sa.ForeignKey("teams.team_id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("user_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger, unique=True, nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="manager"),
        sa.Column("team_id", UUID(as_uuid=True), sa.ForeignKey("teams.team_id"), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "employees",
        sa.Column("employee_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("position", sa.String(255), nullable=True),
        sa.Column("level", sa.String(100), nullable=True),
        sa.Column("team_id", UUID(as_uuid=True), sa.ForeignKey("teams.team_id"), nullable=True),
        sa.Column("manager_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "manager_employee_visibility",
        sa.Column("manager_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), primary_key=True),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.employee_id"), primary_key=True),
        sa.Column("granted_by", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "criteria_matrix",
        sa.Column("criterion_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("criterion_name", sa.String(255), nullable=False),
        sa.Column("below_description", sa.Text, nullable=False, server_default=""),
        sa.Column("meet_description", sa.Text, nullable=False, server_default=""),
        sa.Column("exceeds_description", sa.Text, nullable=False, server_default=""),
        sa.Column("role", sa.String(255), nullable=True),
        sa.Column("weight", sa.Numeric(3, 1), server_default="1.0"),
        sa.Column("is_key_criterion", sa.Boolean, server_default="false"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "periods",
        sa.Column("period_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("period_name", sa.String(100), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "feedback",
        sa.Column("feedback_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("manager_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("period_id", UUID(as_uuid=True), sa.ForeignKey("periods.period_id"), nullable=True),
        sa.Column("feedback_date", sa.Date, nullable=False),
        sa.Column("original_text", sa.Text, nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="telegram"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("is_deleted", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_feedback_employee_period", "feedback", ["employee_id", "period_id"])
    op.create_index("ix_feedback_manager", "feedback", ["manager_id"])

    op.create_table(
        "feedback_criterion_mappings",
        sa.Column("mapping_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("feedback_id", UUID(as_uuid=True), sa.ForeignKey("feedback.feedback_id"), nullable=False),
        sa.Column("criterion_id", UUID(as_uuid=True), sa.ForeignKey("criteria_matrix.criterion_id"), nullable=False),
        sa.Column("original_fragment", sa.Text, nullable=True),
        sa.Column("suggested_rating", sa.String(50), nullable=True),
        sa.Column("confirmed_rating", sa.String(50), nullable=True),
        sa.Column("llm_explanation", sa.Text, nullable=True),
        sa.Column("manager_confirmed", sa.Boolean, server_default="false"),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_mappings_feedback", "feedback_criterion_mappings", ["feedback_id"])
    op.create_index("ix_mappings_criterion", "feedback_criterion_mappings", ["criterion_id"])

    op.create_table(
        "summaries",
        sa.Column("summary_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("manager_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("period_id", UUID(as_uuid=True), sa.ForeignKey("periods.period_id"), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("total_feedback_count", sa.Integer, server_default="0"),
        sa.Column("mapped_feedback_count", sa.Integer, server_default="0"),
        sa.Column("unmapped_feedback_count", sa.Integer, server_default="0"),
        sa.Column("strengths", JSONB, nullable=True),
        sa.Column("growth_areas", JSONB, nullable=True),
        sa.Column("criterion_breakdown", JSONB, nullable=True),
        sa.Column("top_criteria", JSONB, nullable=True),
        sa.Column("repeating_patterns", JSONB, nullable=True),
        sa.Column("rating_recommendation", sa.String(50), nullable=True),
        sa.Column("arguments_for", JSONB, nullable=True),
        sa.Column("arguments_against", JSONB, nullable=True),
        sa.Column("risks", JSONB, nullable=True),
        sa.Column("disputed_areas", JSONB, nullable=True),
        sa.Column("needs_attention", JSONB, nullable=True),
        sa.Column("evidence_comments", JSONB, nullable=True),
        sa.Column("llm_model_version", sa.String(100), nullable=True),
        sa.Column("is_current", sa.Boolean, server_default="true"),
    )

    op.create_index("ix_summaries_employee_period", "summaries", ["employee_id", "period_id"])


def downgrade() -> None:
    op.drop_table("summaries")
    op.drop_table("feedback_criterion_mappings")
    op.drop_table("feedback")
    op.drop_table("periods")
    op.drop_table("criteria_matrix")
    op.drop_table("manager_employee_visibility")
    op.drop_table("employees")
    op.drop_table("users")
    op.drop_table("teams")
