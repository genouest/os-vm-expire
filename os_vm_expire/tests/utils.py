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
from contextlib import contextmanager
import datetime
import functools
# import os
from os import path
import time
import types

import mock
from oslo_config import cfg
from oslo_utils import uuidutils
import oslotest.base as oslotest
from oslotest import createfile

import six
from six.moves.urllib import parse
import webtest

# from OpenSSL import crypto

from os_vm_expire.api import app
# from os_vm_expire.common import config
import os_vm_expire.context
# from os_vm_expire.model import repositories

from os_vm_expire.tests import database_utils


def mock_pecan_request(test_instance, host=None):
    patcher_obj = mock.patch('pecan.request')
    mock_req = patcher_obj.start()
    test_instance.addCleanup(patcher_obj.stop)
    mock_req.url = host


@contextmanager
def pecan_context(test_instance, host=None):
    mock_pecan_request(test_instance, host=host)
    yield


class OsVMExpireAPIBaseTestCase(oslotest.BaseTestCase):
    """Base TestCase for all tests needing to interact with a os-vm-expire app."""
    root_controller = None

    def _build_context(self, project_id, roles=None, user=None, is_admin=False,
                       policy_enforcer=None):
        context = os_vm_expire.context.RequestContext(
            roles=roles,
            user=user,
            project=project_id,
            is_admin=is_admin
        )
        context.policy_enforcer = policy_enforcer
        return context

    def setUp(self):
        super(OsVMExpireAPIBaseTestCase, self).setUp()
        # Make sure we have a test db and session to work with
        database_utils.setup_in_memory_db()

        # Generic project id to perform actions under
        self.project_id = generate_test_valid_uuid()

        # Build the test app
        wsgi_app = app.build_wsgi_app(
            controller=self.root_controller,
            transactional=True
        )

        self.app = webtest.TestApp(wsgi_app)
        self.app.extra_environ = {
            'os_vm_expire.context': self._build_context(self.project_id)
        }

    def tearDown(self):
        database_utils.in_memory_cleanup()
        super(OsVMExpireAPIBaseTestCase, self).tearDown()


class MockModelRepositoryMixin(object):
    """Class for setting up the repo factory mocks

    This class has the purpose of setting up the mocks for the model repository
    factory functions. This is because they are intended to be singletons, and
    thus called inside the code-base, and not really passed around as
    arguments. Thus, this kind of approach is needed.
    The functions assume that the class that inherits from this is a test case
    fixture class. This is because as a side-effect patcher objects will be
    added to the class, and also the cleanup of these patcher objects will be
    added to the tear-down of the respective classes.
    """

    def setup_vmexpire_repository_mock(self, mock_vmexpire_repo=mock.MagicMock(), ):
        """Mocks the expire repository factory function

        :param mock_expire_repo: The pre-configured mock repo to be
                                 returned.
        """
        self.mock_vmexpire_repo_patcher = None
        self._setup_repository_mock(repo_factory='get_vmexpire_repository',
                                    mock_repo_obj=mock_vmexpire_repo,
                                    patcher_obj=self.mock_vmexpire_repo_patcher)

    def setup_vmexclude_repository_mock(self, mock_vmexclude_repo=mock.MagicMock(), ):
        """Mocks the exclude repository factory function

        :param mock_exclude_repo: The pre-configured mock  repo to be
                                 returned.
        """
        self.mock_vmexclude_repo_patcher = None
        self._setup_repository_mock(repo_factory='get_vmexclude_repository',
                                    mock_repo_obj=mock_vmexclude_repo,
                                    patcher_obj=self.mock_vmexclude_repo_patcher)

    def _setup_repository_mock(self, repo_factory, mock_repo_obj, patcher_obj):
        patcher_obj = mock.patch(
            'os_vm_expire.model.repositories.' + repo_factory,
            return_value=mock_repo_obj
        )
        patcher_obj.start()
        self.addCleanup(patcher_obj.stop)


