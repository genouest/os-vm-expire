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
import logging
import mock
# import sqlalchemy.orm as sa_orm
import time

from os_vm_expire.model import models
from os_vm_expire.model import repositories
from os_vm_expire.queue.server import Tasks
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


def mocked_get_project_domain(project_id):
    return '12345domain'


class WhenTestingVmExpiresResource(utils.OsVMExpireAPIBaseTestCase):

    def setUp(self):
        super(WhenTestingVmExpiresResource, self).setUp()
        self.task = Tasks()

    def tearDown(self):
        super(WhenTestingVmExpiresResource, self).tearDown()
        repo = repositories.get_vmexpire_repository()
        repo.delete_all_entities()
        repositories.commit()
        exclude_repo = repositories.get_vmexclude_repository()
        exclude_repo.delete_all_entities()
        repositories.commit()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    @mock.patch('os_vm_expire.queue.server.get_project_domain', side_effect=mocked_get_project_domain)
    def test_vm_create(self, mock_get, mock_post, mock_get_project_domain):
        create_msg = {
            'nova_object.data': {
                'uuid': '1-2-3-4-5',
                'display_name': '12345',
                'tenant_id': '12345project',
                'user_id': '12345user'
            }
        }
        self.task.info(None, 'mock', 'instance.create.end', create_msg, None)
        repo = repositories.get_vmexpire_repository()
        expire = repo.get_by_instance(create_msg['nova_object.data']['uuid'])
        self.assertEqual(expire.instance_id, create_msg['nova_object.data']['uuid'])
        self.assertTrue(expire.expire > 0)

    def test_vm_delete(self):
        self.test_vm_create()
        delete_msg = {
            'nova_object.data': {
                'uuid': '1-2-3-4-5',
                'display_name': '12345',
                'tenant_id': '12345project',
                'user_id': '12345user'
            }
        }
        self.task.info(None, 'mock', 'instance.delete.end', delete_msg, None)
        repo = repositories.get_vmexpire_repository()
        found = False
        try:
            expire = repo.get_by_instance(delete_msg['nova_object.data']['uuid'])
            if expire:
                found = True
        except Exception as e:
            logging.exception(e)
            found = False
        self.assertFalse(found)


class WhenTestingVmExcludesResource(utils.OsVMExpireAPIBaseTestCase):

    def setUp(self):
        super(WhenTestingVmExcludesResource, self).setUp()
        self.task = Tasks()

    def tearDown(self):
        super(WhenTestingVmExcludesResource, self).tearDown()
        repo = repositories.get_vmexpire_repository()
        repo.delete_all_entities()
        repositories.commit()
        exclude_repo = repositories.get_vmexclude_repository()
        exclude_repo.delete_all_entities()
        repositories.commit()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    @mock.patch('os_vm_expire.queue.server.get_project_domain', side_effect=mocked_get_project_domain)
    def test_vm_exclude_domain(self, mock_get, mock_post, mock_get_project_domain):
        create_msg = {
            'nova_object.data': {
                'uuid': '1-2-3-4-5',
                'display_name': '12345',
                'tenant_id': '12345project',
                'user_id': '12345user'
            }
        }
        entity = create_vmexclude_model('12345domain', 0)
        create_vmexclude(entity)
        self.task.info(None, 'mock', 'instance.create.end', create_msg, None)
        repo = repositories.get_vmexpire_repository()
        try:
            repo.get_by_instance(create_msg['nova_object.data']['uuid'])
        except Exception as e:
            logging.info('instance not found: ' + str(e))
        else:
            self.self.fail('domain is excluded, should not have been created')

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    @mock.patch('os_vm_expire.queue.server.get_project_domain', side_effect=mocked_get_project_domain)
    def test_vm_exclude_project(self, mock_get, mock_post, mock_get_project_domain):
        create_msg = {
            'nova_object.data': {
                'uuid': '1-2-3-4-5',
                'display_name': '12345',
                'tenant_id': '12345project',
                'user_id': '12345user'
            }
        }
        entity = create_vmexclude_model('12345project', 1)
        create_vmexclude(entity)
        self.task.info(None, 'mock', 'instance.create.end', create_msg, None)
        repo = repositories.get_vmexpire_repository()
        try:
            repo.get_by_instance(create_msg['nova_object.data']['uuid'])
        except Exception as e:
            logging.info('instance not found: ' + str(e))
        else:
            self.self.fail('domain is excluded, should not have been created')

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    @mock.patch('os_vm_expire.queue.server.get_project_domain', side_effect=mocked_get_project_domain)
    def test_vm_exclude_user(self, mock_get, mock_post, mock_get_project_domain):
        create_msg = {
            'nova_object.data': {
                'uuid': '1-2-3-4-5',
                'display_name': '12345',
                'tenant_id': '12345project',
                'user_id': '12345user'
            }
        }
        entity = create_vmexclude_model('12345user', 2)
        create_vmexclude(entity)
        self.task.info(None, 'mock', 'instance.create.end', create_msg, None)
        repo = repositories.get_vmexpire_repository()
        try:
            repo.get_by_instance(create_msg['nova_object.data']['uuid'])
        except Exception as e:
            logging.info('instance not found: ' + str(e))
        else:
            self.self.fail('domain is excluded, should not have been created')


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


def create_vmexclude_model(exclude_id, exclude_type):
    entity = models.VmExclude()
    entity.exclude_id = exclude_id
    entity.exclude_type = exclude_type
    return entity


def create_vmexclude(entity):
    repo = repositories.get_vmexclude_repository()
    instance = repo.create_exclude(entity)
    repositories.commit()
    return instance
