# Copyright (c) 2013-2014 Rackspace, Inc.
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
import time
import functools
import json

from oslo_service import service

from os_vm_expire.common import utils
from os_vm_expire.model import models
from os_vm_expire.model import repositories
from os_vm_expire import queue
from os_vm_expire.common import config

CONF = config.CONF

LOG = utils.getLogger(__name__)


# Maps the common/shared RetryTasks (returned from lower-level business logic
# and plugin processing) to top-level RPC tasks in the Tasks class below.



def find_function_name(func, if_no_name=None):
    """Returns pretty-formatted function name."""
    return getattr(func, '__name__', if_no_name)


def transactional(fn):
    """Provides request-scoped database transaction support to tasks."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        fn_name = find_function_name(fn, if_no_name='???')

        if not queue.is_server_side():
            # Non-server mode directly invokes tasks.
            fn(*args, **kwargs)
            LOG.info("Completed worker task: '%s'", fn_name)
        else:
            # Manage session/transaction.
            try:
                fn(*args, **kwargs)
                repositories.commit()
                LOG.info("Completed worker task (post-commit): '%s'", fn_name)
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
            LOG.info(event_type + ':' + payload['nova_object.data']['uuid'])
            repo = repositories.get_vmexpire_repository()
            instance = None
            try:
                instance = repo.get_by_instance(str(payload['nova_object.data']['uuid']))
            except Exception:
                LOG.debug("Fine, instance does not already exists")
            if instance:
                LOG.warn("InstanceAlreadyExists:" + payload['nova_object.data']['uuid']+ ", deleting first")
                repo.delete_entity_by_id(entity_id=instance.id)
            entity = models.VmExpire()
            entity.instance_id = payload['nova_object.data']['uuid']
            if payload['nova_object.data']['display_name']:
                entity.instance_name = payload['nova_object.data']['display_name']
            entity.project_id = payload['nova_object.data']['tenant_id']
            entity.user_id = payload['nova_object.data']['user_id']
            entity.expire = int(time.mktime(datetime.datetime.now().timetuple()) + CONF.max_vm_duration * 3600 * 24)
            entity.notified = False
            #repo = repositories.get_vmexpire_repository()
            instance = repo.create_from(entity)
            repositories.commit();
            LOG.debug("NewInstanceExpiration:" + payload['nova_object.data']['uuid'])
        elif event_type == 'instance.delete.end':
            LOG.info(event_type + ':' + payload['nova_object.data']['uuid'])
            repo = repositories.get_vmexpire_repository()
            try:
                instance = repo.get_by_instance(str(payload['nova_object.data']['uuid']))
                repo.delete_entity_by_id(entity_id=instance.id)
                repositories.commit();
                LOG.debug("Delete id:" + instance.id)
            except Exception as e:
                LOG.warn('Failed to delete: ' + payload['nova_object.data']['uuid'])

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

        # This property must be defined for the 'endpoints' specified below,
        #   as the oslo_messaging RPC server will ask for it.

        # Listens to versioned_notification
        # Pb is messages would be dispatched among the different listeners (ceilometer etc...)
        # Solution is to use directly kombu with a routing_key
        # Ex:
        # nova_x = Exchange('nova', type='topic', durable=False)
        # info_q = Queue('osvmexpire-worker', exchange=nova_x, durable=False,
        #       routing_key='notifications.info')
        self.target = queue.get_notification_target()
        #self.target = queue.get_target()

        # Create an oslo RPC server, that calls back on to this class
        #   instance to invoke tasks, such as 'process_order()' on the
        #   extended Tasks class above.
        #self._server = queue.get_server(target=self.target,
        #                                endpoints=[self])
        self._server = queue.get_notification_server(targets= [self.target],
                                                     endpoints=[self])

        #transport = oslo_messaging.get_transport(queue.CONF)
        #targets = [ oslo_messaging.Target(topic='notifications') ]
        #endpoints = [ self ]
        #self._server = oslo_messaging.get_notification_listener(transport, targets, endpoints)

    def start(self):
        LOG.info("Starting the TaskServer")
        self._server.start()
        super(TaskServer, self).start()

    def stop(self):
        LOG.info("Halting the TaskServer")
        super(TaskServer, self).stop()
        self._server.stop()
