
Vmexcludes
===================

Lists, creates, and deletes VM excludes.

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

This API is intended for administrators only. Access is restricted by policy.json.

When a VM is created, if its domain/project/user id matches an exclusion exclude_id,
then no expiration is set for this VM.

List excludes
================

.. rest_method:: GET /vmexcludes/

Lists excluded objects

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401),
forbidden(403)

Request
-------


Response
--------

.. rest_parameters:: parameters.yaml

  - vmexcludes: vmexcludes
  - id: exclude_id
  - exclude_id: exclude_object_id
  - exclude_type: exclude_type


Get exclude
================

.. rest_method:: GET /vmexcludes/{id}

Get selected exclude details.

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

  - vmexclude: vmexclude
  - id: exclude_id
  - exclude_id: exclude_object_id
  - exclude_type: exclude_type


Create exclude
=================

.. rest_method:: POST /vmexpires/

Create an exclusion for an object id and type

Valid types: domain, project, user

Normal response codes: 202

Error response codes: badRequest(400), unauthorized(401),
forbidden(403)

Request
-------


 **Example Create VmExcludes**

.. literalinclude:: vmexclude-create-req.json
  :language: javascript

Response
--------

.. rest_parameters:: parameters.yaml

  - vmexclude: vmexclude
  - id: exclude_id
  - exclude_id: exclude_object_id
  - exclude_type: exclude_type

Delete exclude
=================

.. rest_method:: DELETE /vmexcludes/{id}

Remove exclusion

Normal response codes: 204

Error response codes: badRequest(400), unauthorized(401),
forbidden(403)

Request
-------

.. rest_parameters::parameters.yaml

  - id: id

Response
--------
