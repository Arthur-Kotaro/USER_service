"""add security fields

Revision ID: 7e4d34b30b5b
Revises: 
Create Date: 2026-08-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = '7e4d34b30b5b'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 1. Создаём department
    op.create_table('department',
        sa.Column('dept_code', sa.String(20), nullable=False),
        sa.Column('dept_name', sa.String(200), nullable=False),
        sa.Column('parent_dept_code', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('dept_code'),
        sa.UniqueConstraint('dept_name'),
        sa.ForeignKeyConstraint(['parent_dept_code'], ['department.dept_code'], name='fk_dept_parent'),
    )
    op.create_index('idx_department_parent_code', 'department', ['parent_dept_code'])

    # 2. Создаём users с внешним ключом на department
    op.create_table('users',
        sa.Column('user_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_name', sa.String(100), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('gender', sa.String(1), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('phone_work', sa.String(20), nullable=True),
        sa.Column('phone_mobile', sa.String(20), nullable=True),
        sa.Column('dept_code', sa.String(20), nullable=True),
        sa.Column('head_id', sa.BigInteger(), nullable=True),
        sa.Column('blocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('blocked_reason', sa.String(), nullable=True),
        sa.Column('blocked_by', sa.BigInteger(), nullable=True),
        sa.Column('block_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_history', JSON, nullable=True),
        sa.Column('temp_password', sa.String(255), nullable=True),
        sa.Column('temp_password_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_super_admin', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('user_name'),
        sa.ForeignKeyConstraint(['dept_code'], ['department.dept_code'], name='fk_users_dept_code'),
        sa.ForeignKeyConstraint(['head_id'], ['users.user_id'], name='fk_users_head_id'),
        sa.ForeignKeyConstraint(['blocked_by'], ['users.user_id'], name='fk_users_blocked_by'),
    )

    # Индексы для users
    op.create_index('idx_users_user_name', 'users', ['user_name'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_dept_code', 'users', ['dept_code'])
    op.create_index('idx_users_head_id', 'users', ['head_id'])
    op.create_index('idx_users_super_admin', 'users', ['is_super_admin'], postgresql_where=sa.text('is_super_admin = TRUE'))
    op.create_index('idx_users_locked_until', 'users', ['locked_until'])
    op.create_index('idx_users_deleted_at', 'users', ['deleted_at'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_users_blocked_at', 'users', ['blocked_at'], postgresql_where=sa.text('blocked_at IS NOT NULL'))
    op.create_index('idx_users_last_login', 'users', ['last_login_at'])
    op.create_index('idx_users_gender', 'users', ['gender'])
    op.create_index('idx_users_birth_date', 'users', ['birth_date'])
    op.create_index('idx_users_phone_work', 'users', ['phone_work'], postgresql_where=sa.text('phone_work IS NOT NULL'))
    op.create_index('idx_users_phone_mobile', 'users', ['phone_mobile'], postgresql_where=sa.text('phone_mobile IS NOT NULL'))

def downgrade():
    op.drop_table('users')
    op.drop_table('department')
