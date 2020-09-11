"""Allows more config file settings to be added to the database.

This adds a few columns to track the 'USES_TECHNOTES', 'Count', 'PHACount',
'qc_type' and 'qc_pha' values from the config files. It also replaces the
study_scantypes table with an 'expected_scans' table.

Revision ID: fd0ad656c67b
Revises: c5d321b34b54
Create Date: 2020-05-20 15:46:40.340882

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd0ad656c67b'
down_revision = '442e3abe5587'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'studies',
        'is_open',
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default=sa.text('true')
    )

    expected_scans = op.create_table(
        'expected_scans',
        sa.Column('study', sa.String(length=32), nullable=False),
        sa.Column('site', sa.String(length=32), nullable=False),
        sa.Column('scantype', sa.String(length=64), nullable=False),
        sa.Column('num_expected', sa.Integer(), nullable=True,
                  server_default='0'),
        sa.Column('pha_num_expected', sa.Integer(), nullable=True,
                  server_default='0'),
        sa.ForeignKeyConstraint(['study'], ['studies.id'],
                                name='expected_scans_study_fkey'),
        sa.ForeignKeyConstraint(['site'], ['sites.name'],
                                name='expected_scans_site_fkey'),
        sa.ForeignKeyConstraint(['scantype'], ['scantypes.tag'],
                                name='expected_scans_scantype_fkey'),
        sa.ForeignKeyConstraint(
            ['study', 'site'],
            ['study_sites.study', 'study_sites.site'],
            name='expected_scans_allowed_sites_fkey'
        ),
        sa.PrimaryKeyConstraint('study', 'site', 'scantype')
    )

    conn = op.get_bind()
    records = conn.execute(
        'select study_sites.study, study_sites.site, study_scantypes.scantype '
        '  from study_sites, study_scantypes '
        '  where study_sites.study = study_scantypes.study;'
    )
    op.bulk_insert(
        expected_scans,
        [{'study': record[0],
          'site': record[1],
          'scantype': record[2]}
         for record in records]
    )

    op.add_column(
        'scans',
        sa.Column('length', sa.String(10), nullable=True)
    )
    op.add_column(
        'study_sites',
        sa.Column('uses_tech_notes', sa.Boolean, nullable=True,
                  server_default='false')
    )
    op.add_column(
        'sessions',
        sa.Column('tech_notes', sa.String(length=1028), nullable=True)
    )
    op.add_column(
        'scantypes',
        sa.Column('pha_type', sa.String(length=64), nullable=True)
    )
    op.add_column(
        'scantypes',
        sa.Column('qc_type', sa.String(length=64), nullable=True)
    )
    op.drop_constraint('gold_standards_study_fkey', 'gold_standards',
                       type_='foreignkey')
    op.drop_constraint('gold_standards_study_fkey1', 'gold_standards',
                       type_='foreignkey')
    op.create_foreign_key(
        'gold_standards_expected_scans_fkey',
        'gold_standards',
        'expected_scans',
        ['study', 'site', 'scantype'],
        ['study', 'site', 'scantype'],
    )
    op.drop_table('study_scantypes')
    op.drop_column('timepoints', 'static_page')
    op.drop_column('timepoints', 'last_qc_generated')


def downgrade():
    op.add_column(
        'timepoints',
        sa.Column(
            'last_qc_generated',
            sa.INTEGER(),
            server_default=sa.text('0'),
            autoincrement=False,
            nullable=False
        )
    )
    op.add_column(
        'timepoints',
        sa.Column(
            'static_page',
            sa.VARCHAR(length=1028),
            autoincrement=False,
            nullable=True
        )
    )
    op.alter_column(
        'studies',
        'is_open',
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default=sa.text('true')
    )

    study_scantypes = op.create_table(
        'study_scantypes',
        sa.Column('study', sa.String(length=32), nullable=False),
        sa.Column('scantype', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ['scantype'],
            ['scantypes.tag'],
            name='study_scantypes_scantype_fkey'
        ),
        sa.ForeignKeyConstraint(
            ['study'],
            ['studies.id'],
            name='study_scantypes_study_fkey'
        ),
        sa.PrimaryKeyConstraint('study', 'scantype')
    )

    conn = op.get_bind()
    records = conn.execute(
        'select study, scantype'
        '  from expected_scans '
        '  group by study, scantype '
        '  order by study, scantype;'
    )
    op.bulk_insert(
        study_scantypes,
        [{'study': record[0],
          'scantype': record[1]}
         for record in records]
    )

    op.drop_constraint('gold_standards_expected_scans_fkey', 'gold_standards',
                       type_='foreignkey')
    op.create_foreign_key('gold_standards_study_fkey1',
                          'gold_standards',
                          'study_sites',
                          ['study', 'site'],
                          ['study', 'site'])
    op.create_foreign_key('gold_standards_study_fkey',
                          'gold_standards',
                          'study_scantypes',
                          ['study', 'scantype'],
                          ['study', 'scantype'])
    op.drop_column('scans', 'length')
    op.drop_column('study_sites', 'uses_tech_notes')
    op.drop_column('scantypes', 'qc_type')
    op.drop_column('scantypes', 'pha_type')
    op.drop_column('sessions', 'tech_notes')
    op.drop_table('expected_scans')
