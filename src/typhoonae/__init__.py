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
"""Helper functions for registering App Engine API proxy stubs."""

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import appinfo
import logging
import os
import re


SUPPORTED_DATASTORES = frozenset([
    'bdbdatastore', 'mongodb', 'mysql', 'remote'])

end_request_hook = None


def getAppConfig(directory='.'):
    """Returns a configuration object."""

    path = os.path.join(directory, 'app.yaml')
    conf_file = open(path, 'r')

    try:
        conf = appinfo.LoadSingleAppInfo(conf_file)
    except IOError:
        raise RuntimeError
    finally:
        conf_file.close()

    return conf


def initURLMapping(conf, options):
    """Returns a list with mappings URL to module name and script."""

    url_mapping = []

    add_handlers = [
        appinfo.URLMap(url=url, script=script)
        for url, script in [
            # Configure script with login handler
            (options.login_url, '$PYTHON_LIB/typhoonae/handlers/login.py'),
            # Configure script with logout handler
            (options.logout_url, '$PYTHON_LIB/typhoonae/handlers/login.py'),
            # Configure script with images handler
            ('/_ah/img(?:/.*)?', '$PYTHON_LIB/typhoonae/handlers/images.py'),
            # Configure script with Channel JS API handler
            ('/_ah/channel/jsapi', '$PYTHON_LIB/typhoonae/channel/jsapi.py'),
            # Configure script with Channel JS API handler
            ('/_ah/dev/null', '$PYTHON_LIB/typhoonae/handlers/devnull.py')
        ] if url not in [h.url for h in conf.handlers if h.url]
    ]

    # Generate URL mapping
    for handler in add_handlers + conf.handlers:
        script = handler.script
        regexp = handler.url
        if script != None:
            if script.startswith('$PYTHON_LIB'):
                module = script.replace(os.sep, '.')[12:]
                if module.endswith('.py'):
                    module = module[:-3]
                try:
                    m = __import__(module)
                except Exception, err_obj:
                    logging.error(
                        "Could not initialize script '%s'. %s: %s" %
                        (script, err_obj.__class__.__name__, err_obj)
                    )
                    continue
                p = os.path.dirname(m.__file__).split(os.sep)
                path = os.path.join(os.sep.join(p[:len(p)-1]), script[12:])
            else:
                path = os.path.join(os.getcwd(), script)
                if path.startswith(os.sep) and not os.path.isfile(path):
                    path = path[1:]

            if not regexp.startswith('^'):
                regexp = '^' + regexp
            if not regexp.endswith('$'):
                regexp += '$'
            compiled = re.compile(regexp)
            login_required = handler.login in ('required', 'admin')
            admin_only = handler.login in ('admin',)
            url_mapping.append(
                (compiled, script, path, login_required, admin_only))

    return url_mapping


def setupCapability():
    """Sets up cabability service."""

    from typhoonae import capability_stub

    apiproxy_stub_map.apiproxy.RegisterStub(
        'capability_service', capability_stub.CapabilityServiceStub())


def setupDatastore(options, conf, datastore_file, history, require_indexes, trusted):
    """Sets up datastore."""

    name = options.datastore.lower()

    if name == 'mongodb':
        from typhoonae.mongodb import datastore_mongo_stub
        datastore = datastore_mongo_stub.DatastoreMongoStub(
            conf.application, require_indexes=require_indexes)
    elif name == 'bdbdatastore':
        from notdot.bdbdatastore import socket_apiproxy_stub
        datastore = socket_apiproxy_stub.RecordingSocketApiProxyStub(
            ('localhost', 9123))
        global end_request_hook
        end_request_hook = datastore.closeSession
    elif name == 'mysql':
        from typhoonae.mysql import datastore_mysql_stub
        database_info = {
            "host": options.mysql_host,
            "user": options.mysql_user,
            "passwd": options.mysql_passwd,
            "db": options.mysql_db
        }
        datastore = typhoonae.mysql.datastore_mysql_stub.DatastoreMySQLStub(
            conf.application, database_info, verbose=options.debug_mode)
    else:
        raise RuntimeError, "unknown datastore"

    apiproxy_stub_map.apiproxy.RegisterStub(
        'datastore_v3', datastore)

    if name == 'bdbdatastore':
        from google.appengine.tools import dev_appserver_index
        app_root = os.getcwd()
        logging.info("%s" % app_root)
        dev_appserver_index.SetupIndexes(conf.application, app_root)
        dev_appserver_index.IndexYamlUpdater(app_root)


def setupMail(smtp_host, smtp_port, smtp_user, smtp_password,
              enable_sendmail=False, show_mail_body=False):
    """Sets up mail."""

    from google.appengine.api import mail_stub

    apiproxy_stub_map.apiproxy.RegisterStub('mail',
        mail_stub.MailServiceStub(
            smtp_host, smtp_port, smtp_user, smtp_password,
            enable_sendmail=enable_sendmail, show_mail_body=show_mail_body))


def setupMemcache():
    """Sets up memcache."""

    from typhoonae.memcache import memcache_stub

    apiproxy_stub_map.apiproxy.RegisterStub('memcache',
        memcache_stub.MemcacheServiceStub())


