#!/usr/bin/env python

import os
from paste import deploy
from paste import httpserver


def run():
    vmexpire_port = '9411'
    if 'OSVMEXPIRE_PORT' in os.environ:
        vmexpire_port = os.environ['OSVMEXPIRE_PORT']

    prop_dir = 'etc/os-vm-expire'
    if not os.path.exists('/etc/os-vm-expire/osvmexpire-api-paste.ini'):
        application = deploy.loadapp(
            'config:{prop_dir}/osvmexpire-api-paste.ini'.
            format(prop_dir=prop_dir), name='main', relative_to='.')
    else:
        application = deploy.loadapp(
            'config:{prop_dir}/osvmexpire-api-paste.ini'.
            format(prop_dir=prop_dir), name='main', relative_to='/')

    httpserver.serve(application, host='0.0.0.0', port=vmexpire_port)


if __name__ == '__main__':
    run()
