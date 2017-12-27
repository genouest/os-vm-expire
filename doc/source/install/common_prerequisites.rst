Prerequisites
-------------

Before you install and configure the Openstack VmExpiration Management service,
you must create a database, service credentials, and API endpoints.

#. To create the database, complete these steps:

   * Use the database access client to connect to the database
     server as the ``root`` user:

     .. code-block:: console

        $ mysql -u root -p

   * Create the ``os_vm_expire`` database:

     .. code-block:: none

        CREATE DATABASE os_vm_expire;

   * Grant proper access to the ``os_vm_expire`` database:

     .. code-block:: none

        GRANT ALL PRIVILEGES ON os_vm_expire.* TO 'os_vm_expire'@'localhost' \
          IDENTIFIED BY 'OS_VM_EXPIRE_DBPASS';
        GRANT ALL PRIVILEGES ON os_vm_expire.* TO 'os_vm_expire'@'%' \
          IDENTIFIED BY 'OS_VM_EXPIRE_DBPASS';

     Replace ``OS_VM_EXPIRE_DBPASS`` with a suitable password.

   * Exit the database access client.

     .. code-block:: none

        exit;

#. Source the ``admin`` credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc

#. To create the service credentials, complete these steps:

   * Create the ``os_vm_expire`` user:

     .. code-block:: console

        $ openstack user create --domain default --password-prompt os_vm_expire

   * Add the ``admin`` role to the ``os_vm_expire`` user:

     .. code-block:: console

        $ openstack role add --project service --user os_vm_expire admin

   * Create the os_vm_expire service entities:

     .. code-block:: console

        $ openstack service create --name os_vm_expire --description "Openstack VmExpiration Management" vmexpire

#. Create the Openstack VmExpiration Management service API endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        vmexpire public http://controller:9411/v1/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        vmexpire internal http://controller:9411/v1/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        vmexpire admin http://controller:9411/v1/%\(tenant_id\)s
