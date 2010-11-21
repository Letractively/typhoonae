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
"""Unit tests for task queue."""

import datetime
import google.appengine.api.apiproxy_stub
import google.appengine.api.apiproxy_stub_map
import google.appengine.ext.deferred
import os
import time
import typhoonae.taskqueue
import typhoonae.taskqueue.taskqueue_stub
import unittest


class DummyURLFetchServiceStub(google.appengine.api.apiproxy_stub.APIProxyStub):
    def __init__(self, service_name='urlfetch'):
        super(DummyURLFetchServiceStub, self).__init__(service_name)

    def _Dynamic_Fetch(self, request, response):
        response.set_statuscode(500)


def do_something():
    """Dummy function to test the deferred API."""
    print "Did something."


class TaskQueueTestCase(unittest.TestCase):
    """Testing the typhoonae task queue."""

    def setUp(self):
        """Register typhoonae's task queue API proxy stub."""

        google.appengine.api.apiproxy_stub_map.apiproxy = \
                    google.appengine.api.apiproxy_stub_map.APIProxyStubMap()

        taskqueue = typhoonae.taskqueue.taskqueue_stub.TaskQueueServiceStub(
            internal_address='127.0.0.1:8770',
            root_path=os.path.dirname(__file__))
        google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
            'taskqueue', taskqueue)

        self.stub = google.appengine.api.apiproxy_stub_map.apiproxy.GetStub(
            'taskqueue')

        google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
            'urlfetch', DummyURLFetchServiceStub())

        # Setup environment
        self._os_environ = dict(os.environ)
        os.environ.clear()
        os.environ['SERVER_NAME'] = 'localhost'
        os.environ['SERVER_PORT'] = '8080'
        os.environ['TZ'] = 'UTC'
        time.tzset()

    def tearDown(self):
        """Tear down test environment."""

        os.environ.clear()
        os.environ.update(self._os_environ)

    def testStub(self):
        """Tests stub functions."""

        stub = typhoonae.taskqueue.taskqueue_stub.TaskQueueServiceStub(
            internal_address='127.0.0.1:8770',
            root_path=os.path.dirname(__file__))
        stub.connect()
        del stub

    def testTimeZone(self):
        """Tests custom UTC time zone class."""

        tz = typhoonae.taskqueue._UTCTimeZone()
        self.assertEqual('UTC', tz.tzname(''))

    def testETA(self):
        """Tests helper functions for computing task execution time."""

        unused_eta = typhoonae.taskqueue.get_new_eta_usec(2)
        eta = typhoonae.taskqueue.get_new_eta_usec(0)
        assert typhoonae.taskqueue.is_deferred_eta(eta) == True
        t = datetime.datetime.now() - datetime.timedelta(seconds=20)
        eta = time.mktime(t.replace(tzinfo=typhoonae.taskqueue.UTC).timetuple())
        assert typhoonae.taskqueue.is_deferred_eta(eta) == False

    def testAddingTasks(self):
        """Tests for adding tasks."""

        google.appengine.api.taskqueue.add(url='/run')
        google.appengine.api.taskqueue.Queue('test').add(
            google.appengine.api.taskqueue.Task(url='/foo'))

        self.assertRaises(
            google.appengine.api.taskqueue.UnknownQueueError,
            google.appengine.api.taskqueue.Queue('unknown').add,
            google.appengine.api.taskqueue.Task(url='/foo'))

    def testAddingTaskWithContentType(self):
        """Adds a task with a distinct content-type header."""

        google.appengine.api.taskqueue.add(
            url='/run', params={'foo': 'bar'})

    def testAddingTaskWithMethod(self):
        """Adds a task with an HTTP method other than default."""

        google.appengine.api.taskqueue.add(
            url='/put', params={'foo': 'bar'}, method='PUT')

    def testBulkAdd(self):
        """Adds multiple tasks at once."""

        google.appengine.api.taskqueue.Queue('test').add([
            google.appengine.api.taskqueue.Task(url='/foo'),
            google.appengine.api.taskqueue.Task(url='/bar'),
        ])

    def testGetQueues(self):
        """Tries to obtain existing queues."""

        self.assertEqual([], self.stub.GetQueues())

    def testDeferred(self):
        """Testing deferred API."""

        google.appengine.ext.deferred.defer(
            do_something, _name='deferred', _countdown=10)
