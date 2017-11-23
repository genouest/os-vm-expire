2. Edit the ``/etc/os_vm_expire/os_vm_expire.conf`` file and complete the following
   actions:

   * In the ``[database]`` section, configure database access:

     .. code-block:: ini

        [database]
        ...
        connection = mysql+pymysql://os_vm_expire:OS_VM_EXPIRE_DBPASS@controller/os_vm_expire
