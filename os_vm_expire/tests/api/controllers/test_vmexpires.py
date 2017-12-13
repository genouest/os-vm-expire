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
import os
import time

from os_vm_expire.tests import utils
from os_vm_expire.model import repositories
from os_vm_expire.model import models

class WhenTestingVmExpiresResource(utils.OsVMExpireAPIBaseTestCase):

    def setUp(self):
        super(WhenTestingVmExpiresResource, self).setUp()

    def tearDown(self):
        super(WhenTestingVmExpiresResource, self).tearDown()
        repo = repositories.get_vmexpire_repository()
        repo.delete_all_entities()
        repositories.commit()

    def test_can_get_vmexpires(self):
        entity = create_vmexpire_model()
        create_vmexpire(entity)
        _get_resp = self.app.get('/' + entity.project_id + '/vmexpires/')
        self.assertEqual(200, _get_resp.status_int)
        self.assertIn('vmexpires', _get_resp.json)
        self.assertEqual(len(_get_resp.json['vmexpires']),1)
        self.assertEqual(
            _get_resp.json['vmexpires'][0]['instance_id'],
            entity.instance_id
            )

    def test_can_get_vmexpire(self):
        entity = create_vmexpire_model()
        instance = create_vmexpire(entity)
        _get_resp = self.app.get(
            '/'+ entity.project_id +'/vmexpires/' + instance.id
            )
        self.assertEqual(200, _get_resp.status_int)
        self.assertIn('vmexpire', _get_resp.json)
        self.assertEqual(
            _get_resp.json['vmexpire']['instance_id'],
            entity.instance_id)

    def test_can_extend_vmexpire(self):
        entity = create_vmexpire_model()
        instance = create_vmexpire(entity)
        _get_existing_resp = self.app.get(
            '/'+ entity.project_id +'/vmexpires/' + instance.id
            )
        _get_resp = self.app.put(
            '/'+ entity.project_id +'/vmexpires/' + instance.id,
            headers={'Content-Type': 'application/json'}
            )
        self.assertEqual(202, _get_resp.status_int)
        self.assertIn('vmexpire', _get_resp.json)
        self.assertEqual(
            _get_resp.json['vmexpire']['instance_id'],
            _get_existing_resp.json['vmexpire']['instance_id']
            )
        prev_expire =  _get_existing_resp.json['vmexpire']['expire']
        new_expire = _get_resp.json['vmexpire']['expire']
        self.assertTrue(
            new_expire > prev_expire
            )

    def test_can_delete_vmexpire(self):
        entity = create_vmexpire_model()
        instance = create_vmexpire(entity)
        _get_resp = self.app.delete(
            '/'+ entity.project_id +'/vmexpires/' + instance.id,
            headers={'Content-Type': 'application/json'}
            )
        self.assertEqual(204, _get_resp.status_int)
        _get_resp = self.app.get('/' + entity.project_id + '/vmexpires/')
        self.assertEqual(200, _get_resp.status_int)
        self.assertIn('vmexpires', _get_resp.json)
        self.assertEqual(len(_get_resp.json['vmexpires']),0)

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
