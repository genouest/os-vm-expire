import datetime
import logging
import os
import sqlalchemy.orm as sa_orm
import time

from os_vm_expire.queue.server import Tasks
from os_vm_expire.tests import utils
from os_vm_expire.model import repositories
from os_vm_expire.model import models


class WhenTestingVmExpiresResource(utils.OsVMExpireAPIBaseTestCase):

    def setUp(self):
        super(WhenTestingVmExpiresResource, self).setUp()
        self.task = Tasks()

    def tearDown(self):
        super(WhenTestingVmExpiresResource, self).tearDown()
        repo = repositories.get_vmexpire_repository()
        repo.delete_all_entities()
        repositories.commit()

    def test_vm_create(self):
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
        self.assertEquals(expire.instance_id, create_msg['nova_object.data']['uuid'])
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
