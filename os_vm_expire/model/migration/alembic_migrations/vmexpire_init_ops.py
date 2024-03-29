# Copyright 2015 OpenStack Foundation
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

# Initial operations for agent management extension
# This module only manages the 'agents' table. Binding tables are created
# in the modules for relevant resources


from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'vmexpire',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.Column('instance_id',
                  sa.String(length=255),
                  index=True,
                  nullable=False),
        sa.Column('project_id',
                  sa.String(length=255),
                  index=True,
                  nullable=False),
        sa.Column('user_id',
                  sa.String(length=255),
                  index=False,
                  nullable=False),
        sa.Column('expire', sa.Integer, index=False, nullable=False),
        sa.Column('notified', sa.Boolean, index=False, nullable=False),
        sa.Column('notified_last', sa.Boolean, index=False, nullable=False),
        sa.Column('notified_time', sa.Integer, index=False, nullable=True),
        sa.Column('instance_name', sa.String(255), index=False, nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
