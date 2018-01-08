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

# from oslo_log import versionutils
import pecan
# import time
# import datetime

# from os_vm_expire import api
from os_vm_expire.api import controllers
from os_vm_expire.common import hrefs
from os_vm_expire.common import utils
from os_vm_expire import i18n as u
# from os_vm_expire.model import models
from os_vm_expire.model import repositories as repo

from os_vm_expire.common import config


CONF = config.CONF

LOG = utils.getLogger(__name__)


def _vmexpire_not_found():
    """Throw exception indicating order not found."""
    pecan.abort(404, u._('Not Found. Sorry but your vm is in '
                         'another castle.'))


class VmExpireController(controllers.ACLMixin):

    """Handles Order retrieval and deletion requests."""

    def __init__(self, project_id):
        self.project_id = str(project_id)
        self.vmexpire_repo = repo.get_vmexpire_repository()

    @pecan.expose(generic=True)
    def index(self, **kwargs):
        pecan.abort(405)  # HTTP 405 Method Not Allowed as default

    @index.when(method='GET', template='json')
    @controllers.handle_exceptions(u._('VmExpire retrieval'))
    @controllers.enforce_rbac('vmexpire:get')
    def on_get(self, meta, instance_id=None):
        # if null get all else get expiration for instance
        # ctxt = controllers._get_vmexpire_context(pecan.request)
        vm_repo = self.vmexpire_repo
        instances = []
        if instance_id is None:
            all_tenants = pecan.request.GET.get('all_tenants')
            if all_tenants is not None:
                ctxt = controllers._get_vmexpire_context(pecan.request)
                if ctxt.is_admin:
                    instances = vm_repo.get_entities()
                else:
                    pecan.response.status = 403
                    return "all_tenants is restricted to admin users"
            else:
                instances = vm_repo.get_project_entities(str(self.project_id))
        else:
            instance = vm_repo.get(entity_id=str(instance_id))
            # url = hrefs.convert_vmexpire_to_href(instance.id)
            repo.commit()
            return {
                'vmexpire': hrefs.convert_to_hrefs(instance.to_dict_fields())
                }

        total = len(instances)
        instances_resp = [
            hrefs.convert_to_hrefs(o.to_dict_fields())
            for o in instances
        ]
        instances_resp_overall = hrefs.add_nav_hrefs(
            'vmexpires',
            0, total, total,
            {'vmexpires': instances_resp}
            )
        instances_resp_overall = hrefs.add_self_href(self.project_id + '/vmexpires/', instances_resp_overall)
        instances_resp_overall.update({'total': total})
        repo.commit()
        return instances_resp_overall

    @index.when(method='PUT', template='json')
    @controllers.handle_exceptions(u._('VmExpire extend'))
    @controllers.enforce_rbac('vmexpire:extend')
    @controllers.enforce_content_types(['application/json'])
    def on_put(self, meta, instance_id):
        instance = None
        try:
            instance = self.vmexpire_repo.extend_vm(entity_id=instance_id)
        except Exception as e:
            pecan.response.status = 403
            return str(e)
        # url = hrefs.convert_vmexpire_to_href(instance.id)
        repo.commit()
        pecan.response.status = 202
        return {
            'vmexpire': hrefs.convert_to_hrefs(instance.to_dict_fields())
        }

    @index.when(method='DELETE', template='json')
    @controllers.handle_exceptions(u._('VmExpire expiration deletion'))
    @controllers.enforce_rbac('vmexpire:delete')
    @controllers.enforce_content_types(['application/json'])
    def on_delete(self, meta, instance_id):
        instance = self.vmexpire_repo.get(entity_id=instance_id)
        if instance:
            self.vmexpire_repo.delete_entity_by_id(entity_id=instance.id)
            repo.commit()
        pecan.response.status = 204
        return
