.. _install-ubuntu:

Install and configure for Ubuntu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and configure the Openstack VmExpiration Management
service for Ubuntu 14.04 (LTS).

.. include:: common_prerequisites.rst

Install and configure components
--------------------------------

#. Get the deb from git repo release (e.g. https://github.com/genouest/os-vm-expire/releases/tag/0.9.4)

   .. code-block:: console

      # wget https://github.com/genouest/os-vm-expire/releases/download/0.9.4/python3-osvmexpire_0.9.4_all.deb

#. Install the packages:

   .. code-block:: console

      # apt-get update

      # dpkg -i python3-osvmexpire_0.9.4_all.deb

.. include:: common_configure.rst

.. include:: common_database.rst

Finalize installation
---------------------

Restart the OpenstackVm Expiration Management services:

.. code-block:: console

    # systemctl enable osvmexpire-api.service

    # systemctl start osvmexpire-api.service

    # systemctl enable osvmexpire-worker.service

    # systemctl start osvmexpire-worker.service

    # systemctl enable osvmexpire-cleaner.service

    # systemctl start osvmexpire-cleaner.service
