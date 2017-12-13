====================
Administrators guide
====================

Services
========

API, worker and cleaner services should be ran via systemd.

Tasks
=====

Cleaner service task is triggered every hour to check VM expirations.

Worker is connected to nova notifications to be informed on new VM creation/deletion.
Start/stop operation do not impact the expiration itself.
Only VM is deleted, not linked volumes.
