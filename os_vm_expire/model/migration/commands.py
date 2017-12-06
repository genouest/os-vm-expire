# Copyright (c) 2013-2014 Rackspace, Inc.
#               2017 O. Sallou, IRISA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Interface to the os_vm_expire migration process and environment.
Available Alembic commands are detailed here:
https://alembic.readthedocs.org/en/latest/api.html#module-alembic.command
"""

import os

from alembic import command as alembic_command
from alembic import config as alembic_config

from os_vm_expire.common import config
from os_vm_expire.common import utils

LOG = utils.getLogger(__name__)


CONF = config.CONF


def init_config():
    """Initialize and return the Alembic configuration."""

    config = alembic_config.Config(
        os.path.join(os.path.dirname(__file__), 'alembic.ini')
    )
    config.set_main_option('script_location',
                           'os_vm_expire.model.migration:alembic_migrations')
    return config


def upgrade(to_version='head', config=None):
    """Upgrade to the specified version."""
    alembic_cfg = config or init_config()
    alembic_command.upgrade(alembic_cfg, to_version)


def history(verbose, config=None):
    alembic_cfg = config or init_config()
    alembic_command.history(alembic_cfg, verbose=verbose)


def current(verbose, config=None):
    alembic_cfg = config or init_config()
    alembic_command.current(alembic_cfg, verbose=verbose)


def stamp(to_version='head', config=None):
    """Stamp the specified version, with no migration performed."""
    alembic_cfg = config or init_config()
    alembic_command.stamp(alembic_cfg, to_version)


def generate(autogenerate=True, message='generate changes', config=None):
    """Generate a version file."""
    alembic_cfg = config or init_config()
    alembic_command.revision(alembic_cfg, message=message,
                             autogenerate=autogenerate)