def setupTaskQueue(internal_address, use_celery=False, root_path='.'):
    """Sets up task queue.

    Args:
        internal_address: Address to be used for internal HTTP communication.
        root_path: The app's root directory.
    """

    if use_celery:
        from typhoonae.taskqueue import taskqueue_celery_stub as taskqueue_stub
    else:
        from typhoonae.taskqueue import taskqueue_stub

    apiproxy_stub_map.apiproxy.RegisterStub('taskqueue',
        taskqueue_stub.TaskQueueServiceStub(
            internal_address=internal_address, root_path=root_path))


def setupURLFetchService():
    """Sets up urlfetch."""

    from google.appengine.api import urlfetch_stub

    apiproxy_stub_map.apiproxy.RegisterStub('urlfetch',
        urlfetch_stub.URLFetchServiceStub())


def setupUserService(login_url='/_ah/login', logout_url='/_ah/logout'):
    """Sets up user service.

    Args:
        login_url: The login URL.
        logout_url: The logout URL.
    """

    from google.appengine.api import user_service_stub

    apiproxy_stub_map.apiproxy.RegisterStub('user',
        user_service_stub.UserServiceStub(
            login_url=login_url+'?continue=%s',
            logout_url=logout_url+'?continue=%s'))


def setupXMPP(host):
    """Sets up XMPP.

    Args:
        host: Hostname of the XMPP service.
    """
    from typhoonae.xmpp import xmpp_service_stub

    apiproxy_stub_map.apiproxy.RegisterStub('xmpp',
        xmpp_service_stub.XmppServiceStub(host=host))


def setupChannel(internal_addr):
    """Sets up Channel API.

    Args:
        internal_addt: Internal address of the Channel service.
    """
    from typhoonae.channel import channel_service_stub

    apiproxy_stub_map.apiproxy.RegisterStub('channel',
      channel_service_stub.ChannelServiceStub(internal_addr))

    # We have to monkeypatch the SDK to avoid renaming the SERVER_SOFTWARE
    # variable.
    from google.appengine.api.channel import channel
    channel._GetService = lambda : 'channel'


def setupBlobstore(blobstore_path, app_id):
    """Sets up blobstore service.

    Args:
        blobstore_path: Directory within which to store blobs.
        app_id: App id to store blobs on behalf of.
    """
    from typhoonae.blobstore import blobstore_stub
    from typhoonae.blobstore import file_blob_storage

    storage = file_blob_storage.FileBlobStorage(
        blobstore_path, app_id)
    apiproxy_stub_map.apiproxy.RegisterStub(
        'blobstore',
        blobstore_stub.BlobstoreServiceStub(storage))


def setupWebSocket():
    """Sets up Web Socket service."""
    from typhoonae.websocket import websocket_stub

    apiproxy_stub_map.apiproxy.RegisterStub(
        'websocket', websocket_stub.WebSocketServiceStub())


def setupRemoteDatastore(app_id, email, password):
    """Enables remote API mode for all datastore operations.

    Args:
        app_id: Valid GAE app id.
        email: User email.
        password: User password.
    """

    from google.appengine.ext.remote_api import remote_api_stub
    remote_api_stub.ConfigureRemoteApi(
        app_id, '/remote_api', lambda:(email, password), secure=True,
        servername=app_id+'.appspot.com', services=['datastore_v3'])
    remote_api_stub.MaybeInvokeAuthentication()


def setupStubs(conf, options):
    """Sets up api proxy stubs.

    Args:
        conf: An appinfo.AppInfoExternal instance.
        options: Dictionary with command line options.
    """
    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()

    datastore = options.datastore.lower()

    if datastore in SUPPORTED_DATASTORES:
        if datastore == 'remote':
            setupRemoteDatastore(
                conf.application, options.email, options.password)
        else:
            setupDatastore(options,
                           conf,
                           'dev_appserver.datastore',
                           'dev_appserver.datastore.history',
                           False,
                           False)

    setupCapability()

    setupMail(options.smtp_host, options.smtp_port,
              options.smtp_user, options.smtp_password)

    setupMemcache()

    setupTaskQueue(options.internal_address, use_celery=options.use_celery)

    setupURLFetchService()

    setupUserService(options.login_url, options.logout_url)

    setupBlobstore(options.blobstore_path, conf.application)

    setupChannel(options.internal_address)

    if conf.inbound_services:
        inbound_services = conf.inbound_services
    else:
        inbound_services = []

    if 'xmpp_message' in inbound_services:
        setupXMPP(options.xmpp_host)

    setupWebSocket()

    try:
        from google.appengine.api.images import images_stub
        host_prefix = 'http://%s:%s' % (options.server_name, options.http_port)
        apiproxy_stub_map.apiproxy.RegisterStub(
            'images',
            images_stub.ImagesServiceStub(host_prefix=host_prefix))
    except ImportError, e:
        logging.warning('Could not initialize images API; you are likely '
                        'missing the Python "PIL" module. ImportError: %s', e)
        from google.appengine.api.images import images_not_implemented_stub
        apiproxy_stub_map.apiproxy.RegisterStub(
            'images',
            images_not_implemented_stub.ImagesNotImplementedServiceStub())
