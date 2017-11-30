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
    CLI interface for barbican management
"""

from __future__ import print_function

import argparse
import sys
import datetime

from tabulate import tabulate

from oslo_config import cfg
from oslo_log import log as logging

from os_vm_expire.common import config
from os_vm_expire.model import clean
from os_vm_expire.model.migration import commands
from os_vm_expire.model import repositories


import os_vm_expire.version

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


# Decorators for actions
def args(*args, **kwargs):
    def _decorator(func):
        func.__dict__.setdefault('args', []).insert(0, (args, kwargs))
        return func
    return _decorator


class DbCommands(object):
    """Class for managing osvmexpire database"""

    description = "Subcommands for managing osvmexpire database"

    clean_description = "Clean up soft deletions in the database"

    @args('--db-url', '-d', metavar='<db-url>', dest='dburl',
          help='osvmexpire database URL')
    @args('--min-days', '-m', metavar='<min-days>', dest='min_days', type=int,
          default=90, help='minimum number of days to keep soft deletions. '
          'default is %(default)s days.')
    @args('--verbose', '-V', action='store_true', dest='verbose',
          default=False, help='Show verbose information about the clean up.')
    @args('--log-file', '-L', metavar='<log-file>', type=str, default=None,
          dest='log_file', help='Set log file location. '
          'Default value for log_file can be found in barbican.conf')
    def clean(self, dburl=None, min_days=None, verbose=None, log_file=None):
        """Clean soft deletions in the database"""
        if dburl is None:
            dburl = CONF.sql_connection
        if log_file is None:
            log_file = CONF.log_file

        clean.clean_command(
            sql_url=dburl,
            min_num_days=min_days,
            verbose=verbose,
            log_file=log_file)

    revision_description = "Create a new database version file"

    @args('--db-url', '-d', metavar='<db-url>', dest='dburl',
          help='osvmexpire database URL')
    @args('--message', '-m', metavar='<message>', default='DB change',
          help='the message for the DB change')
    @args('--autogenerate', action="store_true", dest='autogen',
          default=False, help='autogenerate from models')
    def revision(self, dburl=None, message=None, autogen=None):
        """Process the 'revision' Alembic command."""
        if dburl is None:
            commands.generate(autogenerate=autogen, message=str(message),
                              sql_url=CONF.sql_connection)
        else:
            commands.generate(autogenerate=autogen, message=str(message),
                              sql_url=str(dburl))

    upgrade_description = "Upgrade to a future database version"

    @args('--db-url', '-d', metavar='<db-url>', dest='dburl',
          help='osvmexpire database URL')
    @args('--version', '-v', metavar='<version>', default='head',
          help='the version to upgrade to, or else '
          'the latest/head if not specified.')
    def upgrade(self, dburl=None, version=None):
        """Process the 'upgrade' Alembic command."""
        if dburl is None:
            commands.upgrade(to_version=str(version),
                             sql_url=CONF.sql_connection)
        else:
            commands.upgrade(to_version=str(version), sql_url=str(dburl))

    history_description = "Show database changset history"

    @args('--db-url', '-d', metavar='<db-url>', dest='dburl',
          help='osvmexpire database URL')
    @args('--verbose', '-V', action='store_true', dest='verbose',
          default=False, help='Show full information about the revisions.')
    def history(self, dburl=None, verbose=None):
        if dburl is None:
            commands.history(verbose, sql_url=CONF.sql_connection)
        else:
            commands.history(verbose, sql_url=str(dburl))

    current_description = "Show current revision of database"

    @args('--db-url', '-d', metavar='<db-url>', dest='dburl',
          help='osvmexpire database URL')
    @args('--verbose', '-V', action='store_true', dest='verbose',
          default=False, help='Show full information about the revisions.')
    def current(self, dburl=None, verbose=None):
        if dburl is None:
            commands.current(verbose, sql_url=CONF.sql_connection)
        else:
            commands.current(verbose, sql_url=str(dburl))


class VmExpireCommands(object):
    """Class for managing VM expiration"""

    description = "Subcommands for managing VM expiration"

    list_description = "Extend a VM duration"

    @args('--instance', metavar='<instance-id>', dest='instanceid', default=None,
          help='Instance id')
    def list(self, instanceid=None):
        repositories.setup_database_engine_and_factory()
        repo = repositories.get_vmexpire_repository()
        res = repo.get_by(instance_id=instanceid, project_id=None)
        headers = ['id', 'expire', 'instance.name', 'instance.id', 'project.id']
        data = []
        for instance in res:
            data.append([instance.id, datetime.datetime.fromtimestamp(instance.expire), instance.instance_name, instance.instance_id, instance.project_id])
        print(tabulate(data, headers, tablefmt="grid"))

        print("VM list successfully extended!")

    extend_description = "Extend a VM duration"

    @args('--id', metavar='<id>', dest='expirationid',
          help='Expiration id')
    def extend(self, expirationid):
        repositories.setup_database_engine_and_factory()
        repo = repositories.get_vmexpire_repository()
        repo.extend_vm(entity_id=expirationid)
        repositories.commit();
        print("VM expiration successfully extended!")

    remove_description = "Deletes a VM expiration"

    @args('--id', metavar='<expiration-id>', dest='expirationid',
          help='Expiration id')
    def remove(self, instanceid):
        repositories.setup_database_engine_and_factory()
        repo = repositories.get_vmexpire_repository()
        repo.delete_entity_by_id(entity_id=expirationid)
        repositories.commit();
        print("VM expiration successfully generated!")


CATEGORIES = {
    'db': DbCommands,
    'vm': VmExpireCommands,
}


# Modifying similar code from nova/cmd/manage.py
def methods_of(obj):
    """Get all callable methods of an object that don't start with underscore
    returns a list of tuples of the form (method_name, method)
    """

    result = []
    for fn in dir(obj):
        if callable(getattr(obj, fn)) and not fn.startswith('_'):
            result.append((fn, getattr(obj, fn),
                          getattr(obj, fn + '_description', None)))
    return result


# Shamelessly taking same code from nova/cmd/manage.py
def add_command_parsers(subparsers):
    """Add subcommand parser to oslo_config object"""

    for category in CATEGORIES:
        command_object = CATEGORIES[category]()

        desc = getattr(command_object, 'description', None)
        parser = subparsers.add_parser(category, description=desc)
        parser.set_defaults(command_object=command_object)

        category_subparsers = parser.add_subparsers(dest='action')

        for (action, action_fn, action_desc) in methods_of(command_object):
            parser = category_subparsers.add_parser(action,
                                                    description=action_desc)

            action_kwargs = []
            for args, kwargs in getattr(action_fn, 'args', []):
                # Assuming dest is the arg name without the leading
                # hyphens if no dest is supplied
                kwargs.setdefault('dest', args[0][2:])
                if kwargs['dest'].startswith('action_kwarg_'):
                    action_kwargs.append(
                        kwargs['dest'][len('action_kwarg_'):])
                else:
                    action_kwargs.append(kwargs['dest'])
                    kwargs['dest'] = 'action_kwarg_' + kwargs['dest']

                parser.add_argument(*args, **kwargs)

            parser.set_defaults(action_fn=action_fn)
            parser.set_defaults(action_kwargs=action_kwargs)

            parser.add_argument('action_args', nargs='*',
                                help=argparse.SUPPRESS)


# Define subcommand category
category_opt = cfg.SubCommandOpt('category',
                                 title='Command categories',
                                 help='Available categories',
                                 handler=add_command_parsers)


def main():
    """Parse options and call the appropriate class/method."""
    CONF = config.new_config()
    CONF.register_cli_opt(category_opt)

    try:
        logging.register_options(CONF)
        logging.setup(CONF, "osvmexpire-manage")
        cfg_files = cfg.find_config_files(project='os-vm-expire')

        CONF(args=sys.argv[1:],
             project='os-vm-expire',
             prog='os-vmexpire-manage',
             version=os_vm_expire.version.__version__,
             default_config_files=cfg_files)

    except RuntimeError as e:
        sys.exit("ERROR: %s" % e)

    # find sub-command and its arguments
    fn = CONF.category.action_fn
    fn_args = [arg.decode('utf-8') for arg in CONF.category.action_args]
    fn_kwargs = {}
    for k in CONF.category.action_kwargs:
        v = getattr(CONF.category, 'action_kwarg_' + k)
        if v is None:
            continue
        if isinstance(v, bytes):
            v = v.decode('utf-8')
        fn_kwargs[k] = v

    # call the action with the remaining arguments
    try:
        return fn(*fn_args, **fn_kwargs)
    except Exception as e:
        sys.exit("ERROR: %s" % e)

if __name__ == '__main__':
    main()
