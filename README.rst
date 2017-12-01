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



test get: curl -v -H "X-Auth-Token: $TOKEN" http://localhost:9311/v1/123/vmexpire/09400330-3b40-4d10-b719-bb1955d0818f
test inject: curl -v -H "X-Auth-Token: $TOKEN" -H "Content-Type: application/json" -X POST -d '{"instance_id": "1234"}'  http://localhost:9311/v1/123/vmexpire/

check user/policy management


add periodic service to delete VMs expired (need nova conf) (cmd.cleaner.py)

manage alembic revisions for upgrades

Development
-----------

Configuration
~~~~~~~~~~~~~

.. code-block:: bash

  oslo-config-generator --namespace oslo.messaging --namespace osvmexpire.common.config --namespace keystonemiddleware.auth_token --namespace oslo.service.periodic_task --namespace oslo.service.service > etc/oslo-config-generator/osvmexpire.conf
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

  export OSVMEXPIRE_PORT=9311 # optional
  osvmexpire-wsgi-api

For prod

.. code-block:: bash

  # uwsgi --master --die-on-term --emperor /etc/os-vm-expire/vassals --logto /var/log/os-vm-expire/osvmexpire-api.log --stats localhost:9314
  python bin/osvmexpire-api.py


Start worker
~~~~~~~~~~~~

.. code-block:: bash

  osvmexpire-worker --config-file etc/os-vm-expire/osvmexpire.conf


Start cleaner

.. code-block:: bash

  osvmexpire-cleaner --config-file /etc/os-vm-expire/osvmexpire.conf

  CLI usage
  ---------

  .. code-block:: bash

     osvmexpire-manage db -h
     osvmexpire-manage vm extend -h
     osvmexpire-manage vm remove -h
