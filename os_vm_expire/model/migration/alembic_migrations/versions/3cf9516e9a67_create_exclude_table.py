# Copyright 2017 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

"""create exclude table

Revision ID: 3cf9516e9a67
Revises: newton
Create Date: 2017-12-27 17:23:22.288802

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3cf9516e9a67'
down_revision = 'newton'


def upgrade():
    ctx = op.get_context()
    con = op.get_bind()
    table_exists = ctx.dialect.has_table(con, 'vmexclude')
    if not table_exists:
        op.create_table(
            'vmexclude',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted', sa.Boolean(), nullable=False),
            sa.Column('exclude_id', sa.String(255), index=False, nullable=False),
            sa.Column('exclude_type', sa.Integer, index=False, nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
