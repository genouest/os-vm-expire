# Copyright (c) 2013-2015 Rackspace, Inc.
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
API application handler for osvmexpire
"""
import os

from paste import deploy
import pecan


from oslo_log import log

from os_vm_expire.api.controllers import versions
from os_vm_expire.api import hooks
from os_vm_expire.common import config
from os_vm_expire.model import repositories

CONF = config.CONF


def build_wsgi_app(controller=None, transactional=False):
    """WSGI application creation helper

    :param controller: Overrides default application controller
    :param transactional: Adds transaction hook for all requests
    """
    request_hooks = [hooks.JSONErrorHook()]
    if transactional:
        request_hooks.append(hooks.OSVmExpireTransactionHook())

    # Create WSGI app
    wsgi_app = pecan.Pecan(
        controller or versions.AVAILABLE_VERSIONS[versions.DEFAULT_VERSION](),
        hooks=request_hooks,
        force_canonical=False
    )

    # clear the session created in controller initialization     60
    repositories.clear()
    return wsgi_app


def main_app(func):
    def _wrapper(global_config, **local_conf):

        # Configure oslo logging and configuration services.
        log.setup(CONF, 'osvmexpire')

        config.setup_remote_pydev_debug()

        # Initializing the database engine and session factory before the app
        # starts ensures we don't lose requests due to lazy initialization of
        # db connections.
        repositories.setup_database_engine_and_factory()

        wsgi_app = func(global_config, **local_conf)

        LOG = log.getLogger(__name__)
        LOG.info('os-vm-expire app created and initialized')
        return wsgi_app
    return _wrapper


@main_app
def create_main_app(global_config, **local_conf):
    """uWSGI factory method for the osvmexpire-API application."""
    # Setup app with transactional hook enabled
    return build_wsgi_app(versions.V1Controller(), transactional=True)


def create_version_app(global_config, **local_conf):
    wsgi_app = pecan.make_app(versions.VersionsController())
    return wsgi_app


def get_api_wsgi_script():
    conf = '/etc/os-vm-expire/osvmexpire-api-paste.ini'
    if not os.path.exists(conf):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        conf = os.path.join(
            dir_path,
            '../..',
            'etc/os-vm-expire/osvmexpire-api-paste.ini'
            )
    application = deploy.loadapp('config:%s' % conf)
    return application
