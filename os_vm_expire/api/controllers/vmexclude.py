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
from os_vm_expire import api
from os_vm_expire.api import controllers
from os_vm_expire.common import hrefs
from os_vm_expire.common import utils
from os_vm_expire import i18n as u
# from os_vm_expire.model import models
from os_vm_expire.model import repositories as repo

from os_vm_expire.common import config


CONF = config.CONF

LOG = utils.getLogger(__name__)


def _vmexclude_not_found():
    """Throw exception indicating order not found."""
    pecan.abort(404, u._('Not Found. Sorry but your exclude is in '
                         'another castle.'))


class VmExcludeController(controllers.ACLMixin):

    """Handles Order retrieval and deletion requests."""

    def __init__(self, project_id):
        self.project_id = str(project_id)
        self.vmexclude_repo = repo.get_vmexclude_repository()

    @pecan.expose(generic=True)
    def index(self, **kwargs):
        pecan.abort(405)  # HTTP 405 Method Not Allowed as default

    @index.when(method='GET', template='json')
    @controllers.handle_exceptions(u._('VmExclude retrieval'))
    @controllers.enforce_rbac('vmexclude:get')
    def on_get(self, meta, instance_id=None):
        # if null get all else get exclude instance
        vm_repo = self.vmexclude_repo
        instances = []
        if instance_id is None:
            instances = vm_repo.get_type_entities()
        else:
            instance = vm_repo.get(entity_id=str(instance_id))
            # url = hrefs.convert_vmexpire_to_href(instance.id)
            repo.commit()
            return {
                'vmexclude': hrefs.convert_to_hrefs(instance.to_dict_fields())
                }

        total = len(instances)
        instances_resp = [
            hrefs.convert_to_hrefs(o.to_dict_fields())
            for o in instances
        ]
        instances_resp_overall = hrefs.add_nav_hrefs(
            'vmexcludes',
            0, total, total,
            {'vmexcludes': instances_resp}
            )
        instances_resp_overall = hrefs.add_self_href(self.project_id + '/vmexcludes/', instances_resp_overall)
        instances_resp_overall.update({'total': total})
        repo.commit()
        return instances_resp_overall

    @index.when(method='POST', template='json')
    @controllers.handle_exceptions(u._('VmExclude create'))
    @controllers.enforce_rbac('vmexclude:create')
    @controllers.enforce_content_types(['application/json'])
    def on_post(self, meta):
        instance = None
        data = api.load_body(pecan.request)
        entity_id = data.get('id')
        entity_type = data.get('type')
        if not entity_id or entity_type is None:
            pecan.response.status = 403
            return 'Empty id or type'
        if entity_type not in ['domain', 'project', 'user']:
            pecan.response.status = 403
            return 'Invalid type'
        else:
            entity_type = self.vmexclude_repo.get_exclude_type(entity_type)
        try:
            entity = self.vmexclude_repo.create_exclude_entity(entity_id, entity_type)
            instance = self.vmexclude_repo.create_exclude(entity)
        except Exception as e:
            pecan.response.status = 403
            return str(e)
        # url = hrefs.convert_vmexpire_to_href(instance.id)
        repo.commit()
        pecan.response.status = 202
        return {
            'vmexclude': hrefs.convert_to_hrefs(instance.to_dict_fields())
        }

    @index.when(method='DELETE', template='json')
    @controllers.handle_exceptions(u._('VmExclude deletion'))
    @controllers.enforce_rbac('vmexclude:delete')
    @controllers.enforce_content_types(['application/json'])
    def on_delete(self, meta, instance_id):
        instance = self.vmexclude_repo.get(entity_id=instance_id)
        if instance:
            self.vmexclude_repo.delete_entity_by_id(entity_id=instance.id)
            repo.commit()
        pecan.response.status = 204
        return
