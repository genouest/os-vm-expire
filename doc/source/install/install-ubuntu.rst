.. _install-ubuntu:

Install and configure for Ubuntu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and configure the Openstack VmExpiration Management
service for Ubuntu 14.04 (LTS).

.. include:: common_prerequisites.rst

Install and configure components
--------------------------------

#. Install the packages:

   .. code-block:: console

      # apt-get update

      # apt-get install

.. include:: common_configure.rst

.. include:: common_database.rst

Finalize installation
---------------------

Restart the OpenstackVm Expiration Management services:

.. code-block:: console

   # service openstack-os_vm_expire-api restart
