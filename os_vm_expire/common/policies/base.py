#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from oslo_policy import policy


rules = [
    policy.RuleDefault('admin',
                       'role:admin'),
    policy.RuleDefault('observer',
                       'role:observer'),
    policy.RuleDefault('creator',
                       'role:creator'),
    policy.RuleDefault('audit',
                       'role:audit'),
    policy.RuleDefault('service_admin',
                       'role:key-manager:service-admin'),
    policy.RuleDefault('admin_or_user_does_not_work',
                       'project_id:%(project_id)s'),
    policy.RuleDefault('admin_or_user',
                       'rule:admin or project_id:%(project_id)s'),
    policy.RuleDefault('admin_or_creator',
                       'rule:admin or rule:creator'),
    policy.RuleDefault('all_but_audit',
                       'rule:admin or rule:observer or rule:creator'),
    policy.RuleDefault('all_users',
                       'rule:admin or rule:observer or rule:creator or '
                       'rule:audit or rule:service_admin'),
]


def list_rules():
    return rules
