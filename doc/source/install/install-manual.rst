.. _install-manual:

Install and configure from sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and configure the Openstack VmExpiration Management
service from sources.

.. include:: common_prerequisites.rst

Install and configure components
--------------------------------

#. Install the packages:

   .. code-block:: console

      # pip install -r requirements.txt

      # python setup.py install

.. include:: common_configure.rst

.. include:: common_database.rst

Create /var/log/os-vm-expire directory for osvmexpire-api service.

Finalize installation
---------------------

Restart the OpenstackVm Expiration Management services:

.. code-block:: console

   # uwsgi --master --die-on-term --emperor /etc/os-vm-expire/vassals --logto /var/log/os-vm-expire/osvmexpire-api.log --stats localhost:9314

   # osvmexpire-worker --config-file etc/os-vm-expire/osvmexpire.conf

   # osvmexpire-cleaner --config-file /etc/os-vm-expire/osvmexpire.conf
