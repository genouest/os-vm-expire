===================
 Vmexpires
===================

Lists, extend, and deletes VM expirations.

All API calls described throughout the rest of this document require
authentication with the OpenStack Identity service. After authentication,
a base ``service url`` can be extracted from the Identity token of type
``compute``. This ``service url`` will be the root url that every API call
uses to build a full path.

For instance, if the ``service url`` is
``http://mycompute.pvt/v1/%(tenant_id)s`` then the full API call for
``/vmexpire`` is ``http://mycompute.pvt/v1/%(tenant_id)s/vmexpire``.

Depending on the deployment, the vmexpire ``service url`` might be http or
https, a custom port, a custom path, and include your tenant id. The
only way to know the urls for your deployment is by using the service
catalog. The Compute URL should never be hard coded in applications,
even if they are only expected to work at a single site. It should
always be discovered from the Identity token.

List expirations
================

.. rest_method:: GET /vmexpires/

Lists IDs, names, and links for all expiration for selected project.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401),
forbidden(403)

Request
-------




Response
--------

.. rest_parameters:: parameters.yaml

  - instances: instances
  - id: expiration_id
  - instance_id: instance_id
  - intance_name: instance_name
  - project_id: project_id
  - user_id: user_id
