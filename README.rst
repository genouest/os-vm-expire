===============================
os-vm-expire
===============================

Manage VM expiration and auto-deletion in an Openstack cloud.

This project is an unofficial Openstack project, but follows Openstack projects architecture, with a Horizon plugin and associated services.

!!!In Development!!!!

* Free software: Apache license
* Documentation: https://docs.openstack.org/os-vm-expire/latest
* Source: https://git.openstack.org/cgit/genouest/os-vm-expire
* Bugs: https://bugs.launchpad.net/replace with the name of the project on launchpad

Features
--------

* On VM creation, add an expiration date
* On near-expiration date, send an email to user
* Horizon plugin to view VM expiration and allow for expiration extend
* On expiration date, delete the VM and send an email to user
* CLI commands to extend a VM or remove expiration from a VM (admin only)


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

Manage nova notifications on instance creation and deletion to create/delete expiration objects.

.. code-block:: bash

  osvmexpire-worker --config-file etc/os-vm-expire/osvmexpire.conf


Start cleaner
~~~~~~~~~~~~~

Checks expiration time of VMs and sends notifications before expiration to let use extend the VM if necessary.
Once expiration is reached (and if user could be notified of expiration), deletes the VM.

.. code-block:: bash

  osvmexpire-cleaner --config-file /etc/os-vm-expire/osvmexpire.conf

  CLI usage
  ---------

  .. code-block:: bash

     osvmexpire-manage db -h
     osvmexpire-manage vm extend -h
     osvmexpire-manage vm remove -h
