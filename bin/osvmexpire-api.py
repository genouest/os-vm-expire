#!/usr/bin/env python

# Copyright  2017 IRISA
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


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
