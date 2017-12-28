2. Edit the ``/etc/os_vm_expire/os_vm_expire.conf`` file and complete the following
   actions:

   * In the ``[database]`` section, configure database access:

     .. code-block:: ini

        [database]
        ...
        connection = mysql+pymysql://os_vm_expire:OS_VM_EXPIRE_DBPASS@controller/os_vm_expire


   * Minimum fields

     .. code-block:: ini

        [DEFAULT]
        # Optional, for debug
        # debug=true

        # Rabbitmq connection information
        transport_url = rabbit://stackrabbit:rabbitpassword@127.0.0.1:5672//

        # Nova exchange name for notifications
        control_exchange = nova
        # Host name, for use in HATEOAS-style references Note: Typically this
        # would be the load balanced endpoint that clients would use to
        # communicate back with this service. If a deployment wants to derive
        # host from wsgi request instead then make this blank. Blank is needed
        # to override default config value which is 'http://localhost:9411'
        # (string value)
        host_href = http://localhost:9411

        # Maximum life duration of VM in days (integer value)
        #max_vm_duration = 60

        # Maximum life extend of VM in days (integer value)
        #max_vm_extend = 30

        # Maximum life of VM in days, whatever the extends
        #max_vm_total_duration = 365

        [database]
        # SQLAlchemy connection string for the reference implementation
        # registry server. Any valid SQLAlchemy connection string is fine.
        # See:
        # http://www.sqlalchemy.org/docs/05/reference/sqlalchemy/connections.html#sqlalchemy.create_engine.
        # Note: For absolute addresses, use '////' slashes after 'sqlite:'.
        # (string value)
        connection=mysql+pysql://os_vm_expire:dbpassword@localhost/os_vm_expire

        [keystone_authtoken]
        auth_type = password
        username = os_vm_expire
        project_name = service
        user_domain_name = default
        auth_uri = http://127.0.0.1/identity/v3
        www_authenticate_uri = https://127.0.0.1/identity/v3
        auth_version = v3
        auth_url = http://127.0.0.1/identity/v3
        password = os_vm_expire_service_user_password
        project_domain_name = default
        # For backwards compatibility reasons we must let valid service tokens
        # pass that don't pass the service_token_roles check as valid. Setting
        # this true will become the default in a future release and should be
        # enabled if possible. (boolean value)
        service_token_roles_required = true

        [worker]
        # Openstack identity url (string value)
        #auth_uri = http://controller:5000/v3.0

        # service project name (string value)
        #admin_service = service

        # os-vm-expire service user id (string value)
        #admin_user = os_vm_expire

        # os-vm-expire service user password (string value)
        #admin_password = <None>

        # os-vm-expire user domain name (string value)
        #admin_user_domain_name = default

        # os-vm-expire service project domain name (string value)
        #admin_project_domain_name = default

        [cleaner]
        # Openstack identity url (string value)
        auth_uri = http://127.0.0.1/identity/v3
        # Openstack nova compute url (string value)
        nova_url = http://127.0.0.1:8774/compute/v2.1

        # service project name (string value)
        #admin_service = service

        # os-vm-expire service user id (string value)
        #admin_user = os_vm_expire

        # os-vm-expire service user password (string value)
        admin_password = os_vm_expire_service_user_password

        # os-vm-expire user domain name (string value)
        #admin_user_domain_name = default

        # os-vm-expire service project domain name (string value)
        #admin_project_domain_name = default

        # send expiration notification before X days
        #notify_before_days = 10

        # send expiration last notification before X days
        #notify_before_days_last = 2

        [nova_notifications]
        # True enables nova notification listener  functionality. (boolean
        # value)
        enable = true
        # The default exchange under which topics are scoped. May be
        # overridden by an exchange name specified in the transport_url
        # option. (string value)
        control_exchange = nova

        # nova notification queue topic name. This name needs to match one of
        # values mentioned in nova deployment's 'notification_topics'
        # configuration e.g.    notification_topics=notifications.info,
        # notifications.errorMultiple servers may listen on a topic and messages
        # will be dispatched to one of the servers in a round-robin fashion.
        # That's why os-vm-expire service should have its own dedicated
        # notification queue so that it receives all of nova notifications.
        # (string value)
        topic = versioned_notifications

        # Pool notification to listen on nova exchange.
        # Messages in same pool will get messages distributed,
        # while messages are copied over all pools
        #pool_name=os_vm_expire

        [queue]
        # True enables queuing, False invokes workers synchronously (boolean
        # value)
        enable = true
        # Queue namespace (string value)
        namespace = osvmexpire
        # Queue topic name (string value)
        topic = osvmexpire.workers
        # Server name for RPC task processing server (string value)
        server_name = osvmexpire.queue

        [smtp]
        # SMTP hostname (string value)
        email_smtp_host = 127.0.0.1
        # SMTP port (integer value)
        #email_smtp_port = 25
        # SMTP tls use? (boolean value)
        #email_smtp_tls = false
        # SMTP user (string value)
        #email_smtp_user = <None>
        # SMTP password (string value)
        email_smtp_from = support@mycompany.com
