=============
Configuration
=============

Configuration of os-vm-expire.

The osvmexpire.conf contains the configuration for the different services.

*nova_notifications* section contains information to connect to the nova exchange,
to fetch notifications message (versoined_notifications)

*smtp* section is used to send emails to end-user before final expiration.

*keystone_authtoken* section needs to be adapted to your identity configuration (url, etc.)
os-vm-expire works only with v3 authentication.

*cleaner* section is specific to osvmexpire-cleaner service.

Policy.json should be used to defined policy access rules to API endpoints and should also be used for Horizon ACLs.

Templates can be found in et/oslo-config-generator for osvmexpire.conf and policy.json
