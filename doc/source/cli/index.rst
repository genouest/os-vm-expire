================================
Command line interface reference
================================

Those command-line tools need access to configuration file, so are dedicated to administer the tool, not for end user.

osvmexpire-manage
=================

Manage expirations

.. code-block:: bash

  osvmexpire-manage vm list
  osvmexpire-manage vm extend -h
  osvmexpire-manage vm remove -h
  osvmexpire-manage exclude list
  osvmexpire-manage exclude add -h
  osvmexpire-manage exclude delete -h

osvmexpire-db-manage
====================

Manage database creation and upgrades

.. code-block:: bash

  osvmexpire-db-manage -h
