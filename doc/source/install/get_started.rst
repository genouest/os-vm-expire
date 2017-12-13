==================================================
Openstack VmExpiration Management service overview
==================================================

The Openstack VmExpiration Management service consists of the following components:

  ``osvmexpire-api`` service
  Accepts and responds to end user os-vm-expire API calls...

  ``osvmexpire-worker`` service
  Receive nova notifications on VM creation/deletion to create/delete expirations for VMs.

  ``osvmexpire-cleaner`` service
  Checks at regular interval for VM expiration, sends email notifications to user before final deletion of the VM.

Systemd templates can be found in etc/systemd/system directory.
