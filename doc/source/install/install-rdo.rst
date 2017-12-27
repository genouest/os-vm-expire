.. _install-rdo:

Install and configure for Red Hat Enterprise Linux and CentOS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


This section describes how to install and configure the Openstack VmExpiration Management service
for Red Hat Enterprise Linux 7 and CentOS 7.

.. include:: common_prerequisites.rst

Install and configure components
--------------------------------

#. Get the rpm from git repo release (e.g. https://github.com/genouest/os-vm-expire/releases/tag/0.9.4)

   .. code-block:: console

      # wget https://github.com/genouest/os-vm-expire/releases/download/0.9.4/python-osvmexpire-0.9.4-1.el7.centos.noarch.rpm

#. Install the packages:

   .. code-block:: console

      # rpm -ivh python-osvmexpire-0.9.4-1.el7.centos.noarch.rpm

.. include:: common_configure.rst

.. include:: common_database.rst

Finalize installation
---------------------

Start the Openstack VmExpiration Management services and configure them to start when
the system boots:

.. code-block:: console

   # systemctl enable osvmexpire-api.service

   # systemctl start osvmexpire-api.service

   # systemctl enable osvmexpire-worker.service

   # systemctl start osvmexpire-worker.service

   # systemctl enable osvmexpire-cleaner.service

   # systemctl start osvmexpire-cleaner.service
