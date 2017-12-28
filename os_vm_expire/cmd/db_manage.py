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
# import os_vm_expire
from os_vm_expire.common import config
from os_vm_expire.model.migration import commands

# from oslo_config import cfg
from oslo_db import options
from oslo_log import log
# from oslo_log import log as logging

import argparse
import os
import sys

sys.path.insert(0, os.getcwd())

# Import and configure logging.
CONF = config.CONF
options.set_defaults(CONF)
log.setup(CONF, 'osvmexpire')
LOG = log.getLogger(__name__)


class DatabaseManager(object):
    """Database Manager class.

    Builds and executes a CLI parser to manage the osvmexpire database
    This extends the Alembic commands.
    """

    def __init__(self, conf):
        self.conf = conf
        self.parser = self.get_main_parser()
        self.subparsers = self.parser.add_subparsers(
            title='subcommands',
            description='Action to perform')
        self.add_revision_args()
        self.add_upgrade_args()
        self.add_history_args()
        self.add_current_args()

    def get_main_parser(self):
        """Create top-level parser and arguments."""
        parser = argparse.ArgumentParser(description='osvmexpire DB manager.')

        return parser

    def add_revision_args(self):
        """Create 'revision' command parser and arguments."""
        create_parser = self.subparsers.add_parser('revision', help='Create a '
                                                   'new DB version file.')
        create_parser.add_argument('--message', '-m', default='DB change',
                                   help='the message for the DB change')
        create_parser.add_argument('--autogenerate',
                                   help='autogenerate from models',
                                   action='store_true')
        create_parser.set_defaults(func=self.revision)

    def add_upgrade_args(self):
        """Create 'upgrade' command parser and arguments."""
        create_parser = self.subparsers.add_parser('upgrade',
                                                   help='Upgrade to a '
                                                   'future version DB '
                                                   'version file')
        create_parser.add_argument('--version', '-v', default='head',
                                   help='the version to upgrade to, or else '
                                        'the latest/head if not specified.')
        create_parser.set_defaults(func=self.upgrade)

    def add_history_args(self):
        """Create 'history' command parser and arguments."""
        create_parser = self.subparsers.add_parser(
            'history',
            help='List changeset scripts in chronological order.')
        create_parser.add_argument('--verbose', '-V', action="store_true",
                                   help='Show full information about the '
                                        'revisions.')
        create_parser.set_defaults(func=self.history)

    def add_current_args(self):
        """Create 'current' command parser and arguments."""
        create_parser = self.subparsers.add_parser(
            'current',
            help='Display the current revision for a database.')
        create_parser.add_argument('--verbose', '-V', action="store_true",
                                   help='Show full information about the '
                                        'revision.')
        create_parser.set_defaults(func=self.current)

    def revision(self, args):
        """Process the 'revision' Alembic command."""
        config = commands.init_config()
        config.osvmexpire = CONF
        commands.generate(autogenerate=args.autogenerate,
                          message=args.message,
                          config=config)

    def upgrade(self, args):
        """Process the 'upgrade' Alembic command."""
        LOG.debug("Performing database schema migration...")
        config = commands.init_config()
        config.osvmexpire = CONF
        commands.upgrade(to_version=args.version, config=config)

    def history(self, args):
        config = commands.init_config()
        config.osvmexpire = CONF
        commands.history(args.verbose, config=config)

    def current(self, args):
        config = commands.init_config()
        config.osvmexpire = CONF
        commands.current(args.verbose, config=config)

    def execute(self):
        """Parse the command line arguments."""
        args = self.parser.parse_args()
        # Perform other setup here...
        args.func(args)


def _exception_is_successful_exit(thrown_exception):
    return (isinstance(thrown_exception, SystemExit) and
            (thrown_exception.code is None or thrown_exception.code == 0))


def main():
    try:
        dm = DatabaseManager(CONF)
        dm.execute()
    except Exception as ex:
        if not _exception_is_successful_exit(ex):
            LOG.exception('Problem seen trying to run osvmexpire db manage')
            sys.stderr.write("ERROR: {0}\n".format(ex))
            sys.exit(1)


if __name__ == '__main__':
    main()
