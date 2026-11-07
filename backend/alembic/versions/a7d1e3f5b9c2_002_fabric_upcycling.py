"""002_fabric_upcycling

Adds guest-scoped tables for the fabric upcycling workflow:
fabric_analyses, saved_ideas, completed_projects.

Revision ID: a7d1e3f5b9c2
Revises: c65fa324f3bc
Create Date: 2026-10-26 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7d1e3f5b9c2'
down_revision: Union[str, Sequence[str], None] = 'c65fa324f3bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('fabric_analyses',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('owner_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('image_filename', sa.String(length=80), nullable=False),
    sa.Column('image_sha256', sa.String(length=64), nullable=False),
    sa.Column('image_width', sa.Integer(), nullable=False),
    sa.Column('image_height', sa.Integer(), nullable=False),
    sa.Column('predictions_json', sa.Text(), nullable=False),
    sa.Column('decision_json', sa.Text(), nullable=False),
    sa.Column('decision_status', sa.String(length=32), nullable=False),
    sa.Column('final_label', sa.String(length=80), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fabric_analyses_owner_hash'), 'fabric_analyses', ['owner_hash'], unique=False)

    op.create_table('saved_ideas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('owner_hash', sa.String(length=64), nullable=False),
    sa.Column('analysis_id', sa.String(length=36), nullable=True),
    sa.Column('idea_id', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['fabric_analyses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('owner_hash', 'analysis_id', 'idea_id', name='uq_saved_owner_analysis_idea')
    )
    op.create_index(op.f('ix_saved_ideas_id'), 'saved_ideas', ['id'], unique=False)
    op.create_index(op.f('ix_saved_ideas_owner_hash'), 'saved_ideas', ['owner_hash'], unique=False)
    op.create_index(op.f('ix_saved_ideas_analysis_id'), 'saved_ideas', ['analysis_id'], unique=False)

    op.create_table('completed_projects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('owner_hash', sa.String(length=64), nullable=False),
    sa.Column('analysis_id', sa.String(length=36), nullable=True),
    sa.Column('idea_id', sa.String(length=64), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('notes', sa.String(length=500), nullable=True),
    sa.Column('weight_kg', sa.Float(), nullable=False),
    sa.Column('weight_source', sa.String(length=24), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['fabric_analyses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_completed_projects_id'), 'completed_projects', ['id'], unique=False)
    op.create_index(op.f('ix_completed_projects_owner_hash'), 'completed_projects', ['owner_hash'], unique=False)
    op.create_index(op.f('ix_completed_projects_analysis_id'), 'completed_projects', ['analysis_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_completed_projects_analysis_id'), table_name='completed_projects')
    op.drop_index(op.f('ix_completed_projects_owner_hash'), table_name='completed_projects')
    op.drop_index(op.f('ix_completed_projects_id'), table_name='completed_projects')
    op.drop_table('completed_projects')
    op.drop_index(op.f('ix_saved_ideas_analysis_id'), table_name='saved_ideas')
    op.drop_index(op.f('ix_saved_ideas_owner_hash'), table_name='saved_ideas')
    op.drop_index(op.f('ix_saved_ideas_id'), table_name='saved_ideas')
    op.drop_table('saved_ideas')
    op.drop_index(op.f('ix_fabric_analyses_owner_hash'), table_name='fabric_analyses')
    op.drop_table('fabric_analyses')