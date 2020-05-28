"""Allows more config file settings to be added to the database.

Revision ID: fd0ad656c67b
Revises: c5d321b34b54
Create Date: 2020-05-20 15:46:40.340882

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd0ad656c67b'
down_revision = 'c5d321b34b54'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'expected_scans',
        sa.Column('study', sa.String(length=32), nullable=False),
        sa.Column('site', sa.String(length=32), nullable=False),
        sa.Column('scantype', sa.String(length=64), nullable=False),
        sa.Column('num_expected', sa.Integer(), nullable=True,
                  server_default='0'),
        sa.Column('pha_num_expected', sa.Integer(), nullable=True,
                  server_default='0'),
        sa.ForeignKeyConstraint(
            ['study', 'scantype'],
            ['study_scantypes.study', 'study_scantypes.scantype'], ),
        sa.ForeignKeyConstraint(
            ['study', 'site'],
            ['study_sites.study', 'study_sites.site'], ),
        sa.PrimaryKeyConstraint('study', 'site', 'scantype')
    )
    op.add_column(
        'study_sites',
        sa.Column('uses_tech_notes', sa.Boolean, nullable=True,
                  server_default='false'))
    op.add_column(
        'sessions',
        sa.Column('tech_notes', sa.String(length=1028), nullable=True))
    op.add_column(
        'scantypes',
        sa.Column('pha_type', sa.String(length=64), nullable=True))
    op.add_column(
        'scantypes',
        sa.Column('qc_type', sa.String(length=64), nullable=True))


def downgrade():
    op.drop_column('study_sites', 'uses_tech_notes')
    op.drop_column('scantypes', 'qc_type')
    op.drop_column('scantypes', 'pha_type')
    op.drop_column('sessions', 'tech_notes')
    op.drop_table('expected_scans')
