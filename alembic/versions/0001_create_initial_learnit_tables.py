"""create initial LearnIt tables

Revision ID: 0001
Revises: 
Create Date: 2025-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. user_table
    op.create_table(
        'user_table',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_email_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_table_email'), 'user_table', ['email'], unique=True)

    # 2. revoked_token_table
    op.create_table(
        'revoked_token_table',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_revoked_token_table_token_hash'), 'revoked_token_table', ['token_hash'], unique=True)

    # 3. role_table
    op.create_table(
        'role_table',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_role_table_name'), 'role_table', ['name'], unique=True)

    # 4. user_role_table
    op.create_table(
        'user_role_table',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
        sa.ForeignKeyConstraint(['user_id'], ['user_table.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['role_table.id'], ),
    )
    op.create_index(op.f('ix_user_role_table_role_id'), 'user_role_table', ['role_id'], unique=False)
    op.create_index(op.f('ix_user_role_table_user_id'), 'user_role_table', ['user_id'], unique=False)

    # 5. teacher_profile_table
    op.create_table(
        'teacher_profile_table',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('experience_years', sa.Integer(), server_default='0', nullable=False),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('teaching_mode', sa.String(20), server_default='both', nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user_table.id'], ),
    )
    op.create_index(op.f('ix_teacher_profile_table_user_id'), 'teacher_profile_table', ['user_id'], unique=True)

    # 6. category_table
    op.create_table(
        'category_table',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_category_table_name'), 'category_table', ['name'], unique=True)
    op.create_index(op.f('ix_category_table_slug'), 'category_table', ['slug'], unique=True)

    # 7. skill_listing_table
    op.create_table(
        'skill_listing_table',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(140), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('level', sa.String(20), server_default='beginner', nullable=False),
        sa.Column('price_amount', sa.Numeric(10, 2), server_default='0', nullable=False),
        sa.Column('currency', sa.String(10), server_default='INR', nullable=False),
        sa.Column('price_unit', sa.String(20), server_default='session', nullable=False),
        sa.Column('teaching_mode', sa.String(20), server_default='both', nullable=False),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('area', sa.String(200), nullable=True),
        sa.Column('status', sa.String(20), server_default='draft', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('price_amount >= 0', name='chk_price_non_negative'),
        sa.ForeignKeyConstraint(['teacher_id'], ['user_table.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['category_table.id'], ),
    )
    op.create_index(op.f('ix_skill_listing_table_category_id'), 'skill_listing_table', ['category_id'], unique=False)
    op.create_index(op.f('ix_skill_listing_table_teacher_id'), 'skill_listing_table', ['teacher_id'], unique=False)

    # 8. learning_request_table
    op.create_table(
        'learning_request_table',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('skill_listing_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.String(1000), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('teacher_response', sa.Text(), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['skill_listing_id'], ['skill_listing_table.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['user_table.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['user_table.id'], ),
    )
    op.create_index(op.f('ix_learning_request_table_skill_listing_id'), 'learning_request_table', ['skill_listing_id'], unique=False)
    op.create_index(op.f('ix_learning_request_table_student_id'), 'learning_request_table', ['student_id'], unique=False)
    op.create_index(op.f('ix_learning_request_table_teacher_id'), 'learning_request_table', ['teacher_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_learning_request_table_teacher_id'), table_name='learning_request_table')
    op.drop_index(op.f('ix_learning_request_table_student_id'), table_name='learning_request_table')
    op.drop_index(op.f('ix_learning_request_table_skill_listing_id'), table_name='learning_request_table')
    op.drop_table('learning_request_table')

    op.drop_index(op.f('ix_skill_listing_table_teacher_id'), table_name='skill_listing_table')
    op.drop_index(op.f('ix_skill_listing_table_category_id'), table_name='skill_listing_table')
    op.drop_table('skill_listing_table')

    op.drop_index(op.f('ix_category_table_slug'), table_name='category_table')
    op.drop_index(op.f('ix_category_table_name'), table_name='category_table')
    op.drop_table('category_table')

    op.drop_index(op.f('ix_teacher_profile_table_user_id'), table_name='teacher_profile_table')
    op.drop_table('teacher_profile_table')

    op.drop_index(op.f('ix_user_role_table_user_id'), table_name='user_role_table')
    op.drop_index(op.f('ix_user_role_table_role_id'), table_name='user_role_table')
    op.drop_table('user_role_table')

    op.drop_index(op.f('ix_role_table_name'), table_name='role_table')
    op.drop_table('role_table')

    op.drop_index(op.f('ix_revoked_token_table_token_hash'), table_name='revoked_token_table')
    op.drop_table('revoked_token_table')

    op.drop_index(op.f('ix_user_table_email'), table_name='user_table')
    op.drop_table('user_table')
