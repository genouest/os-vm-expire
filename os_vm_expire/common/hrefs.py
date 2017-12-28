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
from os_vm_expire.common import utils


def convert_resource_id_to_href(resource_slug, resource_id):
    """Convert the resource ID to a HATEOAS-style href with resource slug."""
    if resource_id:
        resource = '{slug}/{id}'.format(slug=resource_slug, id=resource_id)
    else:
        resource = '{slug}/????'.format(slug=resource_slug)
    return utils.hostname_for_refs(resource=resource)


def convert_vmexpire_to_href(vmexpire_id):
    """Convert the secret-store ID to a HATEOAS-style href."""
    return convert_resource_id_to_href('vmexpire', vmexpire_id)


def convert_to_hrefs(fields):
    """Convert id's within a fields dict to HATEOAS-style hrefs."""
    url = convert_vmexpire_to_href(fields['id'])
    fields['links'] = {'self': url}
    return fields


def convert_list_to_href(resources_name, offset, limit):
    """Supports pretty output of paged-list hrefs.

    Convert the offset/limit info to a HATEOAS-style href
    suitable for use in a list navigation paging interface.
    """
    resource = '{0}?limit={1}&offset={2}'.format(resources_name, limit,
                                                 offset)
    return utils.hostname_for_refs(resource=resource)


def previous_href(resources_name, offset, limit):
    """Supports pretty output of previous-page hrefs.

    Create a HATEOAS-style 'previous' href suitable for use in a list
    navigation paging interface, assuming the provided values are the
    currently viewed page.
    """
    offset = max(0, offset - limit)
    return convert_list_to_href(resources_name, offset, limit)


def next_href(resources_name, offset, limit):
    """Supports pretty output of next-page hrefs.

    Create a HATEOAS-style 'next' href suitable for use in a list
    navigation paging interface, assuming the provided values are the
    currently viewed page.
    """
    offset = offset + limit
    return convert_list_to_href(resources_name, offset, limit)


def add_nav_hrefs(resources_name, offset, limit,
                  total_elements, data):
    """Adds next and/or previous hrefs to paged list responses.

    :param resources_name: Name of api resource
    :param offset: Element number (ie. index) where current page starts
    :param limit: Max amount of elements listed on current page
    :param total_elements: Total number of elements
    :returns: augmented dictionary with next and/or previous hrefs
    """
    if offset > 0:
        data.update({'previous': previous_href(resources_name,
                                               offset,
                                               limit)})
    if total_elements > (offset + limit):
        data.update({'next': next_href(resources_name,
                                       offset,
                                       limit)})
    return data


def add_self_href(resource_name, data):
    """Add self href to response

    :param resources_name: Name of api resource
    :returns: augmented dictionary with next and/or previous hrefs
    """
    if 'links' not in data:
        data['links'] = {}
    data['links'].update({'self': utils.hostname_for_refs(resource=resource_name)})
    return data


def get_vmexpire_id_from_ref(vmexpire_ref):
    """Parse a container reference and return the container ID

    The container ID is the right-most element of the URL
    :param container_ref: HTTP reference of container
    :return: a string containing the ID of the container
    """
    vmexpire_id = vmexpire_ref.rsplit('/', 1)[1]
    return vmexpire_id
