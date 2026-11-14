"""create student profile table

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'student_profile_table',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('learning_mode', sa.String(length=20), server_default='both', nullable=False),
        sa.Column('learning_level', sa.String(length=20), server_default='beginner', nullable=False),
        sa.Column('learning_goals', sa.Text(), nullable=True),
        sa.Column('skills_to_learn', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_table.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_student_profile_table_user_id'), 'student_profile_table', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_student_profile_table_user_id'), table_name='student_profile_table')
    op.drop_table('student_profile_table')

