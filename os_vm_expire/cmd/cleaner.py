#!/usr/bin/env python

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Osvmexpire worker server.
"""
import datetime
from email.mime.text import MIMEText
import eventlet
import os
import smtplib
import sys
import time


from os_vm_expire.common import config
from os_vm_expire.common import utils
from os_vm_expire.model import repositories
from os_vm_expire import version

from oslo_log import log
from oslo_service import service

# import futurist
from futurist import periodics
import requests

# Oslo messaging RPC server uses eventlet.
eventlet.monkey_patch()

# 'Borrowed' from the Glance project:
# If ../os_vm_expire/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
base_local_dir = os.path.join(possible_topdir, 'os_vm_expire', '__init__.py')
if os.path.exists(base_local_dir):
    sys.path.insert(0, possible_topdir)


LOG = utils.getLogger(__name__)


def fail(returncode, e):
    sys.stderr.write("ERROR: {0}\n".format(e))
    sys.exit(returncode)


def delete_vm(instance_id, project_id, token):
    '''Delete a VM on expiration

    conf in [cleaner]
    nova_url = http://controller.genouest.org:8774/v2.1/%(tenant_id)s
    '''
    nova_url = config.CONF.cleaner.nova_url % {
        'tenant_id': project_id,
        'project_id': project_id
        }
    LOG.debug('Nova URI:' + nova_url)
    headers = {
        'X-Auth-Token': token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    r = requests.delete(nova_url + '/servers/' + instance_id, headers=headers)
    if r.status_code != 204:
        LOG.error('Failed to delete instance ' + str(instance_id))
        return False
    else:
        LOG.info('DELETE:' + str(instance_id) + ':' + str(project_id))
        return True


def get_identity_token():
    conf_cleaner = config.CONF.cleaner
    ks_uri = conf_cleaner.auth_uri

    auth = {
        'auth': {
            'scope':
                {'project': {
                    'name': conf_cleaner.admin_service,
                    'domain':
                        {
                            'name': conf_cleaner.admin_project_domain_name
                        }
                    }
                 },
            'identity': {
                    'password': {
                        'user': {
                            'domain': {
                                'name': conf_cleaner.admin_user_domain_name
                            },
                            'password': conf_cleaner.admin_password,
                            'name': conf_cleaner.admin_user
                        }
                    },
                    'methods': ['password']
                }
        }
    }
    r = requests.post(ks_uri + '/auth/tokens', json=auth)
    if 'X-Subject-Token' not in r.headers:
        LOG.error('Could not get authorization')
        return None
    token = r.headers['X-Subject-Token']
    return token


def get_project_name(project_id, token):
    LOG.debug("Get project name")
    # fetch user from identity to get user email
    headers = {
        'X-Auth-Token': token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    ks_uri = config.CONF.cleaner.auth_uri
    try:
        r = requests.get(ks_uri + '/projects/' + project_id, headers=headers)
    except Exception:
        LOG.exception('Failed to get project name for id ' + str(project_id))
        return None
    if r.status_code != 200:
        return None
    project = r.json()
    if 'project' in project:
        return project['project']['name']
    return None


def send_email(instance, token, delete=False):
    LOG.debug("Send expiration notification mail")
    # fetch user from identity to get user email
    headers = {
        'X-Auth-Token': token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    ks_uri = config.CONF.cleaner.auth_uri
    r = requests.get(ks_uri + '/users/' + instance.user_id, headers=headers)
    if r.status_code != 200:
        return False
    user = r.json()
    email = None
    if 'user' in user and 'email' in user['user']:
        email = user['user']['email']
    if email is None:
        LOG.error('Could not get email for user ' + instance.user_id)
        return False
    # send email
    to = [email]
    if delete and config.CONF.smtp.email_smtp_copy_delete_notif_to is not None:
        to = [email, config.CONF.smtp.email_smtp_copy_delete_notif_to]

    project_name = get_project_name(instance.project_id, token)

    if project_name is None:
        project_name = instance.project_id

    subject = 'VM %s [project: %s] expiration' % (
        str(instance.instance_name),
        project_name
    )

    message = ('VM %s (id: %s, project: %s) will expire at %s,' +
               'connect to dashboard to extend its duration else ' +
               ' it will be deleted.') % (
        instance.instance_name,
        instance.instance_id,
        instance.project_id,
        str(datetime.datetime.fromtimestamp(instance.expire))
        )
    if delete:
        message = ('VM %s (id: %s, project: %s) has expired at %s' +
                   ' and has been deleted.') % (
            instance.instance_name,
            instance.instance_id,
            instance.project_id,
            str(datetime.datetime.fromtimestamp(instance.expire))
            )
    LOG.info('NOTIF:' + instance.id + ':' + str(message))
    # Create a text/plain message
    msg = MIMEText(message)

    msg['Subject'] = subject
    msg['From'] = config.CONF.smtp.email_smtp_from
    if msg['From'] is None:
        LOG.error('Missing smtp.email_smtp_from in config')
        return False
    msg['To'] = ', '.join(to)

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    try:
        s = smtplib.SMTP(config.CONF.smtp.email_smtp_host,
                         config.CONF.smtp.email_smtp_port)
        if config.CONF.smtp.email_smtp_tls:
            s.starttls()
        if config.CONF.smtp.email_smtp_user:
            s.login(config.CONF.smtp.email_smtp_user,
                    config.CONF.smtp.email_smtp_password)
        s.sendmail(msg['From'], to, msg.as_string())
        s.quit()
    except Exception:
        LOG.error('Failed to send expiration notification mail to ' + email)
        return False

    return True


# Every hour
@periodics.periodic(3600)
def check(started_at):
    token = get_identity_token()
    conf_cleaner = config.CONF.cleaner
    LOG.debug("check instances")
    repo = repositories.get_vmexpire_repository()
    now = int(time.mktime(datetime.datetime.now().timetuple()))
    check_time = now + (conf_cleaner.notify_before_days * 3600 * 24)
    last_check_time = now + (conf_cleaner.notify_before_days_last * 3600 * 24)
    entities = repo.get_entities(expiration_filter=check_time)
    for entity in entities:
        if entity.expire < check_time and not entity.notified:
            # notify
            LOG.debug("First expiration notification %s" % (entity.id))
            res = send_email(entity, token, delete=False)
            if res:
                entity.notified = True
                try:
                    entity.save()
                    repositories.commit()
                except Exception as e:
                    LOG.exception("expiration save error: " + str(e))
                    repositories.rollback()
        elif entity.expire < last_check_time and not entity.notified_last:
            # notify_last
            LOG.debug("Last expiration notification %s" % (entity.id))
            res = send_email(entity, token, delete=False)
            if res:
                entity.notified_last = True
                try:
                    entity.save()
                    repositories.commit()
                except Exception as e:
                    LOG.exception("expiration save error: " + str(e))
                    repositories.rollback()
        elif entity.expire < now:
            # delete
            LOG.debug("Delete VM %s" % (entity.id))
            res = delete_vm(entity.instance_id, entity.project_id, token)
            if res:
                try:
                    repo.delete_entity_by_id(entity_id=entity.id)
                    repositories.commit()
                except Exception as e:
                    LOG.exception("expiration deletion error: " + str(e))
                    repositories.rollback()
            send_email(entity, token, delete=True)


class CleanerServer(service.Service):

    def __init__(self):
        super(CleanerServer, self).__init__()
        repositories.setup_database_engine_and_factory()
        started_at = time.time()
        callables = [(check, (started_at,), {})]
        self.w = periodics.PeriodicWorker(callables)

    def start(self):
        LOG.info("Starting the CleanerServer")
        self.w.start()
        super(CleanerServer, self).start()

    def stop(self):
        LOG.info("Halting the CleanerServer")
        self.w.stop()
        super(CleanerServer, self).stop()


def main():
    try:
        config.CONF(sys.argv[1:],
                    project='os-vm-expire',
                    version=version.version_info.version_string)

        # Import and configure logging.
        log.setup(config.CONF, 'osvmexpire')
        LOG = log.getLogger(__name__)
        LOG.debug("Booting up os-vm-expire cleaner node...")

        service.launch(
            config.CONF,
            CleanerServer(),
            workers=1
        ).wait()

    except RuntimeError as e:
        fail(1, e)


if __name__ == '__main__':
    main()
