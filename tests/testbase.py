
import logging
import os
import sys
import time
import unittest

SERVICE_NAME = "notificationsvc"

#Add SERVICE_ROOT to python path, for imports.
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", SERVICE_NAME))
sys.path.insert(0, SERVICE_ROOT)

from tridlcore.gen.ttypes import RequestContext
from trpycore.zookeeper.client import ZookeeperClient
from trsvcscore.service.default import DefaultService
from trsvcscore.service.server.default import ThriftServer
from trsvcscore.proxy.zoo import ZookeeperServiceProxy
from trnotificationsvc.gen import TNotificationService

from handler import NotificationServiceHandler


class NotificationTestService(DefaultService):
    def __init__(self, hostname, port):

        self.handler = NotificationServiceHandler(self)

        server = ThriftServer(
            name="%s-thrift" % SERVICE_NAME,
            interface="0.0.0.0",
            port=port,
            handler=self.handler,
            processor=TNotificationService.Processor(self.handler),
            threads=1)

        super(NotificationTestService, self).__init__(
            name=SERVICE_NAME,
            version="unittest-version",
            build="unittest-build",
            servers=[server],
            hostname=hostname,
            fqdn=hostname)


class IntegrationTestCase(unittest.TestCase):
    """
    This class assumes that the service is already running.
    """

    @classmethod
    def setUpClass(cls):

        logging.basicConfig(level=logging.DEBUG)

        cls.service = NotificationTestService("localhost", 9095)
        cls.service.start()
        time.sleep(1)

        cls.service_name = SERVICE_NAME
        cls.service_class = TNotificationService

        cls.zookeeper_client = ZookeeperClient(["localdev:2181"])
        cls.zookeeper_client.start()
        time.sleep(1)

        cls.service_proxy = ZookeeperServiceProxy(cls.zookeeper_client, cls.service_name, cls.service_class, keepalive=True)
        cls.request_context = RequestContext(userId=0, impersonatingUserId=0, sessionId="dummy_session_id", context="")

    @classmethod
    def tearDownClass(cls):
        cls.zookeeper_client.stop()
        cls.zookeeper_client.join()
        cls.service.stop()
        cls.service.join()


class DistributedTestCase(unittest.TestCase):
    """
    This class creates and starts two instances of the Notification Service.
    """

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

        cls.service = NotificationTestService("localhost", 9095)
        cls.service.start()
        time.sleep(1)

        cls.service2 = NotificationTestService("localhost", 9096) #TODO need to specify some test ports on wiki
        cls.service2.start()
        time.sleep(1)

        cls.service_name = SERVICE_NAME
        cls.service_class = TNotificationService

        cls.zookeeper_client = ZookeeperClient(["localdev:2181"])
        cls.zookeeper_client.start()
        time.sleep(1)

        cls.service_proxy = ZookeeperServiceProxy(cls.zookeeper_client, cls.service_name, cls.service_class, keepalive=True)
        cls.request_context = RequestContext(userId=0, impersonatingUserId=0, sessionId="dummy_session_id", context="")


    @classmethod
    def tearDownClass(cls):
        cls.zookeeper_client.stop()
        cls.zookeeper_client.join()
        cls.service.stop()
        cls.service.join()
        cls.service2.stop()
        cls.service2.join()