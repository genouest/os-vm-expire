===============================
os-vm-expire
===============================

Manage VM expiration and deletion

!!!In Development!!!!



* Free software: Apache license
* Documentation: https://docs.openstack.org/os-vm-expire/latest
* Source: https://git.openstack.org/cgit/genouest/os-vm-expire
* Bugs: https://bugs.launchpad.net/replace with the name of the project on launchpad

Features
--------

* TODO

remove def on_post(self, meta) in api.controllers.vmexpire.py (used to inject data for testing)

test get: curl -v -H "X-Auth-Token: $TOKEN" http://localhost:9311/v1/project/123/vmexpire/09400330-3b40-4d10-b719-bb1955d0818f
test inject: curl -v -H "X-Auth-Token: $TOKEN" -H "Content-Type: application/json" -X POST -d '{"instance_id": "1234"}'  http://localhost:9311/v1/project/123/vmexpire/

check user/policy management

code/test PUT for VM extend

add worker listening to nova notif on vm create/delete

manage alembic revisions for upgrades

Development
-----------

Configuration
~~~~~~~~~~~~~

.. code-block:: bash

  oslo-config-generator --namespace oslo.messaging --namespace osvmexpire.common.config --namespace keystonemiddleware.auth_token > etc/oslo-config-generator/osvmexpire.conf
  oslopolicy-sample-generator --config-file etc/oslo-config-generator/policy.conf --format json

Create/Upgrade DB
~~~~~~~~~~~~~~~~~

(if using mysql need library MySQL-python)

.. code-block:: bash

  osvmexpire-db-manage upgrade

Documentation
~~~~~~~~~~~~~

.. code-block:: bash

  python setup.py build_sphinx

Start API server
~~~~~~~~~~~~~~~~

For dev (port 8000)

.. code-block:: bash

  osvmexpire-wsgi-api

For prod

.. code-block:: bash

  # uwsgi --master --die-on-term --emperor /etc/os-vm-expire/vassals --logto /var/log/os-vm-expire/osvmexpire-api.log --stats localhost:9314
  python bin/osvmexpire-api.py


Start worker
~~~~~~~~~~~~

.. code-block:: bash

  osvmexpire-worker --config-file etc/os-vm-expire/osvmexpire.conf
