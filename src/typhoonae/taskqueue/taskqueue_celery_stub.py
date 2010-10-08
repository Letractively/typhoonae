# -*- coding: utf-8 -*-
#
# Copyright 2009, 2010 Tobias Rodäbel, Joaquin Cuenca Abela
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
"""Task queue API proxy stub."""

from celery.task.base import Task

import base64
import celery_tasks
import google.appengine.api.apiproxy_stub
import google.appengine.api.labs.taskqueue.taskqueue_service_pb
import google.appengine.api.labs.taskqueue.taskqueue_stub
import google.appengine.api.urlfetch
import google.appengine.runtime.apiproxy_errors
import logging
import os
import simplejson
import socket
import time
import typhoonae.taskqueue


class TaskQueueServiceStub(google.appengine.api.apiproxy_stub.APIProxyStub):
    """Task queue service stub."""

    pyaml = google.appengine.api.labs.taskqueue.taskqueue_stub._ParseQueueYaml

    def __init__(
            self,
            internal_address,
            service_name='taskqueue',
            root_path=None):
        """Initialize the Task Queue API proxy stub.

        Args:
            internal_address: The internal host and port of where the
                appserver lives.
            service_name: Service name expected for all calls.
            root_path: The app's root directory.
        """
        super(TaskQueueServiceStub, self).__init__(service_name)

        (self._internal_host, self._internal_port) = internal_address.split(':')

        self.next_task_id = 1
        self.root_path = root_path
        self._SetupQueues()

    def _SetupQueues(self):
        self.celery_tasks_for_queues = (
            celery_tasks.create_task_queues_from_yaml(self.root_path))

    def _ValidQueue(self, queue_name):
        if queue_name == 'default':
            return True
        return queue_name in self.celery_tasks_for_queues

    def _Dynamic_Add(self, request, response):
        bulk_request = taskqueue_service_pb.TaskQueueBulkAddRequest()
        bulk_response = taskqueue_service_pb.TaskQueueBulkAddResponse()

        bulk_request.add_add_request().CopyFrom(request)
        self._Dynamic_BulkAdd(bulk_request, bulk_response)

        assert bulk_response.taskresult_size() == 1
        result = bulk_response.taskresult(0).result()

        if result != taskqueue_service_pb.TaskQueueServiceError.OK:
            raise google.appengine.runtime.apiproxy_errors.ApplicationError(
                result)
        elif bulk_response.taskresult(0).has_chosen_task_name():
            response.set_chosen_task_name(
                bulk_response.taskresult(0).chosen_task_name())

    def _RunAsync(self, **kwargs):
        queue_name = kwargs.get('queue', 'default')
        task = self.celery_tasks_for_queues.get(queue_name)
        if task is None:
            raise google.appengine.runtime.apiproxy_errors.ApplicationError(
                google.appengine.api.labs.taskqueue.taskqueue_service_pb.
                TaskQueueServiceError.UNKNOWN_QUEUE)
        countdown = max(0, kwargs['eta'] - time.time())
        logging.warning('Queueing task with ETA %r and countdown %r',
                        kwargs['eta'], countdown)
        task.apply_async(kwargs=kwargs,
                         countdown=countdown,
                         expires=30 * 24 * 3600)

    def _Dynamic_BulkAdd(self, request, response):
        """Add many tasks to a queue using a single request.

        Args:
            request: The taskqueue_service_pb.TaskQueueBulkAddRequest. See
                taskqueue_service.proto.
            response: The taskqueue_service_pb.TaskQueueBulkAddResponse. See
                taskqueue_service.proto.
        """

        assert request.add_request_size(), 'empty requests not allowed'

        if not self._ValidQueue(request.add_request(0).queue_name()):
            raise google.appengine.runtime.apiproxy_errors.ApplicationError(
                google.appengine.api.labs.taskqueue.taskqueue_service_pb.
                TaskQueueServiceError.UNKNOWN_QUEUE)

        for add_request in request.add_request_list():

            content_type = 'text/plain'
            for h in add_request.header_list():
                if h.key() == 'content-type':
                    content_type = h.value()

            task_dict = dict(
                content_type=content_type,
                eta=add_request.eta_usec()/1000000,
                host=self._internal_host,
                method=add_request.RequestMethod_Name(add_request.method()),
                name=add_request.task_name(),
                payload=base64.b64encode(add_request.body()),
                port=self._internal_port,
                queue=add_request.queue_name(),
                try_count=0,
                url=add_request.url(),
            )

            self._RunAsync(**task_dict)
            task_result = response.add_taskresult()

    def GetQueues(self):
        """Gets all the applications's queues.

        Returns:
            A list of dictionaries, where each dictionary contains one queue's
            attributes.
        """
        queues = []

        return queues
