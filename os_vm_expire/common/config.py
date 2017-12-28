# Copyright (c) 2013-2014 Rackspace, Inc.
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
Configuration setup for os-vm-expire.
"""

import logging
import os

from oslo_config import cfg
from oslo_log import log
from oslo_middleware import cors
from oslo_service import _options

from os_vm_expire import i18n as u
import os_vm_expire.version


MAX_VM_DURATION_DAYS = 60
MAX_VM_EXTEND_DAYS = 30
MAX_VM_TOTAL_DURATION_DAYS = 365

KS_NOTIFICATIONS_GRP_NAME = "nova_notifications"

mail_opt_group = cfg.OptGroup(name='smtp',
                              title='SMTP mail Options')

mail_opts = [
    cfg.StrOpt('email_smtp_host',
               default='localhost',
               help=u._("SMTP hostname")),
    cfg.IntOpt('email_smtp_port',
               default=25,
               help=u._("SMTP port")),
    cfg.BoolOpt('email_smtp_tls',
                default=False,
                help=u._("SMTP tls use?")),
    cfg.StrOpt('email_smtp_user',
               default=None,
               help=u._("SMTP user")),
    cfg.StrOpt('email_smtp_password',
               default=None,
               help=u._("SMTP password")),
    cfg.StrOpt('email_smtp_from',
               default=None,
               help=u._("SMTP From mail origin")),
    cfg.StrOpt('email_smtp_copy_delete_notif_to',
               default=None,
               help=u._('Email where deletion notifications should be sent,'
                        ' leave empty if no copy is needed')),
]

cleaner_opt_group = cfg.OptGroup(name='cleaner',
                                 title='Cleaner Application Options')

cleaner_opts = [
    cfg.StrOpt('auth_uri',
               default='http://controller:5000/v3.0',
               help=u._("Openstack identity url")),
    cfg.StrOpt('nova_url',
               default='http://controller:8774/v2.1',
               help=u._("Openstack nova compute url")),
    cfg.StrOpt('admin_service',
               default='service',
               help=u._("service project name")),
    cfg.StrOpt('admin_user',
               default='os_vm_expire',
               help=u._("os-vm-expire service user id")),
    cfg.StrOpt('admin_password',
               help=u._("os-vm-expire service user password")),
    cfg.StrOpt('admin_user_domain_name',
               default='default',
               help=u._("os-vm-expire user domain name")),
    cfg.StrOpt('admin_project_domain_name',
               default='default',
               help=u._("os-vm-expire service project domain name")),
    cfg.IntOpt('notify_before_days',
               default=10,
               help=u._("os-vm-expire send notification before X days")),
    cfg.IntOpt('notify_before_days_last',
               default=2,
               help=u._("os-vm-expire send last notification before X days")),
]


worker_opt_group = cfg.OptGroup(name='worker',
                                title='Worker Application Options')

worker_opts = [
    cfg.StrOpt('auth_uri',
               default='http://controller:5000/v3.0',
               help=u._("Openstack identity url")),
    cfg.StrOpt('admin_service',
               default='service',
               help=u._("service project name")),
    cfg.StrOpt('admin_user',
               default='os_vm_expire',
               help=u._("os-vm-expire service user id")),
    cfg.StrOpt('admin_password',
               help=u._("os-vm-expire service user password")),
    cfg.StrOpt('admin_user_domain_name',
               default='default',
               help=u._("os-vm-expire user domain name")),
    cfg.StrOpt('admin_project_domain_name',
               default='default',
               help=u._("os-vm-expire service project domain name")),
]

queue_opt_group = cfg.OptGroup(name='queue',
                               title='Queue Application Options')

queue_opts = [
    cfg.BoolOpt('enable', default=False,
                help=u._('True enables queuing, False invokes '
                         'workers synchronously')),
    cfg.StrOpt('namespace', default='osvmexpire',
               help=u._('Queue namespace')),
    cfg.StrOpt('topic', default='osvmexpire.workers',
               help=u._('Queue topic name')),
    cfg.StrOpt('version', default='1.1',
               help=u._('Version of tasks invoked via queue')),
    cfg.StrOpt('server_name', default='osvmexpire.queue',
               help=u._('Server name for RPC task processing server')),
    cfg.IntOpt('asynchronous_workers', default=1,
               help=u._('Number of asynchronous worker processes')),
]


ks_queue_opt_group = cfg.OptGroup(name=KS_NOTIFICATIONS_GRP_NAME,
                                  title='Nova Notification Options')

ks_queue_opts = [
    cfg.BoolOpt('enable', default=False,
                help=u._('True enables nova notification listener '
                         ' functionality.')),
    cfg.StrOpt('control_exchange', default='nova',
               help=u._('The default exchange under which topics are scoped. '
                        'May be overridden by an exchange name specified in '
                        'the transport_url option.')),
    cfg.StrOpt('pool_name', default='os_vm_expire',
               help=u._('Pool notification to listen on nova exchange.'
                        'Messages in same pool will get messages distributed,'
                        ' while messages are copied over all pools')),
    cfg.StrOpt('topic', default='versioned_notifications',
               help=u._("nova notification queue topic name. This name "
                        "needs to match one of values mentioned in nova "
                        "deployment's 'notification_topics' configuration "
                        "e.g."
                        "    notification_topics=notifications.info, "
                        "    notifitions.error"
                        "Multiple servers may listen on a topic and messages "
                        "will be dispatched to one of the servers in a "
                        "round-robin fashion. That's why os-vm-expire service "
                        "should have its own dedicated notification queue so "
                        "that it receives all of nova notifications.")),
    cfg.BoolOpt('allow_requeue', default=False,
                help=u._('True enables requeue feature in case of notification'
                         ' processing error. Enable this only when underlying '
                         'transport supports this feature.')),
    cfg.StrOpt('version', default='1.0',
               help=u._('Version of tasks invoked via notifications')),
    cfg.IntOpt('thread_pool_size', default=10,
               help=u._('Define the number of max threads to be used for '
                        'notification server processing functionality.')),
]


context_opts = [
    cfg.StrOpt('admin_role', default='admin',
               help=u._('Role used to identify an authenticated user as '
                        'administrator.')),
    cfg.BoolOpt('allow_anonymous_access', default=False,
                help=u._('Allow unauthenticated users to access the API with '
                         'read-only privileges. This only applies when using '
                         'ContextMiddleware.')),
]

common_opts = [
    cfg.IntOpt('max_vm_duration',
               default=MAX_VM_DURATION_DAYS,
               help=u._("Maximum life duration of VM in days")),
    cfg.IntOpt('max_vm_extend',
               default=MAX_VM_EXTEND_DAYS,
               help=u._("Maximum life extend of VM in days")),
    cfg.IntOpt('max_vm_total_duration',
               default=MAX_VM_TOTAL_DURATION_DAYS,
               help=u._("Maximum life of VM in days, whatever the extends")),
]

host_opts = [
    cfg.StrOpt('host_href', default='http://localhost:9411',
               help=u._("Host name, for use in HATEOAS-style references Note: "
                        "Typically this would be the load balanced endpoint "
                        "that clients would use to communicate back with this "
                        "service. If a deployment wants to derive host from "
                        "wsgi request instead then make this blank. Blank is "
                        "needed to override default config value which is "
                        "'http://localhost:9411'")),
]


def list_opts():
    yield None, context_opts
    yield None, common_opts
    yield None, host_opts
    yield None, _options.eventlet_backdoor_opts
    yield queue_opt_group, queue_opts
    yield ks_queue_opt_group, ks_queue_opts
    yield cleaner_opt_group, cleaner_opts
    yield worker_opt_group, worker_opts
    yield mail_opt_group, mail_opts


# Flag to indicate  configuration is already parsed once or not
_CONFIG_PARSED_ONCE = False


def parse_args(conf, args=None, usage=None, default_config_files=None):
    global _CONFIG_PARSED_ONCE
    if default_config_files is None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if 'OSVMEXPIRE_CONFIG' in os.environ and os.environ['OSVMEXPIRE_CONFIG']:
            default_config_files = [os.environ['OSVMEXPIRE_CONFIG']]
        elif os.path.exists('/etc/os-vm-expire/osvmexpire.conf'):
            default_config_files = ['/etc/os-vm-expire/osvmexpire.conf']
        elif os.path.exists('osvmexpire.conf'):
            default_config_files = [
                'osvmexpire.conf'
            ]
        elif os.path.exists(
            os.path.join(dir_path, '../../etc/os-vm-expire/osvmexpire.conf')
        ):
            default_config_files = [
                os.path.join(
                    dir_path,
                    '../../etc/os-vm-expire/osvmexpire.conf'
                )
            ]
        elif os.path.exists(os.path.join(dir_path, '../../osvmexpire.conf')):
            default_config_files = [
                os.path.join(dir_path, '../../osvmexpire.conf')
            ]

    conf(args=args if args else [],
         project='os-vm-expire',
         prog='os-vm-expire',
         version=os_vm_expire.version.__version__,
         usage=usage,
         default_config_files=default_config_files)

    conf.pydev_debug_host = os.environ.get('PYDEV_DEBUG_HOST')
    conf.pydev_debug_port = os.environ.get('PYDEV_DEBUG_PORT')

    # Assign cfg.CONF handle to parsed configuration once at startup
    # only. No need to keep re-assigning it with separate plugin conf usage
    if not _CONFIG_PARSED_ONCE:
        cfg.CONF = conf
        _CONFIG_PARSED_ONCE = True


def new_config():
    conf = cfg.ConfigOpts()
    log.register_options(conf)
    conf.register_opts(context_opts)
    conf.register_opts(common_opts)
    conf.register_opts(host_opts)
    conf.register_opts(_options.eventlet_backdoor_opts)
    conf.register_opts(_options.periodic_opts)

    conf.register_opts(_options.ssl_opts, "ssl")
    conf.register_group(queue_opt_group)
    conf.register_opts(queue_opts, group=queue_opt_group)
    conf.register_group(ks_queue_opt_group)
    conf.register_opts(ks_queue_opts, group=ks_queue_opt_group)
    conf.register_opts(cleaner_opts, group=cleaner_opt_group)
    conf.register_opts(worker_opts, group=worker_opt_group)
    conf.register_opts(mail_opts, group=mail_opt_group)

    # Update default values from libraries that carry their own oslo.config
    # initialization and configuration.
    set_middleware_defaults()

    return conf


def setup_remote_pydev_debug():
    """Required setup for remote debugging."""

    if CONF.pydev_debug_host and CONF.pydev_debug_port:
        try:
            try:
                from pydev import pydevd
            except ImportError:
                import pydevd

            pydevd.settrace(CONF.pydev_debug_host,
                            port=int(CONF.pydev_debug_port),
                            stdoutToServer=True,
                            stderrToServer=True)
        except Exception:
            LOG.exception('Unable to join debugger, please '
                          'make sure that the debugger processes is '
                          'listening on debug-host \'%(debug-host)s\' '
                          'debug-port \'%(debug-port)s\'.',
                          {'debug-host': CONF.pydev_debug_host,
                           'debug-port': CONF.pydev_debug_port})
            raise


def set_middleware_defaults():
    """Update default configuration options for oslo.middleware."""
    cors.set_defaults(
        allow_headers=['X-Auth-Token',
                       'X-Openstack-Request-Id',
                       'X-Project-Id',
                       'X-Identity-Status',
                       'X-User-Id',
                       'X-Storage-Token',
                       'X-Domain-Id',
                       'X-User-Domain-Id',
                       'X-Project-Domain-Id',
                       'X-Roles'],
        expose_headers=['X-Auth-Token',
                        'X-Openstack-Request-Id',
                        'X-Project-Id',
                        'X-Identity-Status',
                        'X-User-Id',
                        'X-Storage-Token',
                        'X-Domain-Id',
                        'X-User-Domain-Id',
                        'X-Project-Domain-Id',
                        'X-Roles'],
        allow_methods=['GET',
                       'PUT',
                       'POST',
                       'DELETE',
                       'PATCH']
    )


CONF = new_config()
LOG = logging.getLogger(__name__)
parse_args(CONF)

# Adding global scope dict for all different configs created in various
# modules.
_CONFIGS = {}


def set_module_config(name, module_conf):
    """Each plugin can set its own conf instance with its group name."""
    _CONFIGS[name] = module_conf


def get_module_config(name):
    """Get handle to plugin specific config instance by its group name."""
    return _CONFIGS[name]
