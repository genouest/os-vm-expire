===============================
About
===============================

Manage VM expiration and auto-deletion in an Openstack cloud.

This project is an unofficial Openstack project, but follows Openstack projects architecture, with a Horizon plugin and associated services.


* Free software: Apache license
* Documentation: http://os-vm-expire.readthedocs.io/
* Bugs: https://github.com/genouest/os-vm-expire/issues
* Horizon plugin: https://github.com/genouest/os-vm-expire-horizon-plugin
* OSC plugin (openstack client): https://github.com/genouest/os-vm-expire-osc-plugin

The Openstack VmExpiration Management service adds an expiration to VMs.
After expiration, VM is deleted.
User can extend the VM lifetime via API or Horizon.
Expiration extend is not limited, user can always extend a VM, but it will be extended only for a configured duration.
User cannot extend it more than configured duration.
Example:

  - date A: VM is created, VM will expire at A + N days
  - some days before expiration user is notified
  - user extend VM to today + M days (M is configuration based, user cannot specify it)
  - if user tries to extend VM again, it will be extend again to today + M days


Requirements
------------

Nova notifications need to be enabled to get VM start and end messages.

Software has been tested on **Pike** and **Otaca**, and in single and multi domain configuration. It *should* work from **Newton**.

Features
--------

* On VM creation, add an expiration date
* On near-expiration date, send an email to user
* Horizon plugin to view VM expiration and extend expiration time
* On expiration date, delete the VM and send an email to user
* CLI commands to extend a VM or remove expiration from a VM (admin only)


Configuration
-------------

Configuration files are expected in directory /etc/os-vm-expire/ :

* osvmexpire.conf
* policy.json
* osvmexpire-api-paste.ini (for wsgi server)

Main configuration file can be specified via environment variable OSVMEXPIRE_CONFIG.

Components
----------


Start API server
~~~~~~~~~~~~~~~~

For dev (port 8000)

.. code-block:: bash

  export OSVMEXPIRE_PORT=9411 # optional
  osvmexpire-wsgi-api

For prod

.. code-block:: bash

  uwsgi --master --die-on-term --emperor /etc/os-vm-expire/vassals --logto /var/log/os-vm-expire/osvmexpire-api.log --stats localhost:9314


Start worker
~~~~~~~~~~~~

Manage nova notifications on instance creation and deletion to create/delete expiration objects.

.. code-block:: bash

  osvmexpire-worker --config-file /etc/os-vm-expire/osvmexpire.conf


Start cleaner
~~~~~~~~~~~~~

Checks expiration time of VMs and sends notifications before expiration to let use extend the VM if necessary.
Once expiration is reached (and if user could be notified of expiration), deletes the VM.

.. code-block:: bash

  osvmexpire-cleaner --config-file /etc/os-vm-expire/osvmexpire.conf

CLI usage
---------

Those command-line tools need access to configuration file, so are dedicated to administer the tool, not for end user.

.. code-block:: bash

  osvmexpire-manage vm list
  osvmexpire-manage vm extend -h
  osvmexpire-manage vm remove -h


Credits
-------

Code is mostly inspired (code base coming from) the Barbican Openstack project, code was more or less updated to manage different objects.
This project takes the same license and kept original file headers.

This project was developed by the GenOuest core facility, IRISA, France.
