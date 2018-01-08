
Vmexpires
===================

Lists, extend, and deletes VM expirations.

All API calls described throughout the rest of this document require
authentication with the OpenStack Identity service. After authentication,
a base ``service url`` can be extracted from the Identity token of type
``vmexpire``. This ``service url`` will be the root url that every API call
uses to build a full path.

For instance, if the ``service url`` is
``http://myservice.pvt/v1/%(tenant_id)s`` then the full API call for
``/vmexpire`` is ``http://myservice.pvt/v1/%(tenant_id)s/vmexpire``.

Depending on the deployment, the vmexpire ``service url`` might be http or
https, a custom port, a custom path, and include your tenant id. The
only way to know the urls for your deployment is by using the service
catalog. The os-vm-expire URL should never be hard coded in applications,
even if they are only expected to work at a single site. It should
always be discovered from the Identity token.

List expirations
================

.. rest_method:: GET /vmexpires/

Lists expiration info for all vmexpires in selected project.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401),
forbidden(403)

Request
-------

.. rest_parameters:: parameters.yaml

  - all_tenants: all_tenants


Response
--------

.. rest_parameters:: parameters.yaml

  - vmexpires: vmexpires
  - id: expiration_id
  - instance_id: instance_id
  - intance_name: instance_name
  - project_id: project_id
  - user_id: user_id

**Example List VmExpires**

.. literalinclude:: vmexpire-list-resp.json
    :language: javascript


Get expiration
================

.. rest_method:: GET /vmexpires/{id}

Get selected expiration details.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401),
forbidden(403)

Request
-------

.. rest_parameters::parameters.yaml

  - id: id


Response
--------

.. rest_parameters:: parameters.yaml

  - vmexpire: vmexpire
  - id: expiration_id
  - instance_id: instance_id
  - intance_name: instance_name
  - project_id: project_id
  - user_id: user_id

**Example Get VmExpire**

.. literalinclude:: vmexpire-list-resp.json
    :language: javascript

Extend expiration
=================

.. rest_method:: PUT /vmexpires/{id}

Extend expiration delay for selected expiration.

Normal response codes: 202

Error response codes: badRequest(400), unauthorized(401),
forbidden(403)

Request
-------

.. rest_parameters::parameters.yaml

  - id: id

Response
--------

.. rest_parameters:: parameters.yaml

  - vmexpire: vmexpire
  - id: expiration_id
  - instance_id: instance_id
  - intance_name: instance_name
  - project_id: project_id
  - user_id: user_id

Delete expiration
=================

.. rest_method:: DELETE /vmexpires/{id}

Remove expiration (usually admin only according to policy.json).

Normal response codes: 204

Error response codes: badRequest(400), unauthorized(401),
forbidden(403)

Request
-------

.. rest_parameters::parameters.yaml

  - id: id

Response
--------