def construct_new_test_function(original_func, name, build_params):
    """Builds a new test function based on parameterized data.

    :param original_func: The original test function that is used as a template
    :param name: The fullname of the new test function
    :param build_params: A dictionary or list containing args or kwargs
        for the new test
    :return: A new function object
    """
    new_func = types.FunctionType(
        six.get_function_code(original_func),
        six.get_function_globals(original_func),
        name=name,
        argdefs=six.get_function_defaults(original_func),
        closure=six.get_function_closure(original_func)
    )

    for key, val in original_func.__dict__.items():
        if key != 'build_data':
            new_func.__dict__[key] = val

    # Support either an arg list or kwarg dict for our data
    build_args = build_params if isinstance(build_params, list) else []
    build_kwargs = build_params if isinstance(build_params, dict) else {}

    # Build a test wrapper to execute with our kwargs
    def test_wrapper(func, test_args, test_kwargs):
        @functools.wraps(func)
        def wrapper(self):
            return func(self, *test_args, **test_kwargs)
        return wrapper

    return test_wrapper(new_func, build_args, build_kwargs)


def process_parameterized_function(name, func_obj, build_data):
    """Build lists of functions to add and remove to a test case."""
    to_remove = []
    to_add = []

    for subtest_name, params in build_data.items():
        # Build new test function
        func_name = '{0}_{1}'.format(name, subtest_name)
        new_func = construct_new_test_function(func_obj, func_name, params)

        # Mark the new function as needed to be added to the class
        to_add.append((func_name, new_func))

        # Mark key for removal
        to_remove.append(name)

    return to_remove, to_add


def parameterized_test_case(cls):
    """Class decorator to process parameterized tests

    This allows for parameterization to be used for potentially any
    unittest compatible runner; including testr and py.test.
    """
    tests_to_remove = []
    tests_to_add = []
    for key, val in vars(cls).items():
        # Only process tests with build data on them
        if key.startswith('test_') and val.__dict__.get('build_data'):
            to_remove, to_add = process_parameterized_function(
                name=key,
                func_obj=val,
                build_data=val.__dict__.get('build_data')
            )
            tests_to_remove.extend(to_remove)
            tests_to_add.extend(to_add)

    # Add all new test functions
    [setattr(cls, name, func) for name, func in tests_to_add]

    # Remove all old test function templates (if they still exist)
    [delattr(cls, key) for key in tests_to_remove if hasattr(cls, key)]
    return cls


def parameterized_dataset(build_data):
    """Simple decorator to mark a test method for processing."""
    def decorator(func):
        func.__dict__['build_data'] = build_data
        return func
    return decorator


def setup_oslo_config_conf(testcase, content, conf_instance=None):

    conf_file_fixture = testcase.useFixture(
        createfile.CreateFileWithContent('osvmexpire', content))
    if conf_instance is None:
        conf_instance = cfg.CONF
    conf_instance([], project="os-vm-expire",
                  default_config_files=[conf_file_fixture.path])

    testcase.addCleanup(conf_instance.reset)


def create_timestamp_w_tz_and_offset(timezone=None, days=0, hours=0, minutes=0,
                                     seconds=0):
    """Creates a timestamp with a timezone and offset in days

    :param timezone: Timezone used in creation of timestamp
    :param days: The offset in days
    :param hours: The offset in hours
    :param minutes: The offset in minutes
    :return: a timestamp
    """
    if timezone is None:
        timezone = time.strftime("%z")

    timestamp = '{time}{timezone}'.format(
        time=(datetime.datetime.today() + datetime.timedelta(days=days,
                                                             hours=hours,
                                                             minutes=minutes,
                                                             seconds=seconds)),
        timezone=timezone)

    return timestamp


def get_limit_and_offset_from_ref(ref):
    matches = dict(parse.parse_qsl(parse.urlparse(ref).query))
    ref_limit = matches['limit']
    ref_offset = matches['offset']

    return ref_limit, ref_offset


def get_tomorrow_timestamp():
    tomorrow = (datetime.today() + datetime.timedelta(days=1))
    return tomorrow.isoformat()


def string_to_datetime(datetimestring, date_formats=None):
    date_formats = date_formats or [
        '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%S.%f', "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"]

    for dateformat in date_formats:
        try:
            return datetime.datetime.strptime(datetimestring, dateformat)
        except ValueError:
            continue
    else:
        raise


def get_id_from_ref(ref):
    """Returns id from reference."""
    ref_id = None
    if ref is not None and len(ref) > 0:
        ref_id = path.split(ref)[1]
    return ref_id


def generate_test_uuid(tail_value=0):
    """Returns a blank uuid with the given value added to the end segment."""
    return '00000000-0000-0000-0000-{value:0>{pad}}'.format(value=tail_value,
                                                            pad=12)


def generate_test_valid_uuid():
    """Returns a valid uuid value, similar to uuid generated in barbican"""
    return uuidutils.generate_uuid()


class DummyClassForTesting(object):
    pass
