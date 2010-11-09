# -*- coding: utf-8 -*-
#
# Copyright 2009, 2010 Tobias Rodäbel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Setup script."""

import os
import setuptools


def read(*rnames):
    return open(os.path.join(os.getcwd(), *rnames)).read()


setuptools.setup(
    name='typhoonae',
    version=read('version.txt').strip(),
    author="Tobias Rodaebel",
    author_email="tobias dot rodaebel at googlemail dot com",
    description="Typhoon App Engine.",
    long_description=(
        read('README.txt')
        + '\n\n' +
        read('CHANGES.txt')
        ),
    license="Apache License 2.0",
    keywords=["gae", "appengine", "wsgi", "fastcgi"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
        ],
    url='http://code.google.com/p/typhoonae',
    packages=setuptools.find_packages('src'),
    include_package_data=True,
    package_dir={'': 'src'},
    install_requires=[
        'fcgiapp',
        'setuptools',
        'simplejson',
        ],
    extras_require=dict(
        amqp=['amqplib'],
        appcfg=['supervisor'],
        celery=['celery'],
        memcached=['pylibmc'],
        mongo=['pymongo'],
        mysql=['MySQL-python'],
        websocket=['tornado'],
        xmpp=['xmpppy']
        ),
    entry_points="""
        [console_scripts]
        appcfg_service = typhoonae.appcfg.service:main
        appserver = typhoonae.fcgiserver:main
        apptool = typhoonae.apptool:main
        deferred_taskworker = typhoonae.taskqueue.deferred_worker:main
        ejabberdauth = typhoonae.xmpp.ejabberdauth:main
        runtask = typhoonae.runtask:main
        taskworker = typhoonae.taskqueue.worker:main
        websocket = typhoonae.websocket.server:main
        xmpp_http_dispatch = typhoonae.xmpp.xmpp_http_dispatch:main
        imap_http_dispatch = typhoonae.mail.imap_http_dispatch:main""",
    zip_safe=False,
    )
