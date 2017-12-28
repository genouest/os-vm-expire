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
This test module focuses on RBAC interactions with the API resource classes.
For typical-flow business logic tests of these classes, see the
'resources_test.py' module.
"""
import os

import mock
from oslo_policy import policy
from webob import exc

from os_vm_expire.api.controllers import versions
from os_vm_expire.api.controllers import vmexpire
from os_vm_expire.common import config
from os_vm_expire import context
# from os_vm_expire.model import models
from os_vm_expire.tests import utils

import webob

# Point to the policy.json file located in source control.
TEST_VAR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            '../../../etc', 'oslo-config-generator'))

TEST_CONFIG_FILE = os.path.join(TEST_VAR_DIR, 'osvmexpire.conf.sample')
TEST_POLICY_FILE = os.path.join(TEST_VAR_DIR, 'policy.json.sample')
CONF = config.new_config()

ENFORCER = policy.Enforcer(CONF, policy_file=TEST_POLICY_FILE)


class TestableResource(object):

    def __init__(self, *args, **kwargs):
        self.controller = self.controller_cls(*args, **kwargs)

    def on_get(self, req, resp, *args, **kwargs):
        with mock.patch('pecan.request', req):
            with mock.patch('pecan.response', resp):
                return self.controller.on_get(*args, **kwargs)

    def on_post(self, req, resp, *args, **kwargs):
        with mock.patch('pecan.request', req):
            with mock.patch('pecan.response', resp):
                return self.controller.on_post(*args, **kwargs)

    def on_put(self, req, resp, *args, **kwargs):
        with mock.patch('pecan.request', req):
            with mock.patch('pecan.response', resp):
                return self.controller.on_put(*args, **kwargs)

    def on_delete(self, req, resp, *args, **kwargs):
        with mock.patch('pecan.request', req):
            with mock.patch('pecan.response', resp):
                return self.controller.on_delete(*args, **kwargs)


class VersionsResource(TestableResource):
    controller_cls = versions.VersionsController


class VmExpireResource(TestableResource):
    controller_cls = vmexpire.VmExpireController


class BaseTestCase(utils.OsVMExpireAPIBaseTestCase, utils.MockModelRepositoryMixin):

    def setUp(self):
        super(BaseTestCase, self).setUp()
        CONF(args=['--config-dir', TEST_VAR_DIR])
        CONF(args=['--config-file', TEST_CONFIG_FILE])
        self.policy_enforcer = ENFORCER
        self.policy_enforcer.load_rules(True)
        self.resp = mock.MagicMock()

    def _generate_req(self, roles=None, accept=None, content_type=None,
                      user_id=None, project_id=None):
        """Generate a fake HTTP request with security context added to it."""
        req = mock.MagicMock()
        req.get_param.return_value = None

        kwargs = {
            'user': user_id,
            'project': project_id,
            'roles': roles or [],
            'policy_enforcer': self.policy_enforcer,
        }
        req.environ = {}
        req.environ['os_vm_expire.context'] = context.RequestContext(**kwargs)
        req.content_type = content_type
        if accept:
            req.accept.header_value.return_value = accept
        else:
            req.accept = None

        return req

    def _generate_stream_for_exit(self):
        """Mock HTTP stream generator, to force RBAC-pass exit.

        Generate a fake HTTP request stream that forces an IOError to
        occur, which short circuits API resource processing when RBAC
        checks under test here pass.
        """
        stream = mock.MagicMock()
        read = mock.MagicMock(return_value=None, side_effect=IOError())
        stream.read = read
        return stream

    def _assert_post_rbac_exception(self, exception, role):
        """Assert that we received the expected RBAC-passed exception."""
        self.assertEqual(500, exception.status_int)

    def _generate_get_error(self):
        """Falcon exception generator to throw from early-exit mocks.

        Creates an exception that should be raised by GET tests that pass
        RBAC. This allows such flows to short-circuit normal post-RBAC
        processing that is not tested in this module.
        :return: Python exception that should be raised by repo get methods.
        """
        # The 'Read Error' clause needs to match that asserted in
        #    _assert_post_rbac_exception() above.
        return exc.HTTPServerError(detail='Read Error')

    def _assert_pass_rbac(self, roles, method_under_test, accept=None,
                          content_type=None, user_id=None, project_id=None):
        """Assert that RBAC authorization rules passed for the specified roles.

        :param roles: List of roles to check, one at a time
        :param method_under_test: The test method to invoke for each role.
        :param accept Optional Accept header to set on the HTTP request
        :return: None
        """
        for role in roles:
            self.req = self._generate_req(roles=[role] if role else [],
                                          accept=accept,
                                          content_type=content_type,
                                          user_id=user_id,
                                          project_id=project_id)
            # Force an exception early past the RBAC passing.
            type(self.req).body = mock.PropertyMock(side_effect=IOError)
            self.req.body_file = self._generate_stream_for_exit()

            exception = self.assertRaises(exc.HTTPServerError,
                                          method_under_test)
            self._assert_post_rbac_exception(exception, role)

    def _assert_fail_rbac(self, roles, method_under_test, accept=None,
                          content_type=None, user_id=None, project_id=None):
        """Assert that RBAC rules failed for one of the specified roles.

        :param roles: List of roles to check, one at a time
        :param method_under_test: The test method to invoke for each role.
        :param accept Optional Accept header to set on the HTTP request
        :return: None
        """
        for role in roles:
            self.req = self._generate_req(roles=[role] if role else [],
                                          accept=accept,
                                          content_type=content_type,
                                          user_id=user_id,
                                          project_id=project_id)

            exception = self.assertRaises(exc.HTTPForbidden, method_under_test)
            self.assertEqual(403, exception.status_int)


class WhenTestingVersionsResource(BaseTestCase):
    """RBAC tests for the barbican.api.resources.VersionsResource class."""
    def setUp(self):
        super(WhenTestingVersionsResource, self).setUp()

        self.resource = VersionsResource()

    def test_rules_should_be_loaded(self):
        self.assertIsNotNone(self.policy_enforcer.rules)

    def test_should_pass_get_versions(self):
        # Can't use base method that short circuits post-RBAC processing here,
        # as version GET is trivial
        for role in ['admin', 'member']:
            self.req = self._generate_req(roles=[role] if role else [])
            self._invoke_on_get()

    def test_should_pass_get_versions_with_bad_roles(self):
        self.req = self._generate_req(roles=[None, 'bunkrolehere'])
        self._invoke_on_get()

    def test_should_pass_get_versions_with_no_roles(self):
        self.req = self._generate_req()
        self._invoke_on_get()

    def test_should_pass_get_versions_multiple_roles(self):
        self.req = self._generate_req(roles=['admin', 'member'])
        self._invoke_on_get()

    def _invoke_on_get(self):
        self.resource.on_get(self.req, self.resp)


class WhenTestingVmExpireResource(BaseTestCase):
    """RBAC tests for the barbican.api.resources.SecretsResource class."""
    def setUp(self):
        super(WhenTestingVmExpireResource, self).setUp()

        self.vmexpire_repo = mock.MagicMock()
        self.setup_vmexpire_repository_mock(self.vmexpire_repo)

        self.project_id = '12345project'
        self.user_id = '12345user'
        self.resource = VmExpireResource(self.project_id)

    def test_rules_should_be_loaded(self):
        self.assertIsNotNone(self.policy_enforcer.rules)

    def test_should_pass_get_vmexpires(self):
        self.req = self._generate_req(roles=['member'],
            content_type='application/json',
            project_id=self.project_id)
        res = self._invoke_on_get()
        self.assertIsNotNone(res)

    def test_should_pass_get_vmexpire(self):
        self.req = self._generate_req(roles=['member'],
            content_type='application/json',
            project_id=self.project_id)
        res = self._invoke_on_get('12345expire')
        self.assertIsNotNone(res)

    def test_should_fail_get_vmexpires(self):
        self.req = self._generate_req(roles=['bogus'])
        self.assertRaises(webob.exc.HTTPForbidden, self._invoke_on_get)

    def test_should_fail_get_vmexpire(self):
        self.req = self._generate_req(roles=['bogus'])
        self.assertRaises(webob.exc.HTTPForbidden, self._invoke_on_get, '12345')

    def test_should_pass_get_vmexpires_again(self):
        self.req = self._generate_req(roles=['admin', 'member'])
        res = self._invoke_on_get()
        self.assertIsNotNone(res)

    def test_should_fail_put_vmexpire(self):
        self.req = self._generate_req(roles=['bogus'])
        self.assertRaises(webob.exc.HTTPForbidden, self._invoke_on_put, '12345')

    def test_should_admin_pass_put_vmexpire(self):
        self.req = self._generate_req(roles=['admin'],
            content_type='application/json')
        res = self._invoke_on_put('12345expire')
        self.assertIsNotNone(res)

    def test_should_user_pass_put_vmexpire(self):
        self.req = self._generate_req(roles=['member'],
            content_type='application/json',
            project_id=self.project_id)
        res = self._invoke_on_put('12345expire')
        self.assertIsNotNone(res)

    def test_should_fail_delete_vmexpire(self):
        self.req = self._generate_req(roles=['member'],
            content_type='application/json',
            project_id=self.project_id)
        self.assertRaises(webob.exc.HTTPForbidden, self._invoke_on_delete, '12345')

    def _invoke_on_put(self, instance_id=None):
        return self.resource.on_put(self.req, self.resp, 'vmexpires', instance_id)

    def _invoke_on_delete(self, instance_id=None):
        return self.resource.on_delete(self.req, self.resp, 'vmexpires', instance_id)

    def _invoke_on_get(self, instance_id=None):
        return self.resource.on_get(self.req, self.resp, 'vmexpires', instance_id)
