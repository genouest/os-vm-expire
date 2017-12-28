===========
Users guide
===========

Users guide of os-vm-expire.

When a VM is started, a new expiration is set for the VM. When expiration is reached, VM is deleted.
2 email notifications are sent before expiration, at intervals defined in configuration.

User can extend the life of a VM at any time, but its expiration will only be extended of MAX_VM_EXTEND_DAYS days, from current day.

To extend VM expiration, one can use the Horizon dashboard or the API of os-vm-expire.
For more details on API, see `OpenStack VMExpiration Management API
<../api-ref/index.html>`_


Some domain/project/user ids can be ignored via exclusion. Only administrator can create an exclusion.
