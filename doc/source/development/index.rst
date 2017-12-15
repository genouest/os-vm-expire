=============
Development
=============

Configuration file generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To generate osvmexpire.conf and policy.json files

.. code-block:: bash

  oslo-config-generator --namespace oslo.log --namespace oslo.db --namespace oslo.messaging --namespace osvmexpire.common.config --namespace keystonemiddleware.auth_token --namespace oslo.service.periodic_task --namespace oslo.service.service > etc/oslo-config-generator/osvmexpire.conf

  oslopolicy-sample-generator --config-file etc/oslo-config-generator/policy.conf --format json


Create/Upgrade DB
~~~~~~~~~~~~~~~~~

If using mysql need library MySQL-python or PyMySQL according to database connection url.

.. code-block:: bash

  osvmexpire-db-manage upgrade

Generate documentation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

  python setup.py build_sphinx

Release notes
~~~~~~~~~~~~~

Release notes are managed via reno

.. code-block:: bash

  tox -e releasenotes

To add a release note:

.. code-block:: bash

  reno -new XXXX
