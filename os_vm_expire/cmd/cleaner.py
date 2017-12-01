#!/usr/bin/env python

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
Osvmexpire worker server.
"""

import eventlet
import os
import sys
import time
import datetime

# Oslo messaging RPC server uses eventlet.
eventlet.monkey_patch()

# 'Borrowed' from the Glance project:
# If ../barbican/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'os_vm_expire', '__init__.py')):
    sys.path.insert(0, possible_topdir)


from os_vm_expire.common import config
from os_vm_expire import version
from os_vm_expire.common import utils
from os_vm_expire.model import repositories

from oslo_log import log
from oslo_service import service


import futurist
from futurist import periodics
import requests

LOG = utils.getLogger(__name__)


def fail(returncode, e):
    sys.stderr.write("ERROR: {0}\n".format(e))
    sys.exit(returncode)


def delete_vm(instance_id, project_id, token):
    ''' TODO
    TODO TODO TODO
    conf in [DEFAULT]
    nova_url = http://controller.genouest.org:8774/v2.1
    '''
    # TODO
    LOG.error('Not yet implemented')
    nova_url = config.CONF.nova_url
    LOG.debug('Nova URI:' + nova_url)
    headers = {'X-Auth-Token': token, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    r = requests.delete(nova_url + '/' + project_id + '/servers/' + instance_id, headers=headers)
    if r.status_code != 204:
        LOG.error('Failed to delete instance ' + str(instance_id))
        return False
    else:
        return True

def get_identity_token():
    '''
    [keystone_authtoken]
    auth_uri = http://controller:5000/v3.0
    identity_uri = http://controller:35357
    admin_tenant_name = service
    admin_user = os_vm_expire
    admin_password = XYZ
    admin_user_domain_name = default
    admin_project_domain_name = default
    '''
    ks_uri = config.CONF.cleaner.auth_uri

    auth={"auth":
             {"scope":
                 {'project': {
                    "name": config.CONF.cleaner.admin_service,
                    "domain":
                        {
                          "name": config.CONF.cleaner.admin_project_domain_name
                        }
                    }
                 },
              "identity": {
                  "password": {
                        "user": {
                              "domain": {"name": config.CONF.cleaner.admin_user_domain_name},
                              "password": config.CONF.cleaner.admin_password,
                              "name": config.CONF.cleaner.admin_user
                        }
                  },
                  "methods": ["password"]
                  }
             }
         }
    r = requests.post(ks_uri + '/auth/tokens', json=auth)
    if 'X-Subject-Token' not in r.headers:
        LOG.error('Could not get authorization')
        return None
    token = r.headers['X-Subject-Token']
    return token



@periodics.periodic(60)
def check(started_at):
    token = get_identity_token()
    LOG.info("check instances")
    repo = repositories.get_vmexpire_repository()
    now = int(time.mktime(datetime.datetime.now().timetuple()))
    entities = repo.get_entities(expiration_filter=now)
    for entity in entities:
        res = delete_vm(entity.instance_id, entity.project_id, token)
        if res:
            repo.delete_entity_by_id(entity_id=entity.id)
            repositories.commit()


class CleanerServer(service.Service):

    def __init__(self):
        super(CleanerServer, self).__init__(config.CONF)
        repositories.setup_database_engine_and_factory()
        started_at = time.time()
        nova_url = ''
        callables = [(check,(started_at,),{})]
        self.w = periodics.PeriodicWorker(callables)

    def start(self):
        LOG.info("Starting the CleanerServer")
        self.w.start()
        super(CleanerServer, self).start()

    def stop(self):
        LOG.info("Halting the CleanerServer")
        self.w.stop()
        super(CleanerServer, self).stop()


def main():
    try:
        config.CONF(sys.argv[1:], project='os-vm-expire',
             version=version.version_info.version_string)

        # Import and configure logging.
        log.setup(config.CONF, 'osvmexpire')
        LOG = log.getLogger(__name__)
        LOG.debug("Booting up os-vm-expire cleaner node...")

        service.launch(
            config.CONF,
            CleanerServer(),
            workers=1
        ).wait()

    except RuntimeError as e:
        fail(1, e)

if __name__ == '__main__':
    main()
