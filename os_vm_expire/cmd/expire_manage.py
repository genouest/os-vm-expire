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

from os_vm_expire.common import config
# from os_vm_expire.model import clean
# from os_vm_expire.model.migration import commands
from os_vm_expire.model.models import VmExclude
from os_vm_expire.model import repositories
import os_vm_expire.version

import argparse
import datetime
import prettytable
import six
import sys
import time

from oslo_config import cfg
from oslo_db import options
from oslo_log import log as logging
from oslo_utils import encodeutils


CONF = cfg.CONF
options.set_defaults(CONF)
LOG = logging.getLogger(__name__)


# Decorators for actions
def args(*args, **kwargs):
    def _decorator(func):
        func.__dict__.setdefault('args', []).insert(0, (args, kwargs))
        return func
    return _decorator


class VmExcludeCommands(object):
    """Class for managing VM excludes"""

    EXCLUSION_TYPES = {
        'domain': 0,
        'project': 1,
        'user': 2
    }

    EXCLUSION_MAP = {
        0: 'domain',
        1: 'project',
        2: 'user'
    }

    description = "Subcommands for managing VM excludes"

    list_description = "List exclusions"

    @args('--type', metavar='<exclude-type>', dest='excludeType',
          default=None,
          help='Type of exclusion (domain, project, user)')
    def list(self, excludeType=None):
        repositories.setup_database_engine_and_factory()
        repo = repositories.get_vmexclude_repository()
        exclude_type = None
        if excludeType is not None:
            print("Filter by exclude type %s" % (excludeType))
        if excludeType == 'domain':
            exclude_type = 0
        elif excludeType == 'project':
            exclude_type = 1
        elif excludeType == 'user':
            exclude_type = 2
        excludes = repo.get_type_entities(exclude_type=exclude_type)
        headers = [
            'id',
            'type',
            'exclude_id'
        ]
        pt = prettytable.PrettyTable(headers)

        for instance in excludes:
            pt.add_row(
                [
                    instance.id,
                    VmExcludeCommands.EXCLUSION_MAP[instance.exclude_type],
                    instance.exclude_id
                ]
            )
        if six.PY3:
            print(encodeutils.safe_encode(pt.get_string()).decode())
        else:
            print(encodeutils.safe_encode(pt.get_string()))

    add_description = "Add exclusion"

    @args('--type', metavar='<exclude-type>', dest='excludeType',
          default=None,
          help='Type of exclusion (domain, project, user)')
    @args('--id', metavar='<exclude-id>', dest='excludeId',
          default=None,
          help='id of entity to exclude (domain, project, user)')
    def add(self, excludeType=None, excludeId=None):
        if excludeId is None:
            print("id option is mandatory")
            return
        if excludeType not in VmExcludeCommands.EXCLUSION_TYPES:
            print("type is not valid")
            return
        repositories.setup_database_engine_and_factory()
        repo = repositories.get_vmexclude_repository()
        entity = VmExclude()
        entity.exclude_type = VmExcludeCommands.EXCLUSION_TYPES[excludeType]
        entity.exclude_id = excludeId
        try:
            entity = repo.create_exclude(entity)
        except Exception as e:
            print(str(e))
            return
        repositories.commit()
        headers = [
            'id',
            'type',
            'exclude_id'
        ]
        pt = prettytable.PrettyTable(headers)
        pt.add_row(
            [
                entity.id,
                VmExcludeCommands.EXCLUSION_MAP[entity.exclude_type],
                entity.exclude_id
            ]
        )
        if six.PY3:
            print(encodeutils.safe_encode(pt.get_string()).decode())
        else:
            print(encodeutils.safe_encode(pt.get_string()))

    delete_description = "Delete exclusion"

    @args('--id', metavar='<exclude-id>', dest='excludeId',
          default=None,
          help='id of exclude')
    def delete(self, excludeId=None):
        if excludeId is None:
            print("Missing mandatory id parameter")
            return
        repositories.setup_database_engine_and_factory()
        repo = repositories.get_vmexclude_repository()
        repo.delete_entity_by_id(excludeId)
        repositories.commit()
        print("Exclude deleted")


class VmExpireCommands(object):
    """Class for managing VM expiration"""

    description = "Subcommands for managing VM expiration"

    list_description = "List VM expirations"

    @args('--instance', metavar='<instance-id>', dest='instanceid',
          default=None,
          help='Instance id')
    @args('--days', metavar='<expire-in>', dest='days',
          default=None,
          help='Filter VM expiring in X days')
    def list(self, instanceid=None, days=None):
        repositories.setup_database_engine_and_factory()
        repo = repositories.get_vmexpire_repository()
        res = repo.get_all_by(instance_id=instanceid, project_id=None)
        headers = [
            'id',
            'expire',
            'instance.name',
            'instance.id',
            'project.id',
            'user.id'
        ]
        limit = None
        if days:
            try:
                dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
                limit = time.mktime(dt.timetuple())
            except Exception as e:
                print(str(e))
                return
        pt = prettytable.PrettyTable(headers)
        for instance in res:
            if limit and instance.expire > limit:
                continue

            pt.add_row(
                [
                    instance.id,
                    datetime.datetime.fromtimestamp(instance.expire),
                    instance.instance_name,
                    instance.instance_id,
                    instance.project_id,
                    instance.user_id
                ]
            )
        if six.PY3:
            print(encodeutils.safe_encode(pt.get_string()).decode())
        else:
            print(encodeutils.safe_encode(pt.get_string()))

    extend_description = "Extend a VM duration"

    @args('--id', metavar='<id>', dest='expirationid',
          help='Expiration id')
    def extend(self, expirationid):
        if not expirationid:
            print("Missing id paramerer")
            return
        repositories.setup_database_engine_and_factory()
        repo = repositories.get_vmexpire_repository()
        repo.extend_vm(entity_id=expirationid)
        repositories.commit()
        print("VM expiration successfully extended!")

    remove_description = "Deletes a VM expiration"

    @args('--id', metavar='<expiration-id>', dest='expirationid',
          help='Expiration id')
    def remove(self, expirationid):
        if not expirationid:
            print("Missing id paramerer")
            return
        repositories.setup_database_engine_and_factory()
        repo = repositories.get_vmexpire_repository()
        repo.delete_entity_by_id(entity_id=expirationid)
        repositories.commit()
        print("VM expiration successfully generated!")


CATEGORIES = {
    'vm': VmExpireCommands,
    'exclude': VmExcludeCommands
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
             prog='osvmexpire-manage',
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
