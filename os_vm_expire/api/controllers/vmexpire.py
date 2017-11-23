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

from oslo_log import versionutils
import pecan
import time
import datetime

from os_vm_expire import api
from os_vm_expire.common import hrefs
from os_vm_expire.api import controllers
from os_vm_expire.common import utils
from os_vm_expire import i18n as u
from os_vm_expire.model import models
from os_vm_expire.model import repositories as repo

from os_vm_expire.common import config
CONF = config.CONF

LOG = utils.getLogger(__name__)

_DEPRECATION_MSG = '%s has been deprecated in the Newton release. ' \
                   'It will be removed in the Pike release.'


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
    #@controllers.enforce_rbac('vmexpire:get')
    def on_get(self, meta, instance_id=None):
        # TODO if null get all else get expiration for instance
        ctxt = controllers._get_vmexpire_context(pecan.request)
        instances = []
        if instance_id is None:
            instances = self.vmexpire_repo.get_project_entities(str(self.project_id))
        else:
            instance = self.vmexpire_repo.get(entity_id=str(instance_id))
            if instance:
                instances.append(instance)
        return {'vmexpire': instances, 'project_id': self.project_id, 'instance_id': str(instance_id)}
        #return hrefs.convert_to_hrefs(self.vmexpire.to_dict_fields())

    @index.when(method='POST')
    @controllers.handle_exceptions(u._('VmExpire create'))
    @controllers.enforce_content_types(['application/json'])
    def on_post(self, meta):
        # TODO FOR TEST ONLY

        ctxt = controllers._get_vmexpire_context(pecan.request)
        body = api.load_body(pecan.request)
        entity = models.VmExpire()
        entity.instance_id = str(body.get('instance_id'))
        entity.project_id = self.project_id
        entity.user_id = str(ctxt.user)
        entity.expire = int(time.mktime(datetime.datetime.now().timetuple()) + CONF.max_vm_duration * 3600 * 24)
        entity.notified = False
        try:
            instance = self.vmexpire_repo.create_from(entity)
        except Exception as e:
            LOG.exception(e)
            pecan.abort(500, u._('Failed to create vmexpire object'))
        else:
            repo.commit()
            LOG.debug(str({'vmexpire': instance.to_dict_fields(), 'project_id': self.project_id, 'instance_id': None}))
            #return hrefs.convert_to_hrefs(instance.to_dict_fields())
            url = hrefs.convert_vmexpire_to_href(instance.id)
            pecan.response.status = 201
            #return {'vmexpire': instance.to_dict_fields(), 'project_id': self.project_id, 'instance_id': None}
            # TODO check why str is ok but not dict, works on GET
            return str({'vmexpire_ref': str(url)})

    @index.when(method='PUT')
    @controllers.handle_exceptions(u._('VmExpire extend'))
    #@controllers.enforce_rbac('vmexpire:extend')
    @controllers.enforce_content_types(['application/json'])
    def on_put(self, meta, instance_id):
        #body = api.load_body(pecan.request)
        instance = self.vmexpire_repo.extend_vm(entity_id=instance_id)

        return {'vmexpire': [instance], 'project_id': self.project_id, 'instance_id': instance_id}

    @index.when(method='DELETE')
    @utils.allow_all_content_types
    @controllers.handle_exceptions(u._('VmExpire deletion'))
    @controllers.enforce_rbac('vmexpire:delete')
    def on_delete(self, meta, **kwargs):
        # TODO
        self.vmexpire_repo.delete_entity_by_id(
            entity_id=self.vmexpire.id)

class ProjectController(controllers.ACLMixin):

    @pecan.expose(generic=True)
    def index(self, **kwargs):
        pecan.abort(405)  # HTTP 405 Method Not Allowed as default

    @pecan.expose()
    def _lookup(self, project_id, *remainder):
        return VmExpireController(project_id), remainder
