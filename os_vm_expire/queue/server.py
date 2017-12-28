# Copyright (c) 2013-2014 Rackspace, Inc.
#               2017 IRISA
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
Server-side (i.e. worker side) classes and logic.
"""
import datetime
import functools
import json
import requests
import time

import oslo_messaging

from oslo_service import service

from os_vm_expire.common import config
from os_vm_expire.common import utils
from os_vm_expire.model import models
from os_vm_expire.model import repositories

CONF = config.CONF

LOG = utils.getLogger(__name__)


def get_identity_token():
    conf_worker = config.CONF.worker
    ks_uri = conf_worker.auth_uri

    auth = {
        'auth': {
            'scope':
                {'project': {
                    'name': conf_worker.admin_service,
                    'domain':
                        {
                            'name': conf_worker.admin_project_domain_name
                        }
                    }
                 },
            'identity': {
                    'password': {
                        'user': {
                            'domain': {
                                'name': conf_worker.admin_user_domain_name
                            },
                            'password': conf_worker.admin_password,
                            'name': conf_worker.admin_user
                        }
                    },
                    'methods': ['password']
                }
        }
    }
    r = requests.post(ks_uri + '/auth/tokens', json=auth)
    if 'X-Subject-Token' not in r.headers:
        LOG.error('Could not get authorization')
        return None
    token = r.headers['X-Subject-Token']
    return token


def get_project_domain(project_id):
    token = get_identity_token()
    if not token:
        return None
    conf_worker = config.CONF.worker
    ks_uri = conf_worker.auth_uri
    headers = {
        'X-Auth-Token': token,
        'Content-Type': 'application/json'
    }
    r = requests.get(ks_uri + '/projects/' + str(project_id), headers=headers)
    if not r.status_code == 200:
        LOG.error('Failed to get domain_id for project ' + str(project_id))
        return None
    project = r.json()
    domain_id = project['project']['domain_id']
    return domain_id


def find_function_name(func, if_no_name=None):
    """Returns pretty-formatted function name."""
    return getattr(func, '__name__', if_no_name)


def transactional(fn):
    """Provides request-scoped database transaction support to tasks."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        fn_name = find_function_name(fn, if_no_name='???')

        # Manage session/transaction.
        try:
            fn(*args, **kwargs)
            repositories.commit()
            LOG.debug("Completed worker task (post-commit): '%s'", fn_name)
        except Exception:
            """NOTE: Wrapped functions must process with care!
            Exceptions that reach here will revert the entire transaction,
            including any updates made to entities such as setting error
            codes and error messages.
            """
            LOG.exception("Problem seen processing worker task: '%s'",
                          fn_name
                          )
            repositories.rollback()
        finally:
            repositories.clear()

    return wrapper


def monitored(fn):  # pragma: no cover
    """Provides monitoring capabilities for task methods."""

    return fn


class Tasks(object):
    """Tasks that can be invoked asynchronously.

    Only place task methods and implementations on this class, as they can be
    called directly from the client side for non-asynchronous standalone
    single-node operation.
    If a new method is added that can be retried, please also add its method
    name to MAP_RETRY_TASKS above.
    The TaskServer class below extends this class to implement a worker-side
    server utilizing Oslo messaging's RPC server. This RPC server can invoke
    methods on itself, which include the methods in this class.
    """

    @monitored
    @transactional
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        if event_type == 'instance.create.end':
            LOG.debug(event_type + ':' + payload['nova_object.data']['uuid'])
            repo = repositories.get_vmexpire_repository()
            instance = None
            instance_uuid = str(payload['nova_object.data']['uuid'])
            try:
                instance = repo.get_by_instance(instance_uuid)
            except Exception:
                LOG.debug("Fine, instance does not already exists")
            if instance:
                LOG.warn("InstanceAlreadyExists:" +
                         instance_uuid +
                         ", deleting first"
                         )
                repo.delete_entity_by_id(entity_id=instance.id)
            entity = models.VmExpire()
            entity.instance_id = instance_uuid
            if payload['nova_object.data']['display_name']:
                display_name = payload['nova_object.data']['display_name']
                entity.instance_name = display_name
            else:
                entity.instance_name = instance_uuid
            entity.project_id = payload['nova_object.data']['tenant_id']
            entity.user_id = payload['nova_object.data']['user_id']
            entity.expire = int(
                time.mktime(datetime.datetime.now().timetuple()) +
                (CONF.max_vm_duration * 3600 * 24)
                )
            entity.notified = False
            entity.notified_last = False

            project_domain = None
            try:
                project_domain = get_project_domain(entity.project_id)
            except Exception:
                LOG.exception('Failed to get domain for project')

            exclude_repo = repositories.get_vmexclude_repository()
            if project_domain:
                exclude_id = exclude_repo.get_exclude_by_id(project_domain)
                if exclude_id:
                    LOG.debug('domain %s is excluded, skipping' % (project_domain))
                    return
            exclude_id = exclude_repo.get_exclude_by_id(entity.project_id)
            if exclude_id:
                LOG.debug('project %s is excluded, skipping' % (entity.project_id))
                return
            exclude_id = exclude_repo.get_exclude_by_id(entity.user_id)
            if exclude_id:
                LOG.debug('user %s is excluded, skipping' % (entity.user_id))
                return

            instance = repo.create_from(entity)
            LOG.debug("NewInstanceExpiration:" + instance_uuid)
        elif event_type == 'instance.delete.end':
            instance_uuid = str(payload['nova_object.data']['uuid'])
            LOG.debug(event_type + ':' + instance_uuid)
            repo = repositories.get_vmexpire_repository()
            try:
                instance = repo.get_by_instance(instance_uuid)
                repo.delete_entity_by_id(entity_id=instance.id)
                LOG.debug("Delete id:" + instance.id)
            except Exception:
                LOG.warn('Failed to delete: ' + instance_uuid)

        LOG.debug(publisher_id)
        LOG.debug(event_type)
        LOG.debug(str(metadata))
        LOG.debug(json.dumps(payload, indent=4))

    def warn(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.debug(json.dumps(payload, indent=4))

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.debug(json.dumps(payload, indent=4))


class TaskServer(Tasks, service.Service):
    """Server to process asynchronous tasking from API nodes.

    This server is an Oslo service that exposes task methods that can
    be invoked from the Barbican API nodes. It delegates to an Oslo
    RPC messaging server to invoke methods asynchronously on this class.
    Since this class also extends the Tasks class above, its task-based
    methods are hence available to the RPC messaging server.
    """
    def __init__(self):
        super(TaskServer, self).__init__()

        # Setting up db engine to avoid lazy initialization
        repositories.setup_database_engine_and_factory()

        transport = oslo_messaging.get_transport(CONF)

        conf_opts = getattr(CONF, config.KS_NOTIFICATIONS_GRP_NAME)
        targets = [
            oslo_messaging.Target(
                topic=conf_opts.topic,
                exchange=conf_opts.control_exchange
                )
        ]
        endpoints = [self]
        self._server = oslo_messaging.get_notification_listener(
            transport,
            targets,
            endpoints,
            pool=conf_opts.pool_name
            )

    def start(self):
        LOG.info("Starting the TaskServer")
        self._server.start()
        super(TaskServer, self).start()

    def stop(self):
        LOG.info("Halting the TaskServer")
        super(TaskServer, self).stop()
        self._server.stop()
