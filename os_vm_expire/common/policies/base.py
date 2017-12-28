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
    policy.RuleDefault('context_is_admin',
                       'role:admin'),
    policy.RuleDefault('admin_or_owner',
                       'rule:context_is_admin or is_admin:True or project_id:%(project_id)s'),
    policy.RuleDefault('default',
                       'rule:admin_or_owner'),
]


{
    "context_is_admin": "role:admin",
    "admin_or_owner": "rule:context_is_admin or is_admin:True or project_id:%(project_id)s",
    "default": "rule:admin_or_owner",
    "vmexpire:get": "rule:admin_or_owner",
    "vmexpire:extend": "rule:admin_or_owner",
    "vmexpire:delete": "rule:context_is_admin",
    "vmexclude:get": "rule:admin",
    "vmexclude:create": "rule:admin",
    "vmexclude:delete": "rule:admin"
}


def list_rules():
    return rules
