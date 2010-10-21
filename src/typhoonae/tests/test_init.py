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
"""Unit tests for the runtime environment."""

import os
import re
import sys
import typhoonae
import unittest


class InitTestCase(unittest.TestCase):
    """Tests a number of helper functions."""

    def setUp(self):
        """Loads the sample application."""

        app_root = os.path.join(os.path.dirname(__file__), 'sample')
        os.chdir(app_root)
        sys.path.insert(0, os.getcwd())
        self.conf = typhoonae.getAppConfig()
        assert self.conf.application == 'sample'

    def testSetupStubs(self):
        """Sets up apiproxy stubs."""

        class TestOptions:
            blobstore_path = 'blobstore'
            datastore = 'mongodb'
            http_port = 8080
            internal_address = 'localhost:8770'
            login_url = '/_ah/login'
            logout_url = '/_ah/logout'
            server_name = 'localhost'
            smtp_host = 'localhost'
            smtp_port = 25
            smtp_user = ''
            smtp_password = ''
            use_celery = False
            xmpp_host = 'localhost'

        typhoonae.setupStubs(self.conf, TestOptions())

    def testInitURLMapping(self):
        """Initializes the url/script map."""

        class TestOptions:
            login_url = '/_ah/login'
            logout_url = '/_ah/logout'

        url_mapping = typhoonae.initURLMapping(self.conf, TestOptions())
        for pattern, handler_path, path, login_required, admin_only in url_mapping:
            if pattern.match('/foo'):
                self.assertEqual(handler_path, 'app.py')
