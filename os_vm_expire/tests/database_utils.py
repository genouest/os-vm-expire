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
Supports database/repositories oriented unit testing.
Warning: Do not merge this content with the utils.py module, as doing so will
break the DevStack functional test discovery process.
"""
import datetime
import time

# from sqlalchemy.engine import Engine
# from sqlalchemy import event

from os_vm_expire.model.migration import commands
from os_vm_expire.model import models
from os_vm_expire.model import repositories
from oslo_db import options
import oslotest.base as oslotest


def create_vmexpire(instance=None, session=None):
    expire = models.VmExpire()
    expire.project_id = instance.project_id
    expire.instance_id = instance.instance_id
    expire.instance_name = instance.instance_name
    expire.user_id = instance.user_id
    expire.expire = time.mktime(datetime.datetime.now().timetuple()) + 2 * 3600 * 24
    expire.notified = False
    expire.notified_last = False
    container_repo = repositories.get_vmexpire_repository()
    container_repo.create_from(expire, session=session)
    return expire


def create_vmexclude(exclude_id=None, exclude_type=0, session=None):
    exclude = models.VmExclude()
    exclude.exclude_id = exclude_id
    exclude.exclude_type = exclude_type
    container_repo = repositories.get_vmexclude_repository()
    container_repo.create_exclude(exclude, session=session)
    return exclude


def setup_in_memory_db():
    # Ensure we are using in-memory SQLite database, and creating tables.
    options.set_defaults(repositories.CONF, connection='sqlite:///test.db')

    repositories.CONF.set_override("debug", True)
    config = commands.init_config()
    config.osvmexpire = repositories.CONF

    # Ensure the connection is completely closed, so any previous in-memory
    # database can be removed prior to starting the next test run.
    repositories.hard_reset()
    commands.upgrade(config=config, to_version='head')
    # Start the in-memory database, creating required tables.
    repositories.start()


def in_memory_cleanup():
    repositories.clear()


def get_session():
    return repositories.get_session()


class RepositoryTestCase(oslotest.BaseTestCase):
    """Base test case class for in-memory database unit tests.

    Database/Repository oriented unit tests should *not* modify the global
    state in the os_vm_expire/model/repositories.py module, as this can lead to
    hard to debug errors. Instead only utilize methods in this fixture.
    Also, database-oriented unit tests extending this class MUST NO INVOKE
    the repositories.start()/clear()/hard_reset() methods!*, otherwise *VERY*
    hard to debug 'Broken Pipe' errors could result!
    """
    def setUp(self):
        super(RepositoryTestCase, self).setUp()
        setup_in_memory_db()

        # Clean up once tests are completed.
        self.addCleanup(in_memory_cleanup)
