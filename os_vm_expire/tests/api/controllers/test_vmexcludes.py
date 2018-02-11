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

from os_vm_expire.model import models

from os_vm_expire.model import repositories
from os_vm_expire.tests import utils


class WhenTestingVmExcludesResource(utils.OsVMExpireAPIBaseTestCase):

    def setUp(self):
        super(WhenTestingVmExcludesResource, self).setUp()

    def tearDown(self):
        super(WhenTestingVmExcludesResource, self).tearDown()
        repo = repositories.get_vmexpire_repository()
        repo.delete_all_entities()
        repositories.commit()
        repo = repositories.get_vmexclude_repository()
        repo.delete_all_entities()
        repositories.commit()

    def test_can_get_vmexcludes(self):
        entity = create_vmexclude_model(exclude_type=0)
        create_vmexclude(entity)
        exclude_id = entity.exclude_id
        exclude_type = entity.exclude_type
        _get_resp = self.app.get('/12345project/vmexcludes/')
        self.assertEqual(200, _get_resp.status_int)
        self.assertIn('vmexcludes', _get_resp.json)
        self.assertEqual(len(_get_resp.json['vmexcludes']), 1)
        self.assertEqual(
            _get_resp.json['vmexcludes'][0]['exclude_id'],
            exclude_id
            )
        self.assertEqual(
            _get_resp.json['vmexcludes'][0]['exclude_type'],
            exclude_type
            )

    def test_can_get_vmexclude(self):
        entity = create_vmexclude_model()
        instance = create_vmexclude(entity)
        _get_resp = self.app.get(
            '/12345project/vmexcludes/' + instance.id
            )
        self.assertEqual(200, _get_resp.status_int)
        self.assertIn('vmexclude', _get_resp.json)
        self.assertEqual(
            _get_resp.json['vmexclude']['exclude_id'],
            entity.exclude_id)

    def test_can_create_vmexclude(self):
        entity = create_vmexclude_model(exclude_type=1)
        _get_resp = self.app.post_json(
            '/12345/vmexcludes/',
            {
                'id': entity.exclude_id,
                'type': 'project'
            },
            headers={'Content-Type': 'application/json'}
            )
        self.assertEqual(202, _get_resp.status_int)
        self.assertIn('vmexclude', _get_resp.json)
        self.assertEqual(
            _get_resp.json['vmexclude']['exclude_id'],
            entity.exclude_id
            )
        self.assertEqual(
            _get_resp.json['vmexclude']['exclude_type'],
            entity.exclude_type
            )
        _get_existing_resp = self.app.get(
            '/12345project/vmexcludes/' + _get_resp.json['vmexclude']['id']
        )
        self.assertEqual(200, _get_existing_resp.status_int)
        self.assertIn('vmexclude', _get_existing_resp.json)
        self.assertEqual(
            _get_resp.json['vmexclude']['exclude_id'],
            entity.exclude_id
            )

    def test_can_delete_vmexclude(self):
        entity = create_vmexclude_model()
        instance = create_vmexclude(entity)
        _get_resp = self.app.delete(
            '/12345project/vmexcludes/' + instance.id,
            headers={'Content-Type': 'application/json'}
            )
        self.assertEqual(204, _get_resp.status_int)
        _get_resp = self.app.get('/12345project/vmexcludes/')
        self.assertEqual(200, _get_resp.status_int)
        self.assertIn('vmexcludes', _get_resp.json)
        self.assertEqual(len(_get_resp.json['vmexcludes']), 0)


def create_vmexclude_model(prefix=None, exclude_type=0):
    if not prefix:
        prefix = '12345'
    entity = models.VmExclude()
    entity.exclude_id = prefix
    entity.exclude_type = exclude_type

    return entity


def create_vmexclude(entity):
    repo = repositories.get_vmexclude_repository()
    instance = repo.create_exclude(entity)
    repositories.commit()
    return instance
