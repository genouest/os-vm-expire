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
import datetime
import mock
import time

from os_vm_expire.cmd.cleaner import check as cleaner_check
from os_vm_expire.model import models
from os_vm_expire.model import repositories
# from os_vm_expire.cmd.cleaner import send_email as cleaner_send_email
from os_vm_expire.tests import utils


class MockResponse(object):
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = {
            'X-Subject-Token': 'XXX'
        }

    def json(self):
        return self.json_data


def mocked_requests_get(*args, **kwargs):
    return MockResponse(None, 404)


def mocked_requests_post(*args, **kwargs):
    return MockResponse(None, 404)


def mocked_email(*args, **kwargs):
    return True


def mocked_delete_vm(instance_id, project_id, token):
    return True


class WhenTestingVmExpiresResource(utils.OsVMExpireAPIBaseTestCase):

    def setUp(self):
        super(WhenTestingVmExpiresResource, self).setUp()

    def tearDown(self):
        super(WhenTestingVmExpiresResource, self).tearDown()
        repo = repositories.get_vmexpire_repository()
        repo.delete_all_entities()
        repositories.commit()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    @mock.patch('os_vm_expire.cmd.cleaner.send_email', side_effect=mocked_email)
    def test_vm_expire_not_cleaned(self, mock_get, mock_post, mock_email):
        entity = create_vmexpire_model('12345')
        create_vmexpire(entity)
        cleaner_check(None)
        db_entity = get_vmexpire(entity.id)
        self.assertTrue(db_entity.id == entity.id)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    @mock.patch('os_vm_expire.cmd.cleaner.delete_vm', side_effect=mocked_delete_vm)
    @mock.patch('os_vm_expire.cmd.cleaner.send_email', side_effect=mocked_email)
    def test_vm_expire_cleaned(self, mock_get, mock_post, mock_delete, mock_email):
        entity = create_vmexpire_model('12345')
        instance = create_vmexpire(entity)
        instance.expire = 1
        instance.save()
        repositories.commit()
        cleaner_check(None)
        db_entity = get_vmexpire(entity.id)
        self.assertTrue(db_entity.notified)
        self.assertFalse(db_entity.notified_last)
        cleaner_check(None)
        self.assertTrue(db_entity.notified)
        self.assertTrue(db_entity.notified_last)
        cleaner_check(None)
        found = False
        try:
            db_entity = get_vmexpire(entity.id)
            found = True
        except Exception:
            found = False
        self.assertFalse(found)


def create_vmexpire_model(prefix=None):
    if not prefix:
        prefix = '12345'
    entity = models.VmExpire()
    entity.user_id = prefix + 'user'
    entity.project_id = prefix + 'project'
    entity.instance_id = prefix + 'instance'
    entity.instance_name = prefix
    entity.notified = False
    entity.notified_last = False
    entity.expire = time.mktime(datetime.datetime.now().timetuple())
    return entity


def create_vmexpire(entity):
    repo = repositories.get_vmexpire_repository()
    instance = repo.create_from(entity)
    repositories.commit()
    return instance


def get_vmexpire(entity_id):
    repo = repositories.get_vmexpire_repository()
    instance = repo.get(entity_id=entity_id)
    return instance
